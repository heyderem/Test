"""Shared helpers for authoring."""

from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence, Tuple

from r6anim.core import Anim, H, LA, LL, RA, RL, T, mirror  # noqa: F401  (re-export)

Pose = List[Tuple[str, dict]]


def as_dict(pose: Pose) -> Dict[str, dict]:
    return {j: dict(p) for j, p in pose}


def blend(a: Pose, b: Pose, w: float) -> Pose:
    """Linear blend of two poses (parameters missing on one side count as 0,
    except 'piv' which defaults to -1)."""
    da, db = as_dict(a), as_dict(b)
    out = []
    for j in list(da.keys()) + [k for k in db.keys() if k not in da]:
        pa, pb = da.get(j, {}), db.get(j, {})
        keys = set(pa) | set(pb)
        q = {}
        for k in keys:
            dflt = -1.0 if k == "piv" else 0.0
            q[k] = pa.get(k, dflt) * (1 - w) + pb.get(k, dflt) * w
        out.append((j, q))
    return out


def add(a: Pose, delta: Pose) -> Pose:
    da = as_dict(a)
    for j, p in delta:
        q = da.setdefault(j, {})
        for k, v in p.items():
            q[k] = q.get(k, -1.0 if k == "piv" else 0.0) + v
    return [(j, p) for j, p in da.items()]


def tremble(t: float, seed: int, amp: float) -> float:
    """Deterministic jittery shake built from a few incommensurate sines."""
    r = random.Random(seed)
    f = [r.uniform(9, 13), r.uniform(15, 21), r.uniform(25, 31)]
    ph = [r.uniform(0, 6.28) for _ in range(3)]
    return amp * (0.55 * math.sin(f[0] * t + ph[0]) + 0.3 * math.sin(f[1] * t + ph[1]) + 0.15 * math.sin(f[2] * t + ph[2]))


def smoothstep(a: float) -> float:
    a = max(0.0, min(1.0, a))
    return a * a * (3 - 2 * a)


# --- reusable stances --------------------------------------------------------

NEUTRAL: Pose = [T(), H(), RA(), LA(), RL(), LL()]

RELAXED: Pose = [T(pitch=2), H(pitch=-1), RA(fwd=4, out=7, twist=4), LA(fwd=4, out=7, twist=4),
                 RL(out=3, twist=5), LL(out=3, twist=5)]

RUN_READY: Pose = [T(pitch=12, y=-0.12), H(pitch=-9), RA(fwd=22, out=16), LA(fwd=-18, out=20),
                   RL(fwd=18), LL(fwd=-16)]

# fighting guard (orthodox: left side forward)
GUARD: Pose = [T(turn=16, pitch=6, y=-0.18), H(turn=-14, pitch=4),
               RA(fwd=78, out=6, yaw=-38, twist=-10), LA(fwd=86, out=10, yaw=-30, twist=-6),
               RL(fwd=-14, out=8, twist=18), LL(fwd=16, out=6, twist=-6)]

BRACE_WIDE: Pose = [RL(fwd=-22, out=14, twist=10), LL(fwd=22, out=12, twist=-6)]


# --- preview scenery (not part of the animations) ---------------------------

TEAL = ((96, 138, 138), (74, 108, 110))
GREY = ((128, 130, 136), (104, 106, 112))


def wall_front(face_z, x0, x1, y0, y1, tile=2.0, scroll_v=0.0, cols=TEAL, depth=3.0):
    """Checker wall facing +Z (in front of a character that faces -Z)."""
    nu = int(round((x1 - x0) / tile))
    nv = int(round((y1 - y0) / tile))
    return [("box", ((x0 + x1) / 2, (y0 + y1) / 2, face_z - depth / 2 - 0.06), (x1 - x0, y1 - y0, depth), (70, 90, 95)),
            ("tiles", (x0, y0, face_z), (1, 0, 0), (0, 1, 0), nu, nv, tile, 0.1, cols, (0.0, scroll_v))]


def wall_side(face_x, z0, z1, y0, y1, tile=2.0, scroll_u=0.0, cols=TEAL, depth=3.0):
    """Checker wall on the character's right (face_x > 0) or left (face_x < 0)."""
    nu = int(round((z1 - z0) / tile))
    nv = int(round((y1 - y0) / tile))
    sgn = 1 if face_x > 0 else -1
    if sgn > 0:
        tiles = ("tiles", (face_x, y0, z0), (0, 0, 1), (0, 1, 0), nu, nv, tile, 0.1, cols, (scroll_u, 0.0))
    else:
        tiles = ("tiles", (face_x, y0, z1), (0, 0, -1), (0, 1, 0), nu, nv, tile, 0.1, cols, (-scroll_u, 0.0))
    return [("box", (face_x + sgn * (depth / 2 + 0.06), (y0 + y1) / 2, (z0 + z1) / 2), (depth, y1 - y0, z1 - z0), (70, 90, 95)),
            tiles]


def ledge(face_z, top_y, x0=-7.0, x1=7.0, bottom=-12.0, tile=2.0):
    """Wall in front with a flat top (a ledge to climb onto)."""
    items = wall_front(face_z, x0, x1, bottom, top_y - 0.12, tile=tile, depth=6.0)
    items.append(("box", ((x0 + x1) / 2, top_y - 0.06, face_z - 3.0 + 0.03), (x1 - x0, 0.12, 6.06), (150, 196, 190)))
    return items


def cyc(a, joint_fn, keys, shift=0.0, e="smooth", mirror_side=False):
    """Key one joint of a looping animation by cycle phase (0..1).

    keys  = [(phase, {params}), ...]; phases may be in any order.
    shift = phase offset added to every key (0.5 = half a cycle later).
    Keys are repeated one cycle before and after so interpolation across the
    loop point (and Catmull-Rom tangents) stay seamless."""
    L = a.length
    flip = ("turn", "roll", "x")
    for ph, p in keys:
        q = dict(p)
        if mirror_side:
            for k in flip:
                if k in q:
                    q[k] = -q[k]
        base = (ph + shift) % 1.0
        for rep in (-1, 0, 1):
            t = (base + rep) * L
            if -0.35 * L <= t <= 1.35 * L:
                a.k(round(t, 5), joint_fn(**q), e=e)
