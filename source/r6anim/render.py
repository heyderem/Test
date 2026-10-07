"""
Tiny software renderer for R6 previews (numpy z-buffer + PIL).

The renderer only ever reads the *exported* keyframes (via
core.baked_transforms_at), so what you see in a GIF is what Roblox plays.
Objects, impact sparks and dust are preview-only decoration.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .core import (Baked, PART_SIZE, PropSpec, baked_transforms_at, cf, inv,
                   pose_parts, rx, ry, rz)

GROUND_Y = -3.0  # HumanoidRootPart centre sits 3 studs above the floor in R6

# Classic R6 colours
COL = {
    "Head": (245, 205, 48),
    "Torso": (13, 105, 172),
    "Right Arm": (245, 205, 48),
    "Left Arm": (245, 205, 48),
    "Right Leg": (164, 189, 71),
    "Left Leg": (164, 189, 71),
}

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


@lru_cache(maxsize=8)
def font(size, bold=True):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT_R, size)
    except OSError:
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

_CORNERS = np.array([[sx, sy, sz] for sx in (-0.5, 0.5) for sy in (-0.5, 0.5) for sz in (-0.5, 0.5)])
# faces: (corner indices (ccw from outside), normal)
_FACES = [
    ((0, 1, 3, 2), (-1, 0, 0)),
    ((4, 6, 7, 5), (1, 0, 0)),
    ((0, 4, 5, 1), (0, -1, 0)),
    ((2, 3, 7, 6), (0, 1, 0)),
    ((0, 2, 6, 4), (0, 0, -1)),
    ((1, 5, 7, 3), (0, 0, 1)),
]

LIGHT = np.array([-0.45, 0.85, -0.35])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


class Mesh:
    def __init__(self):
        self.tris: List[np.ndarray] = []   # (3,3) world points
        self.cols: List[Tuple[float, float, float]] = []

    def box(self, m: np.ndarray, size, color, shade=True):
        size = np.asarray(size, dtype=float)
        pts = (_CORNERS * size) @ m[:3, :3].T + m[:3, 3]
        for idx, n in _FACES:
            nw = m[:3, :3] @ np.array(n, dtype=float)
            if shade:
                d = max(0.0, float(nw @ LIGHT))
                k = 0.52 + 0.55 * d + 0.08 * max(0.0, nw[1])
            else:
                k = 1.0
            c = tuple(min(255.0, ch * k) for ch in color)
            a, b, cc, dd = (pts[i] for i in idx)
            self.tris.append(np.array([a, b, cc]))
            self.cols.append(c)
            self.tris.append(np.array([a, cc, dd]))
            self.cols.append(c)

    def quad(self, pts, color):
        a, b, c, d = pts
        self.tris.append(np.array([a, b, c]))
        self.cols.append(color)
        self.tris.append(np.array([a, c, d]))
        self.cols.append(color)


def add_face(mesh: Mesh, head: np.ndarray):
    """Classic smile on the -Z face of the head."""
    dark = (25, 25, 25)
    z = -0.5 - 0.012

    def P(x, y):
        return (head @ np.array([x, y, z, 1.0]))[:3]

    for ex in (-0.28, 0.28):
        mesh.quad([P(ex - 0.07, 0.02), P(ex + 0.07, 0.02), P(ex + 0.07, 0.3), P(ex - 0.07, 0.3)], dark)
    # smile arc
    n = 9
    r_out, r_in = 0.42, 0.34
    cy = 0.12
    for i in range(n):
        a0 = math.radians(-155 + i * (130 / n))
        a1 = math.radians(-155 + (i + 1) * (130 / n))
        pts = [P(r_out * math.cos(a0), cy + r_out * math.sin(a0) * 0.75),
               P(r_out * math.cos(a1), cy + r_out * math.sin(a1) * 0.75),
               P(r_in * math.cos(a1), cy + r_in * math.sin(a1) * 0.75),
               P(r_in * math.cos(a0), cy + r_in * math.sin(a0) * 0.75)]
        mesh.quad(pts, dark)


# --- preview objects --------------------------------------------------------

def prop_boxes(kind: str) -> List[Tuple[np.ndarray, Tuple[float, float, float], Tuple[int, int, int]]]:
    """Box list (local CFrame, size, colour) for a preview object."""
    if kind == "small":      # rock
        return [(cf((0, 0, 0), ry(20) @ rx(15)), (0.85, 0.75, 0.8), (120, 118, 112)),
                (cf((0.12, 0.18, 0.05), ry(-10)), (0.5, 0.45, 0.55), (138, 135, 128))]
    if kind == "medium":     # wooden crate
        return [(cf(), (2.0, 2.0, 2.0), (160, 108, 55)),
                (cf((0, 0, -1.0)), (1.6, 0.3, 0.06), (120, 78, 36)),
                (cf((0, 0, 1.0)), (1.6, 0.3, 0.06), (120, 78, 36)),
                (cf((1.0, 0, 0)), (0.06, 0.3, 1.6), (120, 78, 36)),
                (cf((-1.0, 0, 0)), (0.06, 0.3, 1.6), (120, 78, 36))]
    if kind == "large":      # car
        body = (200, 40, 45)
        glass = (150, 200, 225)
        tire = (30, 30, 32)
        out = [(cf((0, -0.1, 0)), (5.6, 1.3, 2.7), body),
               (cf((-0.3, 0.95, 0)), (3.0, 0.9, 2.5), body),
               (cf((-0.3, 0.95, -1.27)), (2.6, 0.62, 0.04), glass),
               (cf((-0.3, 0.95, 1.27)), (2.6, 0.62, 0.04), glass),
               (cf((1.22, 0.95, 0)), (0.04, 0.62, 2.2), glass),
               (cf((-1.82, 0.95, 0)), (0.04, 0.62, 2.2), glass)]
        for wx in (-1.8, 1.8):
            for wz in (-1.25, 1.25):
                out.append((cf((wx, -0.75, wz)), (1.1, 1.1, 0.4), tire))
        return out
    if kind == "huge":       # train carriage (~14 studs, ~2.8x a character)
        body = (225, 225, 230)
        stripe = (215, 60, 55)
        win = (60, 85, 110)
        out = [(cf((0, 0, 0)), (14.0, 3.6, 3.6), body),
               (cf((0, -0.7, -1.81)), (13.6, 0.5, 0.04), stripe),
               (cf((0, -0.7, 1.81)), (13.6, 0.5, 0.04), stripe),
               (cf((0, 1.85, 0)), (13.4, 0.2, 3.0), (170, 170, 178))]
        for i in range(6):
            x = -5.6 + i * 2.24
            out.append((cf((x, 0.55, -1.81)), (1.4, 1.1, 0.04), win))
            out.append((cf((x, 0.55, 1.81)), (1.4, 1.1, 0.04), win))
        for wx in (-5.0, -3.8, 3.8, 5.0):
            out.append((cf((wx, -2.0, 0)), (0.9, 0.9, 3.0), (40, 40, 44)))
        return out
    raise ValueError(kind)


PROP_EXTENT = {"small": 0.5, "medium": 1.0, "large": 1.5, "huge": 2.4}  # half height to sit on ground


# ---------------------------------------------------------------------------
# Camera & rasteriser
# ---------------------------------------------------------------------------

class Camera:
    def __init__(self, eye, target, w, h, fov=34.0):
        self.eye = np.asarray(eye, float)
        self.target = np.asarray(target, float)
        f = self.target - self.eye
        f /= np.linalg.norm(f)
        r = np.cross(f, [0, 1, 0])
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        self.r, self.u, self.f = r, u, f
        self.w, self.h = w, h
        self.focal = (h / 2) / math.tan(math.radians(fov) / 2)

    def project(self, pts: np.ndarray):
        d = pts - self.eye
        x = d @ self.r
        y = d @ self.u
        z = d @ self.f
        z = np.maximum(z, 1e-3)
        sx = self.w / 2 + self.focal * x / z
        sy = self.h / 2 - self.focal * y / z
        return sx, sy, z

    def rays(self):
        ys, xs = np.mgrid[0:self.h, 0:self.w].astype(float)
        dx = (xs + 0.5 - self.w / 2) / self.focal
        dy = -(ys + 0.5 - self.h / 2) / self.focal
        d = self.f[None, None, :] + dx[..., None] * self.r[None, None, :] + dy[..., None] * self.u[None, None, :]
        return d  # not normalised: z-forward component is 1


def raster(img: np.ndarray, zbuf: np.ndarray, cam: Camera, mesh: Mesh):
    if not mesh.tris:
        return
    tris = np.stack(mesh.tris)  # (N,3,3)
    cols = np.array(mesh.cols)
    flat = tris.reshape(-1, 3)
    sx, sy, sz = cam.project(flat)
    sx = sx.reshape(-1, 3)
    sy = sy.reshape(-1, 3)
    iz = (1.0 / sz).reshape(-1, 3)
    H, W = zbuf.shape
    for i in range(len(tris)):
        x0, x1, x2 = sx[i]
        y0, y1, y2 = sy[i]
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-9:
            continue
        minx = max(int(math.floor(min(x0, x1, x2))), 0)
        maxx = min(int(math.ceil(max(x0, x1, x2))), W - 1)
        miny = max(int(math.floor(min(y0, y1, y2))), 0)
        maxy = min(int(math.ceil(max(y0, y1, y2))), H - 1)
        if minx > maxx or miny > maxy:
            continue
        px = np.arange(minx, maxx + 1) + 0.5
        py = np.arange(miny, maxy + 1) + 0.5
        PX, PY = np.meshgrid(px, py)
        w0 = ((x1 - PX) * (y2 - PY) - (x2 - PX) * (y1 - PY)) / area
        w1 = ((x2 - PX) * (y0 - PY) - (x0 - PX) * (y2 - PY)) / area
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        z = w0 * iz[i, 0] + w1 * iz[i, 1] + w2 * iz[i, 2]
        sub = zbuf[miny:maxy + 1, minx:maxx + 1]
        m = inside & (z > sub)
        if not m.any():
            continue
        sub[m] = z[m]
        img[miny:maxy + 1, minx:maxx + 1][m] = cols[i]


class Scene:
    """Per-camera cached background (sky + ground rays)."""

    def __init__(self, cam: Camera, ground_y: float = GROUND_Y):
        self.cam = cam
        self.ground_y = ground_y
        d = cam.rays()
        self.dy = d[..., 1]
        below = self.dy < -1e-4
        t = np.where(below, (ground_y - cam.eye[1]) / np.where(below, self.dy, -1), 1e6)
        self.t = t
        self.gx = cam.eye[0] + t * d[..., 0]
        self.gz = cam.eye[2] + t * d[..., 2]
        self.below = below & (t < 400)
        # sky gradient
        h = np.clip((self.dy + 0.15) / 0.9, 0, 1)[..., None]
        top = np.array([118, 172, 230.0])
        hor = np.array([205, 226, 245.0])
        self.sky = hor * (1 - h) + top * h

    def background(self, scroll_z: float, tint=(0, 0, 0)):
        img = self.sky.copy()
        gz = self.gz + scroll_z
        tile = 4.0
        chk = ((np.floor(self.gx / tile) + np.floor(gz / tile)) % 2 == 0)
        base = np.where(chk[..., None], np.array([116, 121, 128.0]), np.array([97, 101, 108.0]))
        # fine grid lines
        fx = np.abs((self.gx / tile) - np.round(self.gx / tile))
        fz = np.abs((gz / tile) - np.round(gz / tile))
        line = (np.minimum(fx, fz) < 0.02)
        base = np.where(line[..., None], base * 0.85, base)
        # distance fog
        fog = np.clip((self.t - 30) / 110, 0, 1)[..., None]
        base = base * (1 - fog) + np.array([190, 206, 222.0]) * fog
        img = np.where(self.below[..., None], base, img)
        zbuf = np.where(self.below, 1.0 / np.maximum(self.t, 1e-3), 0.0)
        return img, zbuf


def shadow_mask(cam: Camera, boxes: List[Tuple[np.ndarray, np.ndarray]], shape, ground_y=GROUND_Y) -> np.ndarray:
    """Project boxes along the light onto the ground; return [0..1] mask."""
    H, W = shape
    mask = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(mask)
    L = LIGHT
    for m, size in boxes:
        pts = (_CORNERS * size) @ m[:3, :3].T + m[:3, 3]
        # move along -light until y == GROUND_Y
        t = (pts[:, 1] - ground_y) / L[1]
        t = np.maximum(t, 0)
        g = pts - t[:, None] * L
        g[:, 1] = ground_y
        sx, sy, _ = cam.project(g)
        hull = _convex_hull(np.stack([sx, sy], 1))
        if len(hull) >= 3:
            dr.polygon([tuple(p) for p in hull], fill=255)
    return np.asarray(mask, dtype=float) / 255.0


def _convex_hull(p: np.ndarray) -> List[np.ndarray]:
    pts = sorted(map(tuple, p))
    if len(pts) <= 2:
        return [np.array(x) for x in pts]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return [np.array(x) for x in lower[:-1] + upper[:-1]]


# ---------------------------------------------------------------------------
# Preview state (character + objects) at a time
# ---------------------------------------------------------------------------

def compose(b: Baked, base: Optional[Baked], t: float, base_t: Optional[float] = None) -> Dict[str, np.ndarray]:
    tr = {}
    if base is not None:
        tr.update(baked_transforms_at(base, t if base_t is None else base_t))
    tr.update(baked_transforms_at(b, t))
    return tr


def grip_frame(parts, side: str) -> np.ndarray:
    arm = parts["Right Arm" if side == "r" else "Left Arm"]
    return arm @ cf((0, -1.0, 0))


def both_grip(parts, align: str) -> np.ndarray:
    gr = grip_frame(parts, "r")
    gl = grip_frame(parts, "l")
    pos = (gr[:3, 3] + gl[:3, 3]) / 2
    torso = parts["Torso"][:3, :3]
    if align == "torso":
        return cf(pos, torso)
    d = -(gr[:3, 1] + gl[:3, 1])          # average pointing direction of both arms
    n = np.linalg.norm(d)
    d = d / n if n > 1e-6 else -torso[:, 1]
    x = torso[:, 0] - (torso[:, 0] @ d) * d
    x /= max(np.linalg.norm(x), 1e-6)
    y = d                                 # +Y of the grip frame points out past the hands
    z = np.cross(x, y)
    return cf(pos, np.stack([x, y, z], 1))


def _prop_local(spec: PropSpec, t: float) -> np.ndarray:
    off, rot = spec.offset, spec.rot
    if spec.keys:
        ks = sorted(spec.keys, key=lambda k: k[0])
        if t <= ks[0][0]:
            off, rot = ks[0][1], ks[0][2]
        elif t >= ks[-1][0]:
            off, rot = ks[-1][1], ks[-1][2]
        else:
            for (t0, o0, r0), (t1, o1, r1) in zip(ks, ks[1:]):
                if t0 <= t <= t1:
                    a = (t - t0) / (t1 - t0)
                    a = a * a * (3 - 2 * a)
                    off = tuple(o0[i] + (o1[i] - o0[i]) * a for i in range(3))
                    rot = tuple(r0[i] + (r1[i] - r0[i]) * a for i in range(3))
                    break
    return cf(off, rx(rot[0]) @ ry(rot[1]) @ rz(rot[2]))


def _rest_pose(spec: PropSpec, rest):
    if spec.ground_pos is not None:
        gx, gy, gz = spec.ground_pos
        r = spec.rest_rot
        return cf((gx, GROUND_Y + PROP_EXTENT[spec.kind] + gy, gz), rx(r[0]) @ ry(r[1]) @ rz(r[2]))
    if rest is not None:
        return rest
    return cf((0, GROUND_Y + PROP_EXTENT[spec.kind], -2))


def prop_world(spec: PropSpec, parts, t: float, release_state, rest=None) -> Optional[np.ndarray]:
    local = _prop_local(spec, t)
    if spec.lift is not None:
        t0, t1 = spec.lift
        if t < t0:
            return _rest_pose(spec, rest)
        if t < t1:
            g = both_grip(parts, spec.align) if spec.mode == "both" else grip_frame(parts, spec.mode)
            held = g @ local
            k = (t - t0) / (t1 - t0)
            k = k * k * (3 - 2 * k)
            from .core import cf_lerp
            return cf_lerp(_rest_pose(spec, rest), held, k)
    elif t < spec.appear:
        return _rest_pose(spec, rest)
    if spec.release is not None and t >= spec.release and release_state is not None:
        m0, v = release_state
        dt = t - spec.release
        pos = m0[:3, 3] + np.array(v) * dt + np.array([0, -0.5 * spec.gravity * dt * dt, 0])
        rot = m0[:3, :3] @ rx(spec.spin[0] * dt) @ ry(spec.spin[1] * dt) @ rz(spec.spin[2] * dt)
        floor = GROUND_Y + PROP_EXTENT[spec.kind]
        if pos[1] < floor:
            pos[1] = floor
        return cf(pos, rot)
    if spec.mode == "both":
        g = both_grip(parts, spec.align)
    else:
        g = grip_frame(parts, spec.mode)
    return g @ local


# ---------------------------------------------------------------------------
# Frame & GIF output
# ---------------------------------------------------------------------------

VIEW_ANGLES = {   # azimuth (deg, 0 = in front of the character), elevation (deg)
    "front": (32, 14),
    "front_l": (-32, 14),
    "side": (90, 10),
    "side_l": (-90, 10),
    "back": (160, 16),
    "back_r": (200, 16),
    "back_low": (165, -6),
    "top": (30, 45),
}


def make_camera(view: str, center: np.ndarray, radius: float, w: int, h: int, fov=34.0) -> Camera:
    az, el = VIEW_ANGLES[view]
    dist = radius / math.sin(math.radians(fov / 2)) * 1.02
    a, e = math.radians(az), math.radians(el)
    # character faces -Z; azimuth 0 puts the camera at -Z looking back at it
    eye = center + dist * np.array([math.sin(a) * math.cos(e), math.sin(e), -math.cos(a) * math.cos(e)])
    return Camera(eye, center, w, h, fov)


def scenery_boxes(items, t):
    """Preview-only scenery. Items:
       ("box", center, size, colour)
       ("tiles", origin, u_axis, v_axis, nu, nv, tile, thickness, (col_a, col_b), (scroll_u, scroll_v))
    """
    out = []
    for it in items:
        if it[0] == "box":
            _, c, size, col = it
            out.append((cf(c), np.array(size, float), col))
        elif it[0] == "tiles":
            _, origin, u, v, nu, nv, tile, thick, cols, scroll = it
            u = np.array(u, float)
            v = np.array(v, float)
            n = np.cross(u, v)
            rot = np.stack([u, v, n], 1)
            su = (scroll[0] * t) % (2 * tile)
            sv = (scroll[1] * t) % (2 * tile)
            for i in range(-1, nu + 1):
                for j in range(-1, nv + 1):
                    cu = (i + 0.5) * tile + su
                    cvv = (j + 0.5) * tile + sv
                    if not (0 <= cu <= nu * tile and 0 <= cvv <= nv * tile):
                        continue
                    col = cols[(i + j) % 2]
                    c = np.array(origin, float) + u * cu + v * cvv
                    out.append((cf(c, rot), np.array([tile, tile, thick], float), col))
    return out


def build_mesh(parts, props_world: List[Tuple[str, np.ndarray]], scenery=()):
    mesh = Mesh()
    shadow_boxes = []
    for m, size, col in scenery:
        mesh.box(m, size, col)
    for name in ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg"):
        m = parts[name]
        size = PART_SIZE[name]
        mesh.box(m, size, COL[name])
        shadow_boxes.append((m, np.array(size, float)))
    add_face(mesh, parts["Head"])
    for kind, pm in props_world:
        for lm, size, col in prop_boxes(kind):
            wm = pm @ lm
            mesh.box(wm, size, col)
            shadow_boxes.append((wm, np.array(size, float)))
    return mesh, shadow_boxes


def _fx_draw(dr: ImageDraw.ImageDraw, kind: str, sx: float, sy: float, age: float, scale: float):
    """Draw on an RGBA overlay."""
    life = {"hit": 0.18, "bighit": 0.28, "block": 0.2, "break": 0.34, "dust": 0.42, "spark": 0.14}[kind]
    if age < 0 or age > life:
        return
    k = age / life
    fade = int(255 * (1 - k * k))
    if kind in ("hit", "bighit", "block", "break", "spark"):
        col = {"hit": (255, 236, 120), "bighit": (255, 196, 70), "block": (175, 225, 255),
               "break": (255, 110, 80), "spark": (255, 250, 200)}[kind]
        rays = {"break": 14, "spark": 6}.get(kind, 10)
        big = 1.7 if kind in ("bighit", "break") else 1.0
        r0 = scale * (0.25 + 0.7 * k) * big
        r1 = r0 + scale * (0.9 - 0.5 * k) * big
        width = max(2, int(scale * 0.16 * (1 - k)))
        for i in range(rays):
            a = 2 * math.pi * i / rays + (0.31 if kind == "block" else 0.0) + 0.17 * (i % 2)
            rr1 = r1 * (0.75 if i % 2 else 1.0)
            dr.line([(sx + r0 * math.cos(a), sy + r0 * math.sin(a)), (sx + rr1 * math.cos(a), sy + rr1 * math.sin(a))],
                    fill=col + (fade,), width=width)
        if k < 0.45:
            rr = scale * 0.38 * (1 - k) * big
            dr.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=(255, 255, 255, int(230 * (1 - k / 0.45))))
        if kind == "block":
            rr = scale * (0.5 + 1.2 * k)
            dr.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], outline=(200, 235, 255, fade), width=max(2, int(scale * 0.1)))
    elif kind == "dust":
        for i in range(9):
            side = -1 if i % 2 else 1
            a = (i // 2) / 4.0
            d = scale * (0.3 + (1.2 + 0.8 * a) * k)
            rr = scale * (0.32 + 0.25 * k) * (1.1 - 0.4 * a)
            cx = sx + side * d
            cy = sy - scale * (0.15 + 0.35 * a) * k
            g = 215
            dr.ellipse([cx - rr, cy - rr * 0.75, cx + rr, cy + rr * 0.75], fill=(g, g, g - 6, int(150 * (1 - k))))


def render_frame(scenes, cams, parts, props_world, fx_now, w, h, ss, scroll, scenery=()):
    tiles = []
    mesh, sboxes = build_mesh(parts, props_world, scenery)
    for scene, cam in zip(scenes, cams):
        img, zbuf = scene.background(scroll)
        sm = shadow_mask(cam, sboxes, zbuf.shape, scene.ground_y)
        ground_px = scene.below
        img = np.where((ground_px & (sm > 0))[..., None], img * (1 - 0.38 * sm[..., None]), img)
        raster(img, zbuf, cam, mesh)
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        if fx_now:
            ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            for kind, pos, age in fx_now:
                sx, sy, sz = cam.project(np.array([pos]))
                scale = cam.focal / max(sz[0], 1e-3)
                _fx_draw(dr, kind, sx[0], sy[0], age, scale)
            im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
        im = im.resize((w, h), Image.LANCZOS)
        tiles.append(im)
    return tiles


def render_gif_times(b: Baked, panels: List[dict], times, panel=(340, 340), ss=2):
    return render_gif(b, None, panels, panel=panel, ss=ss, times=times)


def render_gif(b: Baked, out_path: Optional[str], panels: List[dict], panel=(300, 300), ss=2, fps=20,
               title=None, subtitle=None, times=None):
    """panels: list of dicts {view, base (Baked|None), scroll (studs/s), label}."""
    a = b.anim
    W, H = panel
    length = a.length
    n = max(2, int(round(length * fps)))
    hold = 0 if a.loop else int(round(a.preview_hold * fps))
    frame_ts = [min(length, i / fps) for i in range(n + (0 if a.loop else 1))]
    frame_ts += [length] * hold
    if times is not None:
        frame_ts = list(times)

    def base_time(pn, t):
        base = pn.get("base")
        if base is None:
            return None
        return t % base.anim.length

    ground_y = a.preview_ground

    def root_at(t):
        if a.preview_root is None:
            return np.eye(4)
        r = a.preview_root(t)
        if len(r) == 3:
            return cf(r)
        x, y, z, yaw = r
        return cf((x, y, z), ry(yaw))

    def parts_at(pn, t):
        return pose_parts(compose(b, pn.get("base"), t, base_time(pn, t)), root_at(t))

    # --- per panel object release state ---
    for pn in panels:
        rs = {}
        for spec in a.props:
            if spec.release is not None:
                parts = parts_at(pn, spec.release)
                m0 = prop_world(spec, parts, spec.release - 1e-6, None)
                rs[id(spec)] = (m0, tuple(float(v) for v in spec.throw_vel))
        pn["_rs"] = rs

    for pn in panels:
        rest = {}
        for spec in a.props:
            if spec.appear > 0 and spec.ground_pos is None:
                parts = parts_at(pn, spec.appear)
                m = prop_world(spec, parts, spec.appear, None)
                rest[id(spec)] = m
        pn["_rest"] = rest

    def props_at(pn, t, parts):
        out = []
        for spec in a.props:
            m = prop_world(spec, parts, t, pn["_rs"].get(id(spec)), pn["_rest"].get(id(spec)))
            if m is not None:
                out.append((spec.kind, m))
        return out

    # --- framing: one bounding sphere over every panel and the whole clip ---
    pts = []
    sample_ts = frame_ts[:: max(1, len(frame_ts) // 24)] + [frame_ts[-1]]
    for pn in panels:
        for t in sample_ts:
            parts = parts_at(pn, t)
            for name in ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg"):
                m = parts[name]
                for c in _CORNERS * np.array(PART_SIZE[name], float):
                    pts.append(m[:3, 3] + m[:3, :3] @ c)
            for spec in a.props:
                if spec.release is None or t < spec.release:
                    m = prop_world(spec, parts, t, pn["_rs"].get(id(spec)), pn["_rest"].get(id(spec)))
                    for lm, size, _ in prop_boxes(spec.kind):
                        wm = m @ lm
                        for c in _CORNERS * np.array(size, float):
                            pts.append(wm[:3, 3] + wm[:3, :3] @ c)
    pts = np.array(pts)
    if ground_y >= pts[:, 1].min() - 0.8:
        pts = np.vstack([pts, [[pts[:, 0].mean(), ground_y, pts[:, 2].mean()]]])
    lo, hi = pts.min(0), pts.max(0)
    center = (lo + hi) / 2
    radius = max(3.3, float(np.max(np.linalg.norm(pts - center, axis=1))) + 0.4)
    zoom = a.preview_zoom if hasattr(a, "preview_zoom") else 1.0
    radius *= zoom

    for pn in panels:
        pn["_cam"] = make_camera(pn["view"], center, radius, W * ss, H * ss)
        pn["_scene"] = Scene(pn["_cam"], ground_y)

    def where_pos(where, parts, pw):
        if where == "rhand":
            return grip_frame(parts, "r")[:3, 3]
        if where == "lhand":
            return grip_frame(parts, "l")[:3, 3]
        if where == "hands":
            return (grip_frame(parts, "r")[:3, 3] + grip_frame(parts, "l")[:3, 3]) / 2
        if where == "prop" and pw:
            return pw[0][1][:3, 3]
        if where == "propfront" and pw:
            m = pw[0][1]
            return m[:3, 3] + np.array([0, 0, -1.0])
        if where == "propground" and pw:
            m = pw[0][1]
            return np.array([m[0, 3], GROUND_Y + 0.2, m[2, 3]])
        if where == "feet":
            r = parts["HumanoidRootPart"][:3, 3]
            return np.array([r[0], ground_y + 0.1, r[2]])
        if where == "front":
            return parts["Torso"][:3, 3] + parts["Torso"][:3, :3] @ np.array([0, 0.3, -2.2])
        if where == "rfoot":
            return (parts["Right Leg"] @ np.array([0, -1, 0, 1.0]))[:3]
        if where == "lfoot":
            return (parts["Left Leg"] @ np.array([0, -1, 0, 1.0]))[:3]
        if where.startswith("pt:"):
            x, y, z = (float(v) for v in where[3:].split(","))
            return np.array([x, y, z])
        return parts["Torso"][:3, 3]

    for pn in panels:
        cache = {}
        for ev in a.fx:
            t0, kind, where = ev
            parts = parts_at(pn, t0)
            cache[ev] = where_pos(where, parts, props_at(pn, t0, parts))
        pn["_fx"] = cache

    header = 30
    footer = 14
    frames = []
    font_t = font(15)
    font_s = font(11, False)
    font_m = font(14)
    markers = b.markers
    for t in frame_ts:
        tiles = []
        for pn in panels:
            parts = parts_at(pn, t)
            pw = props_at(pn, t, parts)
            fx_now = []
            for ev in a.fx:
                age = t - ev[0]
                if 0 <= age <= 0.4:
                    fx_now.append((ev[1], pn["_fx"][ev], age))
            scroll = pn.get("scroll", 0.0) * t
            scen = scenery_boxes(a.preview_scenery, t)
            tiles += render_frame([pn["_scene"]], [pn["_cam"]], parts, pw, fx_now, W, H, ss, scroll, scen)
        canvas = Image.new("RGB", (W * len(tiles) + 4 * (len(tiles) - 1), H + header + footer), (24, 26, 32))
        for i, tile in enumerate(tiles):
            canvas.paste(tile, (i * (W + 4), header))
        dr = ImageDraw.Draw(canvas)
        name = title or a.name
        dr.text((8, 6), name, font=font_t, fill=(255, 255, 255))
        if subtitle:
            tw = dr.textlength(name, font=font_t)
            dr.text((18 + tw, 9), subtitle, font=font_s, fill=(170, 180, 195))
        tl = f"{min(t, length):.2f}s / {length:.2f}s" + ("  loop" if a.loop else "")
        dr.text((canvas.width - dr.textlength(tl, font=font_s) - 8, 9), tl, font=font_s, fill=(170, 180, 195))
        for i, pn in enumerate(panels):
            lab = pn.get("label")
            if lab:
                tw = dr.textlength(lab, font=font_s)
                x0 = i * (W + 4) + 5
                dr.rectangle([x0, header + H - 19, x0 + tw + 8, header + H - 4], fill=(20, 24, 32))
                dr.text((x0 + 4, header + H - 18), lab, font=font_s, fill=(235, 240, 248))
        y0 = H + header + 4
        dr.rectangle([6, y0, canvas.width - 6, y0 + 5], fill=(55, 60, 70))
        prog = min(1.0, t / length) if length > 0 else 1
        dr.rectangle([6, y0, 6 + (canvas.width - 12) * prog, y0 + 5], fill=(255, 196, 45))
        for mt, mn in markers:
            x = 6 + (canvas.width - 12) * (mt / length)
            dr.rectangle([x - 1, y0 - 2, x + 1, y0 + 7], fill=(90, 200, 255))
        recent = [mn for mt, mn in markers if 0 <= t - mt < 0.16]
        if recent:
            txt = recent[-1].upper()
            tw = dr.textlength(txt, font=font_m)
            bx = canvas.width // 2 - tw / 2
            dr.rectangle([bx - 6, header + 6, bx + tw + 6, header + 26], fill=(90, 200, 255))
            dr.text((bx, header + 8), txt, font=font_m, fill=(15, 20, 30))
        frames.append(canvas)

    if out_path is None:
        return frames
    pal_src = Image.new("RGB", (frames[0].width, frames[0].height * 4))
    picks = [frames[int(i * (len(frames) - 1) / 3)] for i in range(4)]
    for i, fr in enumerate(picks):
        pal_src.paste(fr, (0, i * frames[0].height))
    pal = pal_src.quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    q[0].save(out_path, save_all=True, append_images=q[1:], duration=int(round(1000 / fps)), loop=0,
              optimize=False, disposal=1)
    return frames
