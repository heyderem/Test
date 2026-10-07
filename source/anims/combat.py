"""Unarmed attacks, in the movement set's style.

Torso rules (the chest is never square to the camera in a strike):
  * the hips/chest turn 30-45 degrees into every punch
  * the shoulder of the striking arm drops forward (roll toward that side)
  * the head counter-turns to keep looking at the target
  * strikes land in 2-3 frames, hold 4-5 frames, then settle back to guard
"""

from __future__ import annotations

from r6anim.core import Anim
from .common import H, LA, LL, RA, RL, T, add

CAT = "Combat"
UB_PANELS = [("front", "Idle", 0, "over Idle"), ("side", "Sprint", 9.5, "over Sprint")]
FRONT_SIDE = [("front", None, 0, ""), ("side", None, 0, "")]

# fighting guard (left side forward): chest turned, slightly rolled, fists up
GUARD = [T(turn=18, pitch=8, roll=-4, y=-0.1), H(turn=-16, pitch=4, roll=3),
         RA(fwd=80, out=8, yaw=-36, twist=-10), LA(fwd=86, out=10, yaw=-28, twist=-6),
         RL(fwd=-16, out=8, twist=18), LL(fwd=18, out=6, twist=-6)]


def _ub(a: Anim, src_name: str):
    a.upper_only = True
    a.description = f"Upper-body-only version of {src_name}: plays on top of Walk/Sprint (legs keep running)."
    a.preview_panels = UB_PANELS
    return a


def punch1(ub=False):
    a = Anim("Punch1_UB" if ub else "Punch1", 0.36, priority="Action2", category=CAT,
             description="Combo hit 1: lead-hand jab, chest snaps round and the left shoulder drives forward.")
    a.k(0.0, *GUARD)
    a.k(0.05, *add(GUARD, [T(turn=-6, roll=2), LA(fwd=-8, yaw=4)]), e="in")
    a.k(0.11, T(turn=36, pitch=10, roll=-9, y=-0.12, z=0.15), H(turn=-32, pitch=4, roll=6),
        RA(fwd=80, out=8, yaw=-40, twist=-10), LA(fwd=94, out=2, yaw=-4, z=0.4),
        RL(fwd=-18, out=8, twist=22), LL(fwd=22, out=6, twist=-6), e="out")
    a.k(0.19, T(turn=33, pitch=10, roll=-8, y=-0.12, z=0.12), H(turn=-29, pitch=4, roll=5),
        RA(fwd=80, out=8, yaw=-40, twist=-10), LA(fwd=91, out=3, yaw=-8, z=0.3),
        RL(fwd=-18, out=8, twist=22), LL(fwd=22, out=6, twist=-6))
    a.k(0.36, *GUARD)
    a.mark(0.05, "Swing")
    a.mark(0.11, "Hit")
    a.preview_panels = FRONT_SIDE
    return _ub(a, "Punch1") if ub else a


def punch2(ub=False):
    a = Anim("Punch2_UB" if ub else "Punch2", 0.42, priority="Action2", category=CAT,
             description="Combo hit 2: rear cross, full hip and chest turn, right shoulder rolls through.")
    a.k(0.0, *GUARD)
    a.k(0.07, *add(GUARD, [T(turn=10, roll=-3), RA(fwd=-8, yaw=4)]), e="in")
    a.k(0.15, T(turn=-30, pitch=12, roll=10, y=-0.16, z=0.25), H(turn=24, pitch=2, roll=-7),
        RA(fwd=94, out=0, yaw=-2, z=0.5), LA(fwd=78, out=10, yaw=-42, twist=-6),
        RL(fwd=-28, out=8, twist=34), LL(fwd=24, out=6, twist=-10), e="out")
    a.k(0.24, T(turn=-27, pitch=12, roll=9, y=-0.16, z=0.2), H(turn=22, pitch=2, roll=-6),
        RA(fwd=91, out=2, yaw=-6, z=0.36), LA(fwd=78, out=10, yaw=-42, twist=-6),
        RL(fwd=-28, out=8, twist=34), LL(fwd=24, out=6, twist=-10))
    a.k(0.42, *GUARD)
    a.mark(0.07, "Swing")
    a.mark(0.15, "Hit")
    a.preview_panels = FRONT_SIDE
    return _ub(a, "Punch2") if ub else a


