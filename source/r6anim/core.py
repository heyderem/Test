"""
R6 animation core: rig definition, authoring DSL, Roblox-faithful baking and
KeyframeSequence (.rbxmx) export.

Coordinate system is Roblox's: +X right, +Y up, -Z forward (LookVector).

Authoring is done in "body space" with friendly per-joint parameters (degrees):

  torso (RootJoint, relative to HumanoidRootPart)
      pitch  + = lean forward          turn + = twist to the character's right
      roll   + = lean to the right     x/y/z  = offset in studs (z + = forward)
      piv    = pivot height of the rotation relative to torso centre
               (-1 = hip line, the default, 0 = torso centre)
  head (Neck)
      pitch  + = look down   turn + = look right   roll + = tilt right
  ra / la (Right / Left Shoulder)   rl / ll (Right / Left Hip)
      fwd    + = swing the limb forward (arm raise forward, leg kick forward)
      out    + = swing the limb away from the body (sideways)
      yaw    + = swing a raised limb outward around the vertical axis
      twist  + = rotate the limb outward around its own long axis
      x/y/z  = small positional offsets in studs (z + = forward)

Left-side parameters are mirrored so the same numbers mean the same thing on
both sides.  Legs are authored relative to the HumanoidRootPart by default
("world legs") so leaning the torso does not drag the legs along; animations
that tumble (rolls) switch this off.

The authored curves are sampled at 30 fps, converted to the exact
Motor6D.Transform values Roblox uses (taking the R6 C0/C1 frames into
account), then reduced to the smallest set of linear keyframes that still
reproduces every sample within a tight tolerance.  Because the exported data is
linear keyframes, the preview renderer (which reads the exported keyframes)
shows exactly what Roblox will play.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Basic CFrame math (4x4 homogeneous matrices)
# ---------------------------------------------------------------------------

def rx(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def ry(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)


def rz(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


def cf(pos=(0, 0, 0), rot: Optional[np.ndarray] = None) -> np.ndarray:
    m = np.eye(4)
    if rot is not None:
        m[:3, :3] = rot
    m[:3, 3] = pos
    return m


def cf_rows(x, y, z, r00, r01, r02, r10, r11, r12, r20, r21, r22) -> np.ndarray:
    """CFrame.new(x, y, z, R00..R22) exactly like Roblox (row-major)."""
    m = np.eye(4)
    m[:3, :3] = np.array([[r00, r01, r02], [r10, r11, r12], [r20, r21, r22]], dtype=float)
    m[:3, 3] = (x, y, z)
    return m


def inv(m: np.ndarray) -> np.ndarray:
    r = m[:3, :3]
    p = m[:3, 3]
    out = np.eye(4)
    out[:3, :3] = r.T
    out[:3, 3] = -r.T @ p
    return out


def quat_from_matrix(r: np.ndarray) -> np.ndarray:
    """Returns (w, x, y, z)."""
    t = np.trace(r)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        w = 0.25 * s
        x = (r[2, 1] - r[1, 2]) / s
        y = (r[0, 2] - r[2, 0]) / s
        z = (r[1, 0] - r[0, 1]) / s
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = math.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2]) * 2
        w = (r[2, 1] - r[1, 2]) / s
        x = 0.25 * s
        y = (r[0, 1] + r[1, 0]) / s
        z = (r[0, 2] + r[2, 0]) / s
    elif r[1, 1] > r[2, 2]:
        s = math.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2]) * 2
        w = (r[0, 2] - r[2, 0]) / s
        x = (r[0, 1] + r[1, 0]) / s
        y = 0.25 * s
        z = (r[1, 2] + r[2, 1]) / s
    else:
        s = math.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1]) * 2
        w = (r[1, 0] - r[0, 1]) / s
        x = (r[0, 2] + r[2, 0]) / s
        y = (r[1, 2] + r[2, 1]) / s
        z = 0.25 * s
    q = np.array([w, x, y, z])
    return q / np.linalg.norm(q)


def matrix_from_quat(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def slerp(q0: np.ndarray, q1: np.ndarray, a: float) -> np.ndarray:
    d = float(np.dot(q0, q1))
    if d < 0:
        q1 = -q1
        d = -d
    if d > 0.9995:
        q = q0 + a * (q1 - q0)
        return q / np.linalg.norm(q)
    th = math.acos(max(-1.0, min(1.0, d)))
    s = math.sin(th)
    return (math.sin((1 - a) * th) * q0 + math.sin(a * th) * q1) / s


def cf_lerp(m0: np.ndarray, m1: np.ndarray, a: float) -> np.ndarray:
    """CFrame:Lerp - linear position, spherical rotation (what Roblox does)."""
    q = slerp(quat_from_matrix(m0[:3, :3]), quat_from_matrix(m1[:3, :3]), a)
    return cf(m0[:3, 3] + (m1[:3, 3] - m0[:3, 3]) * a, matrix_from_quat(q))


def rot_angle_between(r0: np.ndarray, r1: np.ndarray) -> float:
    c = (np.trace(r0.T @ r1) - 1) / 2
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


# ---------------------------------------------------------------------------
# R6 rig
# ---------------------------------------------------------------------------

PART_SIZE = {
    "HumanoidRootPart": (2, 2, 1),
    "Torso": (2, 2, 1),
    "Head": (2, 1, 1),
    "Right Arm": (1, 2, 1),
    "Left Arm": (1, 2, 1),
    "Right Leg": (1, 2, 1),
    "Left Leg": (1, 2, 1),
}

_A_ROOT = (-1, 0, 0, 0, 0, 1, 0, 1, 0)
_A_R = (0, 0, 1, 0, 1, 0, -1, 0, 0)
_A_L = (0, 0, -1, 0, 1, 0, 1, 0, 0)


@dataclass(frozen=True)
class Motor:
    name: str
    part0: str
    part1: str
    c0: np.ndarray
    c1: np.ndarray


MOTORS: Dict[str, Motor] = {
    "torso": Motor("RootJoint", "HumanoidRootPart", "Torso", cf_rows(0, 0, 0, *_A_ROOT), cf_rows(0, 0, 0, *_A_ROOT)),
    "head": Motor("Neck", "Torso", "Head", cf_rows(0, 1, 0, *_A_ROOT), cf_rows(0, -0.5, 0, *_A_ROOT)),
    "ra": Motor("Right Shoulder", "Torso", "Right Arm", cf_rows(1, 0.5, 0, *_A_R), cf_rows(-0.5, 0.5, 0, *_A_R)),
    "la": Motor("Left Shoulder", "Torso", "Left Arm", cf_rows(-1, 0.5, 0, *_A_L), cf_rows(0.5, 0.5, 0, *_A_L)),
    "rl": Motor("Right Hip", "Torso", "Right Leg", cf_rows(1, -1, 0, *_A_R), cf_rows(0.5, 1, 0, *_A_R)),
    "ll": Motor("Left Hip", "Torso", "Left Leg", cf_rows(-1, -1, 0, *_A_L), cf_rows(-0.5, 1, 0, *_A_L)),
}

JOINTS = ["torso", "head", "ra", "la", "rl", "ll"]
UPPER = ["head", "ra", "la"]
SIDE = {"ra": 1, "rl": 1, "la": -1, "ll": -1}
PARAMS = {
    "torso": ("pitch", "turn", "roll", "x", "y", "z", "piv"),
    "head": ("pitch", "turn", "roll", "x", "y", "z"),
    "limb": ("fwd", "out", "yaw", "twist", "x", "y", "z"),
}
DEFAULTS = {"piv": -1.0}


def params_for(joint: str) -> Tuple[str, ...]:
    if joint in ("torso", "head"):
        return PARAMS[joint]
    return PARAMS["limb"]


def body_rotation(joint: str, p: Dict[str, float]) -> np.ndarray:
    """Body-space rotation (in the parent part's axes) for a joint."""
    g = lambda k: p.get(k, DEFAULTS.get(k, 0.0))
    if joint in ("torso", "head"):
        return ry(-g("turn")) @ rx(-g("pitch")) @ rz(-g("roll"))
    s = SIDE[joint]
    return ry(-s * g("yaw")) @ rx(g("fwd")) @ rz(s * g("out")) @ ry(-s * g("twist"))


def body_offset(joint: str, p: Dict[str, float]) -> np.ndarray:
    g = lambda k: p.get(k, DEFAULTS.get(k, 0.0))
    return np.array([g("x"), g("y"), -g("z")], dtype=float)


def transform_from_body(joint: str, rb: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Motor6D.Transform that produces body-space rotation rb and offset v
    around the joint's pivot (C0 position)."""
    a = MOTORS[joint].c0[:3, :3]
    t = np.eye(4)
    t[:3, :3] = a.T @ rb @ a
    t[:3, 3] = a.T @ v
    return t


def pose_parts(transforms: Dict[str, np.ndarray], hrp: Optional[np.ndarray] = None) -> Dict[str, np.ndarray]:
    """World CFrames of every part given Motor6D.Transform values (missing
    joints use identity), exactly like Roblox: Part1 = Part0*C0*T*C1^-1."""
    hrp = np.eye(4) if hrp is None else hrp
    out = {"HumanoidRootPart": hrp}
    order = ["torso", "head", "ra", "la", "rl", "ll"]
    for j in order:
        m = MOTORS[j]
        t = transforms.get(j, np.eye(4))
        out[m.part1] = out[m.part0] @ m.c0 @ t @ inv(m.c1)
    return out


# ---------------------------------------------------------------------------
# Easing
# ---------------------------------------------------------------------------

def _ease(name: str, a: float) -> float:
    a = min(1.0, max(0.0, a))
    if name == "lin":
        return a
    if name == "const":
        return 0.0
    if name == "io":  # sine in-out
        return 0.5 - 0.5 * math.cos(math.pi * a)
    if name == "in":
        return a * a
    if name == "out":
        return 1 - (1 - a) * (1 - a)
    if name == "in3":
        return a * a * a
    if name == "out3":
        return 1 - (1 - a) ** 3
    if name == "io3":
        return 4 * a ** 3 if a < 0.5 else 1 - (-2 * a + 2) ** 3 / 2
    if name == "out5":
        return 1 - (1 - a) ** 5
    if name == "in5":
        return a ** 5
    if name == "back":  # ease-out with overshoot
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * (a - 1) ** 3 + c1 * (a - 1) ** 2
    if name == "backin":
        c1 = 1.70158
        c3 = c1 + 1
        return c3 * a ** 3 - c1 * a ** 2
    if name == "elastic":
        if a in (0.0, 1.0):
            return a
        return 2 ** (-10 * a) * math.sin((a * 10 - 0.75) * (2 * math.pi) / 3) + 1
    raise ValueError(name)


EASES = {"lin", "const", "io", "in", "out", "in3", "out3", "io3", "out5", "in5", "back", "backin", "elastic", "smooth"}


# ---------------------------------------------------------------------------
# Authoring DSL
# ---------------------------------------------------------------------------

def T(**p):
    return ("torso", p)


def H(**p):
    return ("head", p)


def RA(**p):
    return ("ra", p)


def LA(**p):
    return ("la", p)


def RL(**p):
    return ("rl", p)


def LL(**p):
    return ("ll", p)


def mirror(spec: Sequence[Tuple[str, dict]]) -> List[Tuple[str, dict]]:
    """Left/right mirror of a list of joint specs (for alternating cycles)."""
    swap = {"ra": "la", "la": "ra", "rl": "ll", "ll": "rl", "torso": "torso", "head": "head"}
    out = []
    for j, p in spec:
        q = dict(p)
        if j in ("torso", "head"):
            for k in ("turn", "roll", "x"):
                if k in q:
                    q[k] = -q[k]
        else:
            if "x" in q:
                q["x"] = -q["x"]
        out.append((swap[j], q))
    return out


@dataclass
class Key:
    t: float
    p: Dict[str, float]
    ease: str


@dataclass
class PropSpec:
    """Preview-only object shown in the GIF (not part of the animation)."""
    kind: str                     # small | medium | large | huge
    mode: str = "r"               # r | l | both
    offset: Tuple[float, float, float] = (0, 0, 0)   # in grip frame (x right, y up, z back)
    rot: Tuple[float, float, float] = (0, 0, 0)      # extra rotation (deg) x, y, z
    appear: float = 0.0           # time the object is in hand (before: on the ground)
    ground_pos: Optional[Tuple[float, float, float]] = None  # rest position before pickup (None = under the hand)
    release: Optional[float] = None    # time it leaves the hand
    throw_vel: Tuple[float, float, float] = (0, 6, -40)    # velocity after release (character space)
    spin: Tuple[float, float, float] = (0, 0, 0)            # deg/s after release
    gravity: float = 50.0
    align: str = "arm"            # arm | torso  (orientation of the grip frame for 'both')
    keys: Optional[list] = None   # [(t, offset, rot)] to change the grip over time (linear)
    lift: Optional[Tuple[float, float]] = None   # blend from the rest pose into the hands over (t0, t1)
    rest_rot: Tuple[float, float, float] = (0, 0, 0)   # rotation while resting on the floor


@dataclass
class Anim:
    name: str
    length: float
    loop: bool = False
    priority: str = "Action"
    default_ease: str = "io"
    world_legs: bool = True
    upper_only: bool = False          # export only Neck + shoulders (layers on top of locomotion)
    export_joints: Optional[Tuple[str, ...]] = None   # explicit joint list to export
    fold: Tuple[str, ...] = ("turn",)  # torso motion folded into arms/head for upper-body variants
    category: str = "Misc"
    description: str = ""
    # preview settings
    preview_base: Optional[str] = None     # animation played underneath (for upper-body variants)
    preview_speed: float = 0.0             # studs/s the ground scrolls in previews
    preview_views: Tuple[str, str] = ("front", "side")
    preview_hold: float = 0.35             # extra seconds the last frame is held in a non-looping GIF
    preview_zoom: float = 1.0
    preview_ground: float = -3.0           # floor height in the preview (HRP space)
    preview_root: Optional[Callable[[float], Tuple[float, float, float]]] = None  # preview-only root motion
    preview_scenery: list = field(default_factory=list)  # preview-only walls / ledges
    preview_panels: Optional[list] = None  # [(view, base_name or None, scroll, label)]
    props: List[PropSpec] = field(default_factory=list)
    fx: List[Tuple[float, str, str]] = field(default_factory=list)  # (time, kind, where)
    keys: Dict[str, List[Key]] = field(default_factory=dict)
    markers: List[Tuple[float, str]] = field(default_factory=list)
    fn: Optional[Callable[[float], List[Tuple[str, dict]]]] = None
    fps: int = 30
    overlap: Optional["Overlap"] = None     # secondary motion (None = default settings)
    grounded: bool = True                  # keep feet out of the floor
    floor: float = -3.0
    foot_mode: str = "fwd"                 # how sinking legs are fixed: angle 'fwd' or splay 'out'
    _proc: Optional[tuple] = None

    # -- authoring ----------------------------------------------------------
    def k(self, t: float, *specs, e: Optional[str] = None):
        self._proc = None
        ease = e or self.default_ease
        assert ease in EASES, ease
        for j, p in specs:
            lst = self.keys.setdefault(j, [])
            lst[:] = [kk for kk in lst if abs(kk.t - t) > 1e-6]
            lst.append(Key(t, dict(p), ease))
            lst.sort(key=lambda kk: kk.t)
        return self

    def pose(self, t: float, pose: Sequence[Tuple[str, dict]], e: Optional[str] = None):
        return self.k(t, *pose, e=e)

    def mark(self, t: float, name: str):
        self.markers.append((t, name))
        return self

    def close_loop(self):
        """Copy the first key of every joint to t=length so the loop is seamless."""
        for j, lst in self.keys.items():
            first = lst[0]
            self.k(self.length, (j, first.p), e=first.ease)
        return self

    # -- evaluation ---------------------------------------------------------
    def exported(self) -> List[str]:
        if self.fn is not None:
            js = [j for j, _ in self.fn(0.0)]
        else:
            js = list(self.keys.keys())
        if self.export_joints is not None:
            js = [j for j in js if j in self.export_joints]
        elif self.upper_only:
            js = [j for j in js if j in UPPER]
        return [j for j in JOINTS if j in js]

    def _eval_track(self, keys: List[Key], t: float, name: str) -> float:
        get = lambda kk: kk.p.get(name, DEFAULTS.get(name, 0.0))
        n = len(keys)
        if n == 1 or t <= keys[0].t:
            return get(keys[0])
        if t >= keys[-1].t:
            return get(keys[-1])
        i = 0
        while i < n - 1 and not (keys[i].t <= t <= keys[i + 1].t):
            i += 1
        k0, k1 = keys[i], keys[i + 1]
        span = k1.t - k0.t
        a = (t - k0.t) / span if span > 1e-9 else 1.0
        v0, v1 = get(k0), get(k1)
        if k0.ease != "smooth":
            return v0 + (v1 - v0) * _ease(k0.ease, a)
        # Catmull-Rom (non-uniform) tangents; wraps for looping anims
        def neighbour(idx):
            if 0 <= idx < n:
                return keys[idx].t, get(keys[idx])
            if self.loop:
                if idx < 0:
                    kk = keys[n - 1 + idx]  # keys[-1] duplicates keys[0]
                    return kk.t - self.length, get(kk)
                kk = keys[idx - n + 1]
                return kk.t + self.length, get(kk)
            return None

        def tangent(idx, tv, vv):
            prev = neighbour(idx - 1)
            nxt = neighbour(idx + 1)
            if prev is None and nxt is None:
                return 0.0
            if prev is None or nxt is None:
                return 0.0
            return (nxt[1] - prev[1]) / (nxt[0] - prev[0])

        m0 = tangent(i, k0.t, v0) * span
        m1 = tangent(i + 1, k1.t, v1) * span
        a2, a3 = a * a, a * a * a
        h00 = 2 * a3 - 3 * a2 + 1
        h10 = a3 - 2 * a2 + a
        h01 = -2 * a3 + 3 * a2
        h11 = a3 - a2
        return h00 * v0 + h10 * m0 + h01 * v1 + h11 * m1

    def raw_params_at(self, t: float) -> Dict[str, Dict[str, float]]:
        if self.fn is not None:
            out = {j: dict(p) for j, p in self.fn(t)}
            for j, p in out.items():
                for name in params_for(j):
                    p.setdefault(name, DEFAULTS.get(name, 0.0))
            return out
        out = {}
        for j, keys in self.keys.items():
            out[j] = {name: self._eval_track(keys, t, name) for name in params_for(j)}
        return out

    def process(self):
        from .secondary import Overlap, apply_overlap, fix_feet
        dt = 1.0 / 120
        n = max(2, int(round(self.length / dt)))
        ts = np.linspace(0.0, self.length, n + 1)
        raw = [self.raw_params_at(float(t)) for t in ts]
        tracks = {j: {k: np.array([r[j][k] for r in raw], float) for k in raw[0][j]} for j in raw[0]}
        ov = self.overlap if self.overlap is not None else Overlap()
        apply_overlap(tracks, dt, ov, self.loop)
        self.foot_fix_amount = 0.0
        if self.grounded:
            self.foot_fix_amount = fix_feet(tracks, self.floor, self.world_legs, self.foot_mode)
        if self.loop:
            for j in tracks:
                for k, x in tracks[j].items():
                    m = (x[0] + x[-1]) / 2
                    x[0] = x[-1] = m
        self._proc = (ts, tracks)

    def params_at(self, t: float) -> Dict[str, Dict[str, float]]:
        if self._proc is None:
            self.process()
        ts, tracks = self._proc
        if self.loop and self.length > 0:
            t = t % self.length if t != self.length else t
        t = min(max(t, 0.0), self.length)
        f = t / (ts[1] - ts[0])
        i = min(int(f), len(ts) - 2)
        a = f - i
        return {j: {k: float(x[i] + (x[i + 1] - x[i]) * a) for k, x in tr.items()} for j, tr in tracks.items()}

    def transforms_at(self, t: float) -> Dict[str, np.ndarray]:
        pr = self.params_at(t)
        keep = self.exported()
        if self.upper_only or self.export_joints is not None:
            tr = params_to_transforms(pr, self.world_legs, fold=self.fold if "torso" not in keep else ())
        else:
            tr = params_to_transforms(pr, self.world_legs)
        return {j: m for j, m in tr.items() if j in keep}


def params_to_transforms(pr: Dict[str, Dict[str, float]], world_legs: bool = True,
                         fold: Sequence[str] = ()) -> Dict[str, np.ndarray]:
    """fold: when the torso is not exported (upper-body layer), fold parts of
    its motion into the head/arms so they keep pointing where they would
    have pointed with the torso motion ('turn' and/or 'pitch')."""
    out = {}
    rf = np.eye(3)
    if fold and "torso" in pr:
        tp = pr["torso"]
        if "turn" in fold:
            rf = ry(-tp.get("turn", 0.0)) @ rf
        if "pitch" in fold:
            rf = rf @ rx(-tp.get("pitch", 0.0) * 0.8)
        if "roll" in fold:
            rf = rf @ rz(-tp.get("roll", 0.0))
    rt = np.eye(3)
    if "torso" in pr:
        p = pr["torso"]
        rb = body_rotation("torso", p)
        v = body_offset("torso", p)
        piv = np.array([0.0, p.get("piv", DEFAULTS["piv"]), 0.0])
        v = v + piv - rb @ piv
        out["torso"] = transform_from_body("torso", rb, v)
        rt = rb
    for j in ("head", "ra", "la", "rl", "ll"):
        if j not in pr:
            continue
        p = pr[j]
        rb = body_rotation(j, p)
        v = body_offset(j, p)
        if world_legs and j in ("rl", "ll") and "torso" in pr:
            # legs ignore the torso's forward/back lean (so leaning doesn't swing the legs back) but
            # follow its twist and sideways tilt, like the hips would - otherwise a tilted chest
            # looks snapped off at the hips
            tp = pr["torso"]
            follow = ry(-tp.get("turn", 0.0)) @ rz(-tp.get("roll", 0.0))
            rb = rt.T @ follow @ rb
        if fold and j in ("head", "ra", "la"):
            p0 = MOTORS[j].c0[:3, 3]
            rb = rf @ rb
            # move the pivot part of the way so shoulders follow the twist
            v = 0.45 * (rf @ (p0 + v) - p0) + 0.55 * (rf @ v)
        out[j] = transform_from_body(j, rb, v)
    return out


# ---------------------------------------------------------------------------
# Baking & keyframe reduction
# ---------------------------------------------------------------------------

@dataclass
class Baked:
    anim: Anim
    times: List[float]                       # keyframe times
    frames: List[Dict[str, np.ndarray]]      # Motor6D.Transform per joint per keyframe
    names: List[str]                         # keyframe names
    markers: List[Tuple[float, str]]


def sample(anim: Anim) -> Tuple[List[float], List[Dict[str, np.ndarray]]]:
    n = max(1, int(round(anim.length * anim.fps)))
    ts = [i / anim.fps for i in range(n + 1)]
    ts[-1] = anim.length
    for t, _ in anim.markers:
        if all(abs(t - x) > 1e-4 for x in ts):
            ts.append(t)
    ts.sort()
    return ts, [anim.transforms_at(t) for t in ts]


def _close(a: np.ndarray, b: np.ndarray, rot_tol: float, pos_tol: float) -> bool:
    if np.linalg.norm(a[:3, 3] - b[:3, 3]) > pos_tol:
        return False
    return rot_angle_between(a[:3, :3], b[:3, :3]) <= rot_tol


def reduce_keys(ts, frames, keep: set, rot_tol=0.6, pos_tol=0.012):
    """Greedy reduction: drop a sample when linear (slerp) interpolation of
    the surrounding kept keys reproduces every dropped sample in between."""
    joints = list(frames[0].keys())
    kept = [0]
    i = 0
    n = len(ts)
    while i < n - 1:
        best = i + 1
        j = i + 2
        while j < n:
            ok = True
            for m in range(i + 1, j):
                a = (ts[m] - ts[i]) / (ts[j] - ts[i])
                for jt in joints:
                    approx = cf_lerp(frames[i][jt], frames[j][jt], a)
                    if not _close(approx, frames[m][jt], rot_tol, pos_tol):
                        ok = False
                        break
                if not ok:
                    break
            # never skip over a required key
            if ok and any(k in keep for k in range(i + 1, j)):
                ok = False
            if not ok:
                break
            best = j
            j += 1
        kept.append(best)
        i = best
    return kept


def bake(anim: Anim, reduce: bool = True) -> Baked:
    ts, frames = sample(anim)
    assert frames[0], f"{anim.name}: no joints exported"
    keep = {i for i, t in enumerate(ts) if any(abs(t - mt) < 1e-4 for mt, _ in anim.markers)}
    keep.add(0)
    keep.add(len(ts) - 1)
    idx = reduce_keys(ts, frames, keep) if reduce else list(range(len(ts)))
    names = []
    for i in idx:
        nm = [m for mt, m in anim.markers if abs(mt - ts[i]) < 1e-4]
        names.append(nm[0] if nm else "Keyframe")
    return Baked(anim, [ts[i] for i in idx], [frames[i] for i in idx], names, sorted(anim.markers))


def baked_transforms_at(b: Baked, t: float) -> Dict[str, np.ndarray]:
    """Evaluate exported keyframes exactly like Roblox does with Linear easing."""
    ts = b.times
    if b.anim.loop and b.anim.length > 0:
        t = t % b.anim.length
    if len(ts) == 1 or t <= ts[0]:
        return dict(b.frames[0])
    if t >= ts[-1]:
        return dict(b.frames[-1])
    i = 0
    while not (ts[i] <= t <= ts[i + 1]):
        i += 1
    a = (t - ts[i]) / (ts[i + 1] - ts[i])
    return {j: cf_lerp(b.frames[i][j], b.frames[i + 1][j], a) for j in b.frames[i]}


# ---------------------------------------------------------------------------
# .rbxmx export
# ---------------------------------------------------------------------------

PRIORITY = {"Idle": 0, "Movement": 1, "Action": 2, "Action2": 3, "Action3": 4, "Action4": 5, "Core": 1000}


class _Ref:
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return f"RBX{self.n:08X}"


def _fmt(v: float) -> str:
    if abs(v) < 1e-9:
        v = 0.0
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _cframe_xml(name: str, m: np.ndarray) -> str:
    p = m[:3, 3]
    r = m[:3, :3]
    parts = [f'<CoordinateFrame name="{name}">']
    parts += [f"<X>{_fmt(p[0])}</X>", f"<Y>{_fmt(p[1])}</Y>", f"<Z>{_fmt(p[2])}</Z>"]
    for i in range(3):
        for k in range(3):
            parts.append(f"<R{i}{k}>{_fmt(r[i, k])}</R{i}{k}>")
    parts.append("</CoordinateFrame>")
    return "".join(parts)


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _pose_xml(ref, name: str, m: np.ndarray, weight: float, children: str, ind: str) -> str:
    return (
        f'{ind}<Item class="Pose" referent="{ref()}">\n'
        f"{ind}\t<Properties>\n"
        f"{ind}\t\t{_cframe_xml('CFrame', m)}\n"
        f'{ind}\t\t<token name="EasingDirection">0</token>\n'
        f'{ind}\t\t<token name="EasingStyle">0</token>\n'
        f'{ind}\t\t<string name="Name">{_esc(name)}</string>\n'
        f'{ind}\t\t<float name="Weight">{_fmt(weight)}</float>\n'
        f"{ind}\t</Properties>\n"
        f"{children}"
        f"{ind}</Item>\n"
    )


def keyframe_sequence_xml(b: Baked, ref: _Ref, ind: str = "\t") -> str:
    a = b.anim
    joints = list(b.frames[0].keys())
    out = [
        f'{ind}<Item class="KeyframeSequence" referent="{ref()}">\n',
        f"{ind}\t<Properties>\n",
        f'{ind}\t\t<bool name="Loop">{"true" if a.loop else "false"}</bool>\n',
        f'{ind}\t\t<string name="Name">{_esc(a.name)}</string>\n',
        f'{ind}\t\t<token name="Priority">{PRIORITY[a.priority]}</token>\n',
        f"{ind}\t</Properties>\n",
    ]
    marker_at = {}
    for mt, mn in b.markers:
        marker_at.setdefault(round(mt, 4), []).append(mn)
    for t, fr, kname in zip(b.times, b.frames, b.names):
        ki = ind + "\t"
        out.append(f'{ki}<Item class="Keyframe" referent="{ref()}">\n')
        out.append(f"{ki}\t<Properties>\n")
        out.append(f'{ki}\t\t<string name="Name">{_esc(kname)}</string>\n')
        out.append(f'{ki}\t\t<float name="Time">{_fmt(t)}</float>\n')
        out.append(f"{ki}\t</Properties>\n")
        for mn in marker_at.get(round(t, 4), []):
            out.append(f'{ki}\t<Item class="KeyframeMarker" referent="{ref()}">\n')
            out.append(f"{ki}\t\t<Properties>\n")
            out.append(f'{ki}\t\t\t<string name="Name">{_esc(mn)}</string>\n')
            out.append(f'{ki}\t\t\t<string name="Value"></string>\n')
            out.append(f"{ki}\t\t</Properties>\n")
            out.append(f"{ki}\t</Item>\n")
        pi = ki + "\t"
        # children of Torso
        child_xml = ""
        for j in ("head", "ra", "la", "rl", "ll"):
            if j in joints:
                child_xml += _pose_xml(ref, MOTORS[j].part1, fr[j], 1.0, "", pi + "\t\t")
        torso_m = fr.get("torso", np.eye(4))
        torso_w = 1.0 if "torso" in joints else 0.0
        torso_xml = _pose_xml(ref, "Torso", torso_m, torso_w, child_xml, pi + "\t")
        out.append(_pose_xml(ref, "HumanoidRootPart", np.eye(4), 0.0, torso_xml, pi))
        out.append(f"{ki}</Item>\n")
    out.append(f"{ind}</Item>\n")
    return "".join(out)


HEADER = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
          'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
          'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
          "\t<External>null</External>\n\t<External>nil</External>\n")


def write_single(b: Baked, path: str):
    ref = _Ref()
    with open(path, "w", encoding="utf-8") as f:
        f.write(HEADER)
        f.write(keyframe_sequence_xml(b, ref))
        f.write("</roblox>\n")


def write_folder(bakeds: List[Baked], path: str, folder_name: str = "AnimSaves", folder_class: str = "Model",
                 groups: Optional[Dict[str, List[Baked]]] = None):
    """One file holding every KeyframeSequence.  The root is a Model named
    AnimSaves so it can be dropped straight under a rig for the Animation
    Editor; optional sub-folders group the sequences by category."""
    ref = _Ref()
    with open(path, "w", encoding="utf-8") as f:
        f.write(HEADER)
        f.write(f'\t<Item class="{folder_class}" referent="{ref()}">\n\t\t<Properties>\n'
                f'\t\t\t<string name="Name">{_esc(folder_name)}</string>\n\t\t</Properties>\n')
        if groups:
            for gname, items in groups.items():
                f.write(f'\t\t<Item class="Folder" referent="{ref()}">\n\t\t\t<Properties>\n'
                        f'\t\t\t\t<string name="Name">{_esc(gname)}</string>\n\t\t\t</Properties>\n')
                for b in items:
                    f.write(keyframe_sequence_xml(b, ref, "\t\t\t"))
                f.write("\t\t</Item>\n")
        else:
            for b in bakeds:
                f.write(keyframe_sequence_xml(b, ref, "\t\t"))
        f.write("\t</Item>\n</roblox>\n")
