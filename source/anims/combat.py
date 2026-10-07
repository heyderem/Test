"""Unarmed attacks (same snappy style as the movement set)."""

from __future__ import annotations

from r6anim.core import Anim
from .common import GUARD, H, LA, LL, RA, RL, T, add

CAT = "Combat"
UB_PANELS = [("front", "Idle", 0, "over Idle"), ("side", "Sprint", 9.5, "over Sprint")]


def _ub(a: Anim, src_name: str):
    a.upper_only = True
    a.category = "Combat"
    a.description = f"Upper-body-only version of {src_name}: plays on top of Walk/Sprint (legs keep running)."
    a.preview_panels = UB_PANELS
    return a


def punch1(ub=False):
    a = Anim("Punch1_UB" if ub else "Punch1", 0.36, priority="Action2", category=CAT,
             description="Combo hit 1 - quick lead-hand jab.")
    a.k(0.0, *GUARD)
    a.k(0.05, *add(GUARD, [T(turn=-6), LA(fwd=-6, yaw=4)]), e="in")
    a.k(0.11, T(turn=32, pitch=8, y=-0.2, z=0.15), H(turn=-28, pitch=4), RA(fwd=78, out=6, yaw=-40, twist=-10),
        LA(fwd=93, out=4, yaw=-6, z=0.4, twist=0), RL(fwd=-16, out=8, twist=22), LL(fwd=20, out=6, twist=-6), e="out")
    a.k(0.19, T(turn=30, pitch=8, y=-0.2, z=0.12), H(turn=-26, pitch=4), RA(fwd=78, out=6, yaw=-40, twist=-10),
        LA(fwd=91, out=4, yaw=-8, z=0.3), RL(fwd=-16, out=8, twist=22), LL(fwd=20, out=6, twist=-6))
    a.k(0.36, *GUARD)
    a.mark(0.05, "Swing")
    a.mark(0.11, "Hit")
    a.fx = [(0.11, "hit", "lhand")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return _ub(a, "Punch1") if ub else a


def punch2(ub=False):
    a = Anim("Punch2_UB" if ub else "Punch2", 0.42, priority="Action2", category=CAT,
             description="Combo hit 2 - rear-hand cross with hip turn.")
    a.k(0.0, *GUARD)
    a.k(0.07, *add(GUARD, [T(turn=10), RA(fwd=-6, yaw=4)]), e="in")
    a.k(0.15, T(turn=-28, pitch=10, y=-0.24, z=0.22), H(turn=22, pitch=2), RA(fwd=93, out=2, yaw=-4, z=0.48),
        LA(fwd=80, out=8, yaw=-42, twist=-6), RL(fwd=-26, out=8, twist=34), LL(fwd=22, out=6, twist=-10), e="out")
    a.k(0.24, T(turn=-26, pitch=10, y=-0.24, z=0.18), H(turn=20, pitch=2), RA(fwd=91, out=2, yaw=-6, z=0.36),
        LA(fwd=80, out=8, yaw=-42, twist=-6), RL(fwd=-26, out=8, twist=34), LL(fwd=22, out=6, twist=-10))
    a.k(0.42, *GUARD)
    a.mark(0.07, "Swing")
    a.mark(0.15, "Hit")
    a.fx = [(0.15, "hit", "rhand")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return _ub(a, "Punch2") if ub else a


def punch3(ub=False):
    a = Anim("Punch3_UB" if ub else "Punch3", 0.46, priority="Action2", category=CAT,
             description="Combo hit 3 - wide lead hook.")
    a.k(0.0, *GUARD)
    a.k(0.08, T(turn=-14, pitch=6, y=-0.22), H(turn=8), RA(fwd=78, out=6, yaw=-36, twist=-10),
        LA(fwd=90, out=30, yaw=52, twist=10), RL(fwd=-14, out=8, twist=10), LL(fwd=16, out=6), e="in")
    a.k(0.16, T(turn=36, pitch=8, y=-0.24, z=0.12), H(turn=-26), RA(fwd=80, out=6, yaw=-40, twist=-10),
        LA(fwd=94, out=8, yaw=-26, twist=-10, z=0.2), RL(fwd=-18, out=8, twist=26), LL(fwd=18, out=6, twist=-12), e="out")
    a.k(0.25, T(turn=42, pitch=8, y=-0.24, z=0.1), H(turn=-30), RA(fwd=80, out=6, yaw=-40, twist=-10),
        LA(fwd=90, out=8, yaw=-44, twist=-12), RL(fwd=-18, out=8, twist=26), LL(fwd=18, out=6, twist=-12))
    a.k(0.46, *GUARD)
    a.mark(0.08, "Swing")
    a.mark(0.16, "Hit")
    a.fx = [(0.16, "hit", "lhand")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return _ub(a, "Punch3") if ub else a


def punch4():
    a = Anim("Punch4", 0.62, priority="Action2", category=CAT,
             description="Combo finisher - dipping rising uppercut (launcher).")
    a.k(0.0, *GUARD)
    a.k(0.13, T(turn=22, pitch=16, y=-0.6), H(turn=-14, pitch=6), RA(fwd=8, out=22, yaw=-8, twist=10),
        LA(fwd=84, out=10, yaw=-34), RL(fwd=-30, out=12, twist=14), LL(fwd=30, out=10), e="in")
    a.k(0.23, T(turn=-22, pitch=-16, y=0.12, z=0.15), H(turn=12, pitch=-16), RA(fwd=168, out=4, yaw=-14, z=0.25),
        LA(fwd=58, out=18, yaw=-40), RL(fwd=-12, out=8, twist=22), LL(fwd=22, out=6), e="out")
    a.k(0.36, T(turn=-24, pitch=-18, y=0.1, z=0.12), H(turn=12, pitch=-18), RA(fwd=172, out=6, yaw=-12, z=0.15),
        LA(fwd=50, out=20, yaw=-40), RL(fwd=-12, out=8, twist=22), LL(fwd=22, out=6))
    a.k(0.62, *GUARD)
    a.mark(0.13, "Swing")
    a.mark(0.22, "Hit")
    a.fx = [(0.22, "bighit", "rhand")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def kick():
    a = Anim("Kick", 0.72, priority="Action2", category=CAT,
             description="Spinning-hip roundhouse kick.")
    a.k(0.0, *GUARD)
    a.k(0.13, T(turn=14, pitch=-6, roll=-12, y=-0.1), H(turn=-12, roll=8), RA(fwd=40, out=40, yaw=10),
        LA(fwd=86, out=12, yaw=-34), RL(fwd=40, out=62, twist=10), LL(fwd=-4, out=8, twist=-20), e="in")
    a.k(0.26, T(turn=-46, pitch=-10, roll=-28, y=-0.12), H(turn=30, roll=22), RA(fwd=-28, out=46),
        LA(fwd=82, out=16, yaw=-30), RL(fwd=88, out=16, yaw=0, twist=-10), LL(fwd=-6, out=10, twist=-40), e="out")
    a.k(0.4, T(turn=-56, pitch=-8, roll=-24, y=-0.12), H(turn=36, roll=20), RA(fwd=-24, out=44),
        LA(fwd=80, out=16, yaw=-30), RL(fwd=76, out=-8, yaw=0, twist=-14), LL(fwd=-6, out=10, twist=-44))
    a.k(0.72, *GUARD)
    a.mark(0.13, "Swing")
    a.mark(0.26, "Hit")
    a.fx = [(0.26, "hit", "pt:0.0,0.3,-3.0")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def heavy_punch():
    a = Anim("HeavyPunch", 1.0, priority="Action2", category=CAT,
             description="Charged heavy punch: deep wind-up, lunging step, big follow-through.")
    a.k(0.0, *GUARD)
    a.k(0.36, T(turn=56, pitch=-6, y=-0.36, z=-0.15), H(turn=-46, pitch=6), RA(fwd=-34, out=42, twist=20),
        LA(fwd=74, out=22, yaw=-6), RL(fwd=-20, out=14, twist=24), LL(fwd=28, out=10), e="in3")
    a.k(0.48, T(turn=-42, pitch=26, y=-0.42, z=0.65), H(turn=32, pitch=-16), RA(fwd=94, out=2, yaw=-2, z=0.55),
        LA(fwd=-36, out=40), RL(fwd=-44, out=10, twist=30), LL(fwd=46, out=8), e="out")
    a.k(0.7, T(turn=-46, pitch=30, y=-0.46, z=0.6), H(turn=34, pitch=-18), RA(fwd=88, out=4, yaw=-8, z=0.35),
        LA(fwd=-40, out=42), RL(fwd=-44, out=10, twist=30), LL(fwd=46, out=8))
    a.k(1.0, *GUARD)
    a.mark(0.05, "Charge")
    a.mark(0.38, "Swing")
    a.mark(0.48, "Hit")
    a.fx = [(0.48, "bighit", "rhand"), (0.48, "dust", "feet")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def build():
    return [punch1(), punch2(), punch3(), punch4(), kick(), heavy_punch(),
            punch1(True), punch2(True), punch3(True)]