def punch3(ub=False):
    a = Anim("Punch3_UB" if ub else "Punch3", 0.46, priority="Action2", category=CAT,
             description="Combo hit 3: wide lead hook, chest coils back then whips through.")
    a.k(0.0, *GUARD)
    a.k(0.08, T(turn=-16, pitch=6, roll=7, y=-0.16), H(turn=10, roll=-4), RA(fwd=80, out=8, yaw=-36, twist=-10),
        LA(fwd=88, out=34, yaw=52, twist=10), RL(fwd=-16, out=8, twist=10), LL(fwd=18, out=6), e="in")
    a.k(0.16, T(turn=40, pitch=9, roll=-11, y=-0.18, z=0.12), H(turn=-30, roll=7), RA(fwd=82, out=8, yaw=-40, twist=-10),
        LA(fwd=94, out=8, yaw=-26, twist=-10, z=0.2), RL(fwd=-20, out=8, twist=26), LL(fwd=20, out=6, twist=-12), e="out")
    a.k(0.25, T(turn=46, pitch=9, roll=-12, y=-0.18, z=0.1), H(turn=-34, roll=8), RA(fwd=82, out=8, yaw=-40, twist=-10),
        LA(fwd=90, out=8, yaw=-44, twist=-12), RL(fwd=-20, out=8, twist=26), LL(fwd=20, out=6, twist=-12))
    a.k(0.46, *GUARD)
    a.mark(0.08, "Swing")
    a.mark(0.16, "Hit")
    a.preview_panels = FRONT_SIDE
    return _ub(a, "Punch3") if ub else a


def punch4():
    a = Anim("Punch4", 0.62, priority="Action2", category=CAT,
             description="Combo finisher: dip with the chest rolled over the right hip, then a rising uppercut "
                         "that rolls the body the other way (launcher).")
    a.k(0.0, *GUARD)
    a.k(0.13, T(turn=24, pitch=18, roll=12, y=-0.5), H(turn=-16, pitch=6, roll=-8), RA(fwd=6, out=24, yaw=-8, twist=10),
        LA(fwd=84, out=12, yaw=-34), RL(fwd=-30, out=12, twist=14), LL(fwd=30, out=10), e="in")
    a.k(0.23, T(turn=-24, pitch=-16, roll=-10, y=0.1, z=0.15), H(turn=14, pitch=-16, roll=6),
        RA(fwd=168, out=4, yaw=-14, z=0.25), LA(fwd=56, out=20, yaw=-40), RL(fwd=-12, out=8, twist=22),
        LL(fwd=22, out=6), e="out")
    a.k(0.36, T(turn=-26, pitch=-18, roll=-11, y=0.08, z=0.12), H(turn=14, pitch=-18, roll=6),
        RA(fwd=172, out=6, yaw=-12, z=0.15), LA(fwd=50, out=22, yaw=-40), RL(fwd=-12, out=8, twist=22), LL(fwd=22, out=6))
    a.k(0.62, *GUARD)
    a.mark(0.13, "Swing")
    a.mark(0.22, "Hit")
    a.preview_panels = FRONT_SIDE
    return a


