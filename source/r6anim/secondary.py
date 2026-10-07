"""
Secondary motion and foot contact, applied to the authored parameter curves
before export (so the exported keyframes contain them).

Overlap
  * drag   - head and arms trail the torso's rotation (springs on the torso
             pitch/turn/roll) and arms flop with fast vertical torso moves
  * settle - head and arm curves pass through an under-damped spring, so fast
             moves overshoot slightly and settle instead of stopping dead

Foot contact (grounded animations)
  * a leg whose lowest corner goes below the floor is angled further away
    from vertical until it touches; nearly vertical legs push the torso up
    instead (so legs never visibly sink into the ground)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

import numpy as np


@dataclass
class Overlap:
    drag: float = 0.55        # arm trail per degree of torso lag
    head: float = 0.5         # head counter-trail per degree of torso lag
    bounce: float = 20.0      # arm 'out' degrees per stud of torso vertical lag
    freq: float = 3.2         # Hz of the torso-trail spring
    zeta: float = 0.5
    settle: float = 0.4       # blend of the own-curve spring for head/arms
    settle_freq: float = 5.5
    settle_zeta: float = 0.38
    legs: float = 0.0         # settle applied to legs too (air moves)


NONE = Overlap(drag=0, head=0, bounce=0, settle=0)

ARM_KEYS = ("fwd", "out", "yaw", "twist")
HEAD_KEYS = ("pitch", "turn", "roll")


def spring(x: np.ndarray, dt: float, freq: float, zeta: float, periodic: bool) -> np.ndarray:
    """Critically/under-damped follower of signal x."""
    w = 2 * math.pi * freq
    n = len(x)
    passes = 3 if periodic else 1
    y = float(x[0])
    v = 0.0
    out = np.empty(n)
    sub = 4
    h = dt / sub
    for p in range(passes):
        for i in range(n):
            tgt = x[i]
            for _ in range(sub):
                a = w * w * (tgt - y) - 2 * zeta * w * v
                v += a * h
                y += v * h
            out[i] = y
    return out


def apply_overlap(tracks: Dict[str, Dict[str, np.ndarray]], dt: float, ov: Overlap, periodic: bool):
    """tracks[joint][param] -> sampled arrays (modified in place)."""
    if ov is None:
        return
    if "torso" in tracks and (ov.drag or ov.head or ov.bounce):
        tp = tracks["torso"]
        lag = {}
        for k in ("pitch", "turn", "roll", "y"):
            x = tp.get(k)
            if x is None:
                lag[k] = 0.0
                continue
            lag[k] = x - spring(x, dt, ov.freq, ov.zeta, periodic)
        if "head" in tracks:
            hp = tracks["head"]
            for k in ("pitch", "turn", "roll"):
                hp[k] = hp[k] - ov.head * lag[k]
        for j, s in (("ra", 1.0), ("la", -1.0)):
            if j not in tracks:
                continue
            ap = tracks[j]
            ap["fwd"] = ap["fwd"] + ov.drag * lag["pitch"] + s * ov.drag * lag["turn"]
            ap["out"] = ap["out"] + s * ov.drag * lag["roll"] - ov.bounce * lag["y"]
    if ov.settle:
        for j in ("head", "ra", "la") + (("rl", "ll") if ov.legs else ()):
            if j not in tracks:
                continue
            keys = HEAD_KEYS if j == "head" else ARM_KEYS
            amt = ov.settle if j in ("head", "ra", "la") else ov.legs
            for k in keys:
                x = tracks[j][k]
                if np.ptp(x) < 1e-6:
                    continue
                y = spring(x, dt, ov.settle_freq, ov.settle_zeta, periodic)
                tracks[j][k] = x + amt * (y - x)


# ---------------------------------------------------------------------------
# foot contact
# ---------------------------------------------------------------------------

def _leg_lowest(pr_t: Dict[str, Dict[str, float]], leg: str, world_legs: bool) -> float:
    from .core import params_to_transforms, pose_parts
    sub = {"torso": pr_t["torso"], leg: pr_t[leg]} if "torso" in pr_t else {leg: pr_t[leg]}
    tr = params_to_transforms(sub, world_legs)
    parts = pose_parts(tr)
    m = parts["Right Leg" if leg == "rl" else "Left Leg"]
    corners = np.array([[sx, -1.0, sz] for sx in (-0.5, 0.5) for sz in (-0.5, 0.5)])
    pts = corners @ m[:3, :3].T + m[:3, 3]
    return float(pts[:, 1].min())


def fix_feet(tracks: Dict[str, Dict[str, np.ndarray]], floor: float, world_legs: bool, mode: str = "fwd",
             tol: float = 0.02) -> float:
    """Returns the largest correction applied (degrees) for reporting."""
    if "torso" not in tracks or "rl" not in tracks or "ll" not in tracks:
        return 0.0
    n = len(tracks["torso"]["pitch"])
    worst = 0.0
    raises = np.zeros(n)
    default_sign = {"rl": 1.0, "ll": -1.0} if mode == "fwd" else {"rl": 1.0, "ll": 1.0}
    key = "fwd" if mode == "fwd" else "out"
    for i in range(n):
        pr = {j: {k: float(v[i]) for k, v in tracks[j].items()} for j in ("torso", "rl", "ll")}
        raise_y = 0.0
        for leg in ("rl", "ll"):
            low = _leg_lowest(pr, leg, world_legs)
            pen = floor - tol - low
            if pen <= 0:
                continue
            cur = pr[leg][key]
            mag = abs(cur)
            sign = math.copysign(1.0, cur) if mag > 1e-6 else default_sign[leg]
            w = min(1.0, max(0.0, (mag - 3.0) / 6.0))   # near-vertical legs: lift the torso instead
            if w > 0:
                lo, hi = 0.0, 70.0
                base = dict(pr[leg])
                for _ in range(16):
                    mid = (lo + hi) / 2
                    pr[leg] = dict(base, **{key: cur + sign * mid})
                    if _leg_lowest(pr, leg, world_legs) < floor - tol:
                        lo = mid
                    else:
                        hi = mid
                delta = hi * w
                pr[leg] = dict(base, **{key: cur + sign * delta})
                tracks[leg][key][i] = cur + sign * delta
                worst = max(worst, delta)
            low = _leg_lowest(pr, leg, world_legs)
            raise_y = max(raise_y, floor - tol - low)
        raises[i] = max(raise_y, 0.0)
    if raises.any():
        # widen then smooth so the lift eases in and out instead of popping
        k = 6
        wide = np.array([raises[max(0, i - k):i + k + 1].max() for i in range(n)])
        ker = np.exp(-0.5 * (np.arange(-2 * k, 2 * k + 1) / (k * 0.6)) ** 2)
        ker /= ker.sum()
        pad = np.pad(wide, 2 * k, mode="edge")
        smooth = np.convolve(pad, ker, mode="same")[2 * k:-2 * k]
        lift = np.maximum(smooth, raises)
        tracks["torso"]["y"] += lift
        worst = max(worst, float(lift.max()) * 30)
    return worst