def kick():
    a = Anim("Kick", 0.72, priority="Action2", category=CAT,
             description="Roundhouse kick: chest leans well away from the kicking leg and turns through.")
    a.k(0.0, *GUARD)
    a.k(0.13, T(turn=14, pitch=-6, roll=-14, y=-0.06), H(turn=-12, roll=10), RA(fwd=40, out=44, yaw=10),
        LA(fwd=86, out=12, yaw=-34), RL(fwd=40, out=62, twist=10), LL(fwd=-4, out=8, twist=-20), e="in")
    a.k(0.26, T(turn=-46, pitch=-10, roll=-30, y=-0.1), H(turn=30, roll=24), RA(fwd=-28, out=50),
        LA(fwd=82, out=16, yaw=-30), RL(fwd=88, out=16, twist=-10), LL(fwd=-6, out=10, twist=-40), e="out")
    a.k(0.4, T(turn=-56, pitch=-8, roll=-26, y=-0.1), H(turn=36, roll=21), RA(fwd=-24, out=48),
        LA(fwd=80, out=16, yaw=-30), RL(fwd=76, out=-8, twist=-14), LL(fwd=-6, out=10, twist=-44))
    a.k(0.72, *GUARD)
    a.mark(0.13, "Swing")
    a.mark(0.26, "Hit")
    a.preview_panels = FRONT_SIDE
    return a


def heavy_punch():
    a = Anim("HeavyPunch", 1.0, priority="Action2", category=CAT,
             description="Charged heavy punch: chest coils right and rolls back, lunging step, the whole body rolls "
                         "into a long follow-through.")
    a.k(0.0, *GUARD)
    a.k(0.36, T(turn=58, pitch=-8, roll=8, y=-0.3, z=-0.15), H(turn=-48, pitch=6, roll=-5),
        RA(fwd=-34, out=44, twist=20), LA(fwd=74, out=24, yaw=-6), RL(fwd=-20, out=14, twist=24), LL(fwd=28, out=10), e="in3")
    a.k(0.48, T(turn=-42, pitch=26, roll=14, y=-0.36, z=0.65), H(turn=32, pitch=-16, roll=-9),
        RA(fwd=94, out=2, yaw=-2, z=0.55), LA(fwd=-36, out=42), RL(fwd=-44, out=10, twist=30), LL(fwd=46, out=8), e="out")
    a.k(0.7, T(turn=-46, pitch=30, roll=15, y=-0.4, z=0.6), H(turn=34, pitch=-18, roll=-10),
        RA(fwd=88, out=4, yaw=-8, z=0.35), LA(fwd=-40, out=44), RL(fwd=-44, out=10, twist=30), LL(fwd=46, out=8))
    a.k(1.0, *GUARD)
    a.mark(0.05, "Charge")
    a.mark(0.38, "Swing")
    a.mark(0.48, "Hit")
    a.preview_panels = FRONT_SIDE
    return a


def punch_blocked():
    a = Anim("PunchBlocked", 0.55, priority="Action3", category=CAT,
             description="Your punch/kick hits a block: fist knocked back, chest twisted open, recoil half-step, "
                         "guard back up.")
    a.k(0.0, T(turn=-27, pitch=12, roll=9, y=-0.16, z=0.2), H(turn=22, pitch=2, roll=-6), RA(fwd=91, out=2, yaw=-6, z=0.4),
        LA(fwd=78, out=10, yaw=-42, twist=-6), RL(fwd=-28, out=8, twist=34), LL(fwd=24, out=6, twist=-10), e="out")
    a.k(0.06, T(turn=16, pitch=-14, roll=-8, y=-0.16, z=-0.28), H(turn=-6, pitch=-20, roll=8), RA(fwd=122, out=42, twist=24),
        LA(fwd=60, out=32, yaw=-20), RL(fwd=-30, out=8), LL(fwd=8, out=8), e="io")
    a.k(0.22, T(turn=12, pitch=-4, roll=-5, y=-0.2, z=-0.36), H(pitch=-6, roll=3), RA(fwd=86, out=28, yaw=-10, twist=10),
        LA(fwd=74, out=16, yaw=-30), RL(fwd=-20, out=8, twist=14), LL(fwd=6, out=8))
    a.k(0.55, *GUARD)
    a.mark(0.0, "Blocked")
    a.preview_panels = FRONT_SIDE
    return a


def build():
    return [punch1(), punch2(), punch3(), punch4(), kick(), heavy_punch(), punch_blocked(),
            punch1(True), punch2(True), punch3(True)]
