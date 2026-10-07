"""
Object handling for four weight classes.

  Small   (rock, can, brick ...)        one hand, light and quick
  Medium  (crate, barrel, chair ...)    one hand, big dramatic wind-ups
  Large   (car, boulder, dumpster ...)  two hands overhead, heavy impacts
  Huge    (train car, plane, bus ...)   2-3x the character, titan-sized two-hand moves

Per class: Pickup, Hold (loop, arms only), Throw (+_UB), Swing (+_UB),
SwingBlocked, Block (+_UB, weakens over 4 s), BlockHit, BlockBreak.

Every animation of a class uses the SAME grip, so one weld per class works
for all of them (see README).  Strain/shake is hand-keyed (alternating
keys that grow), not noise.

Torso rules (same as the movement set): the chest is never square - it
turns into throws and swings, rolls toward the working arm, arches back on
wind-ups and crunches forward on releases; under load it sags and tilts.

Markers (AnimationTrack:GetMarkerReachedSignal):
  Pickup: Grab (+ Lift, Settle on the big ones)   Throw: Windup, Release
  Swing: Swing, Hit    SwingBlocked: Blocked      BlockHit: Impact
  Block: Raised, Weakening, Critical, Exhausted   BlockBreak: Break
"""

from __future__ import annotations

from typing import Callable, List

from r6anim.core import Anim, PropSpec
from .common import H, LA, LL, RA, RL, T, RELAXED, add, blend

UB_PANELS = [("front", "Idle", 0, "over Idle"), ("side", "Sprint", 9.5, "over Sprint")]
FULL_PANELS = [("front", None, 0, ""), ("side", None, 0, "")]
BIG_PANELS = [("front", None, 0, "body (object hidden)", {"frame": "char"}), ("front", None, 0, "with object")]
BIG_UB_PANELS = [("front", "Idle", 0, "over Idle, object hidden", {"frame": "char"}),
                 ("side", "Sprint", 9.5, "over Sprint")]

# one grip per class (preview objects only - weld these the same way in game)
SMALL_GRIP = dict(kind="small", mode="r", offset=(0, -0.36, -0.05))
MEDIUM_GRIP = dict(kind="medium", mode="r", offset=(0, -1.12, 0))
LARGE_GRIP = dict(kind="large", mode="both", align="arm", offset=(0, 1.28, 0))
HUGE_GRIP = dict(kind="huge", mode="both", align="arm", offset=(0, 1.86, 0))


def prop(base: dict, **kw) -> PropSpec:
    d = dict(base)
    d.update(kw)
    return PropSpec(**d)


def _ub_variant(src_builder, name: str, fold=("turn",), panels=None):
    a = src_builder()
    a.name = name
    a.upper_only = True
    a.fold = fold
    a.description = a.description.split(".")[0] + ". Upper-body only: plays over Walk/Sprint, legs keep running."
    a.preview_panels = panels or UB_PANELS
    return a


def strain(a: Anim, t0: float, t1: float, pose_at: Callable[[float], list], period: float,
           amp0: float, amp1: float, e="io"):
    """Hand-keyed shake: alternate keys every half period, growing from amp0
    to amp1 degrees (arms), with smaller torso/head components."""
    t = t0
    sign = 1
    while t < t1 - 1e-6:
        k = (t - t0) / max(t1 - t0, 1e-6)
        amp = amp0 + (amp1 - amp0) * k
        d = sign * amp
        a.k(round(t, 4), *add(pose_at(t), [T(pitch=0.35 * d, roll=0.25 * d, y=-0.004 * abs(d)),
                                          H(pitch=0.5 * d, roll=-0.3 * d),
                                          RA(fwd=d, out=0.4 * d), LA(fwd=-0.8 * d, out=0.4 * d)]), e=e)
        sign = -sign
        t += period / 2


# =============================================================================
# hand-keyed weakening block
# =============================================================================

def _block(name: str, size: str, start: list, strong: list, weak: list, grip: dict, period: float,
           upper=False, desc="", panels=None):
    """4 s block.  0-1.8 s solid (breathing), 1.85 first give and re-brace,
    2.65 second give with a foot sliding back, 3.0-3.55 shaking hard,
    3.65 buckle.  AdjustSpeed(4 / seconds) for a 3-5 s block."""
    L = 4.0
    a = Anim(name, L, priority="Action2", category=f"Objects/{size}",
             description=desc + " Solid for ~1.8 s, gives twice, shakes, then buckles at 4 s "
                                "(AdjustSpeed(4 / seconds) for 3-5 s).")
    up = [T(pitch=-4, y=0.05), H(pitch=-4), RA(fwd=8), LA(fwd=8)]
    breathe = [T(pitch=-1.5, y=0.03), H(pitch=-2), RA(fwd=2), LA(fwd=2)]
    a.k(0.0, *start, e="out")
    a.k(0.1, *add(strong, up), e="io")
    a.k(0.24, *strong, e="io")
    a.k(0.7, *add(strong, breathe), e="io")
    a.k(1.2, *strong, e="io")
    a.k(1.6, *add(strong, [T(pitch=-1, y=0.02), RA(fwd=1), LA(fwd=1)]), e="io")
    a.k(1.75, *strong, e="in")
    give1 = add(blend(strong, weak, 0.35), [T(pitch=5, roll=-3, y=-0.08, z=-0.08), H(pitch=8), RA(fwd=-6), LA(fwd=-6)])
    a.k(1.85, *give1, e="io")
    a.k(2.05, *add(blend(strong, weak, 0.2), [T(pitch=-3, roll=1), H(pitch=-3), RA(fwd=3), LA(fwd=3)]), e="io")
    strain(a, 2.25, 2.6, lambda t: blend(strong, weak, 0.25 + 0.1 * (t - 2.25) / 0.35), period, 0.8, 1.4)
    give2 = add(blend(strong, weak, 0.62), [T(pitch=7, roll=-5, y=-0.12, z=-0.12), H(pitch=10, roll=3),
                                            RA(fwd=-9), LA(fwd=-9), RL(fwd=-8)])
    a.k(2.65, *give2, e="io")
    a.k(2.85, *add(blend(strong, weak, 0.48), [T(pitch=-2), H(pitch=-2), RA(fwd=3), LA(fwd=3)]), e="io")
    strain(a, 2.95, 3.55, lambda t: blend(strong, weak, 0.5 + 0.3 * (t - 2.95) / 0.6), period, 1.6, 3.2)
    a.k(3.65, *add(weak, [T(pitch=6, roll=-4, y=-0.12), H(pitch=10, roll=4), RA(fwd=-10), LA(fwd=-10)]), e="out")
    a.k(3.85, *add(weak, [T(pitch=3, roll=-2, y=-0.06), H(pitch=5), RA(fwd=-4), LA(fwd=-4)]), e="io")
    a.k(4.0, *weak)
    a.mark(0.1, "Raised")
    a.mark(1.85, "Weakening")
    a.mark(3.0, "Critical")
    a.mark(3.95, "Exhausted")
    a.props = [prop(grip)]
    a.preview_panels = panels or FULL_PANELS
    a.preview_hold = 0.5
    if upper:
        a.upper_only = True
        a.export_joints = ("head", "ra", "la")
        a.description += " Upper-body only: plays over Walk/Sprint."
        a.preview_panels = BIG_UB_PANELS if size in ("Large", "Huge") else UB_PANELS
    return a


def _block_hit(size: str, strong: list, grip: dict, jolt: float, length: float, panels=None):
    a = Anim(f"{size}BlockHit", length, priority="Action3", category=f"Objects/{size}",
             description=f"{size} block takes a hit: guard and chest knocked back and twisted, feet slide, "
                         f"then re-set. Play over {size}Block (starts and ends in the block pose).")
    hit = add(strong, [T(pitch=-6 * jolt, roll=4 * jolt, turn=-4 * jolt, z=-0.22 * jolt, y=-0.07 * jolt),
                       H(pitch=-10 * jolt, roll=-3 * jolt), RA(fwd=-9 * jolt, z=-0.12 * jolt),
                       LA(fwd=-9 * jolt, z=-0.12 * jolt), RL(fwd=-6 * jolt), LL(fwd=6 * jolt)])
    a.k(0.0, *strong, e="out")
    a.k(0.05, *hit, e="io")
    a.k(0.05 + 0.35 * length, *add(blend(hit, strong, 0.7), [T(pitch=1.5 * jolt), RA(fwd=2 * jolt), LA(fwd=2 * jolt)]))
    a.k(length, *strong)
    a.mark(0.0, "Impact")
    a.props = [prop(grip)]
    a.preview_panels = panels or FULL_PANELS
    return a


# =============================================================================
# SMALL - one hand, light and quick
# =============================================================================

S_HOLD = add(RELAXED, [RA(fwd=20, out=3, twist=-16)])


def small_pickup():
    a = Anim("SmallPickup", 0.55, priority="Action2", category="Objects/Small",
             description="Quick one-hand scoop: dip and reach with the right shoulder rolled down.")
    a.k(0.0, *RELAXED)
    a.k(0.2, T(pitch=50, turn=-12, roll=8, y=-0.5), H(pitch=-16, turn=10, roll=-5), RA(fwd=62, out=10, twist=-10),
        LA(fwd=18, out=26), RL(fwd=34, out=8), LL(fwd=-30, out=8), e="io")
    a.k(0.26, T(pitch=48, turn=-12, roll=7, y=-0.48), H(pitch=-16, turn=10, roll=-5), RA(fwd=60, out=10, twist=-14),
        LA(fwd=18, out=26), RL(fwd=34, out=8), LL(fwd=-30, out=8), e="io")
    a.k(0.55, *S_HOLD)
    a.mark(0.22, "Grab")
    a.props = [prop(SMALL_GRIP, appear=0.22)]
    a.preview_panels = FULL_PANELS
    return a


def small_hold():
    a = Anim("SmallHold", 1.6, loop=True, priority="Action", category="Objects/Small", default_ease="smooth",
             export_joints=("ra",), upper_only=True,
             description="Carry a small object in the right hand. Only the right arm is animated, "
                         "so the other arm keeps swinging with Walk/Sprint.")
    a.k(0.0, RA(fwd=24, out=10, twist=-12))
    a.k(0.8, RA(fwd=29, out=11, twist=-12))
    a.close_loop()
    a.props = [prop(SMALL_GRIP)]
    a.preview_panels = UB_PANELS
    return a


def small_throw():
    a = Anim("SmallThrow", 0.5, priority="Action2", category="Objects/Small",
             description="Light one-hand flick throw: chest opens right, then snaps round with the right "
                         "shoulder rolling through.")
    a.k(0.0, *S_HOLD)
    a.k(0.12, T(turn=26, pitch=-5, roll=6, y=-0.05), H(turn=-20, roll=-4), RA(fwd=152, out=24, twist=20),
        LA(fwd=34, out=20, yaw=10), RL(fwd=-8, out=4), LL(fwd=14, out=4), e="in")
    a.k(0.2, T(turn=-20, pitch=12, roll=-8, y=-0.12, z=0.12), H(turn=14, pitch=-6, roll=5), RA(fwd=74, out=6, yaw=-10, z=0.2),
        LA(fwd=-14, out=26), RL(fwd=-18, out=4, twist=14), LL(fwd=20, out=4), e="out")
    a.k(0.3, T(turn=-26, pitch=15, roll=-9, y=-0.14, z=0.12), H(turn=18, pitch=-6, roll=6), RA(fwd=24, out=4, yaw=-36),
        LA(fwd=-20, out=28), RL(fwd=-18, out=4, twist=14), LL(fwd=20, out=4))
    a.k(0.5, *RELAXED)
    a.mark(0.02, "Windup")
    a.mark(0.2, "Release")
    a.props = [prop(SMALL_GRIP, release=0.2, throw_vel=(0, 7, -60), spin=(-900, 0, 0))]
    a.preview_panels = FULL_PANELS
    return a


def small_swing():
    a = Anim("SmallSwing", 0.45, priority="Action2", category="Objects/Small",
             description="Fast overhand smack: arm cocks up behind the head, chest whips down and round.")
    a.k(0.0, *S_HOLD)
    a.k(0.1, T(turn=18, pitch=-6, roll=6), H(turn=-12, roll=-4), RA(fwd=160, out=22, twist=10), LA(fwd=26, out=22),
        RL(fwd=-6), LL(fwd=8), e="in")
    a.k(0.18, T(turn=-16, pitch=15, roll=-8, y=-0.14, z=0.12), H(turn=10, pitch=-8, roll=5), RA(fwd=48, out=6, yaw=-14, z=0.18),
        LA(fwd=-10, out=22), RL(fwd=-16, out=4, twist=10), LL(fwd=18, out=4), e="out")
    a.k(0.27, T(turn=-14, pitch=13, roll=-7, y=-0.12, z=0.1), H(turn=10, pitch=-6, roll=4), RA(fwd=58, out=8, yaw=-12),
        LA(fwd=-8, out=22), RL(fwd=-16, out=4, twist=10), LL(fwd=18, out=4))
    a.k(0.45, *S_HOLD)
    a.mark(0.1, "Swing")
    a.mark(0.18, "Hit")
    a.props = [prop(SMALL_GRIP)]
    a.preview_panels = FULL_PANELS
    return a


def small_swing_blocked():
    a = Anim("SmallSwingBlocked", 0.5, priority="Action3", category="Objects/Small",
             description="Small-object hit bounces off a block: arm knocked up and back, chest twisted open, "
                         "half-step back.")
    a.k(0.0, T(turn=-16, pitch=15, roll=-8, y=-0.14, z=0.12), H(turn=10, pitch=-8, roll=5), RA(fwd=48, out=6, yaw=-14, z=0.18),
        LA(fwd=-10, out=22), RL(fwd=-16, out=4, twist=10), LL(fwd=18, out=4), e="out")
    a.k(0.06, T(turn=22, pitch=-10, roll=7, y=-0.12, z=-0.18), H(turn=-10, pitch=-16, roll=-5), RA(fwd=132, out=36, twist=20),
        LA(fwd=12, out=34), RL(fwd=-22, out=6), LL(fwd=8, out=6), e="io")
    a.k(0.2, T(turn=12, pitch=-4, roll=4, y=-0.16, z=-0.22), H(pitch=-8, roll=-2), RA(fwd=104, out=28, twist=14),
        LA(fwd=10, out=30), RL(fwd=-18, out=6), LL(fwd=-2, out=6))
    a.k(0.5, *S_HOLD)
    a.mark(0.0, "Blocked")
    a.props = [prop(SMALL_GRIP)]
    a.preview_panels = FULL_PANELS
    return a


S_BLOCK_STRONG = [T(pitch=10, turn=10, roll=-4, y=-0.2), H(pitch=6, turn=-8, roll=3),
                  RA(fwd=102, out=2, yaw=-42, twist=-26), LA(fwd=76, out=8, yaw=-28, twist=-10),
                  RL(fwd=-18, out=10, twist=12), LL(fwd=18, out=10)]
S_BLOCK_WEAK = [T(pitch=24, turn=4, roll=-9, y=-0.42), H(pitch=20, turn=-2, roll=5),
                RA(fwd=78, out=8, yaw=-30, twist=-20), LA(fwd=52, out=16, yaw=-14),
                RL(fwd=-26, out=12, twist=12), LL(fwd=20, out=12)]


def small_block(upper=False):
    return _block("SmallBlock_UB" if upper else "SmallBlock", "Small", S_HOLD, S_BLOCK_STRONG, S_BLOCK_WEAK,
                  SMALL_GRIP, period=0.09, upper=upper,
                  desc="Forearm guard with the small object up by the face, chest turned side-on.")


def small_block_break():
    a = Anim("SmallBlockBreak", 0.72, priority="Action3", category="Objects/Small",
             description="Guard knocked wide open, chest flung back and twisted, stumble back.")
    a.k(0.0, *S_BLOCK_WEAK, e="out")
    a.k(0.06, T(pitch=-24, turn=14, roll=8, y=-0.15, z=-0.35), H(pitch=-30, turn=-8, roll=-6), RA(fwd=146, out=54, twist=20),
        LA(fwd=112, out=62), RL(fwd=24, out=6), LL(fwd=-34, out=8), e="io")
    a.k(0.26, T(pitch=-10, turn=6, roll=-5, y=-0.34, z=-0.55), H(pitch=-12, roll=4), RA(fwd=82, out=50), LA(fwd=70, out=55),
        RL(fwd=-20, out=8), LL(fwd=16, out=8), e="io")
    a.k(0.46, T(pitch=16, roll=3, y=-0.34, z=-0.45), H(pitch=-4), RA(fwd=32, out=22), LA(fwd=26, out=24),
        RL(fwd=16, out=8), LL(fwd=-18, out=8))
    a.k(0.72, *S_HOLD)
    a.mark(0.03, "Break")
    a.props = [prop(SMALL_GRIP)]
    a.preview_panels = FULL_PANELS
    return a


# =============================================================================
# MEDIUM - one hand, dramatic
# =============================================================================

M_HOLD = add(RELAXED, [RA(fwd=162, out=12), T(roll=-5, turn=4), H(roll=3, turn=-3)])


def medium_pickup():
    a = Anim("MediumPickup", 0.8, priority="Action2", category="Objects/Medium",
             description="Bend with the right shoulder dropped, grab one-handed and swing it up overhead.")
    a.k(0.0, *RELAXED)
    a.k(0.25, T(pitch=52, turn=-12, roll=9, y=-0.62), H(pitch=-18, turn=10, roll=-6), RA(fwd=56, out=12, twist=-10),
        LA(fwd=30, out=28), RL(fwd=36, out=10), LL(fwd=-34, out=10), e="io")
    a.k(0.32, T(pitch=50, turn=-12, roll=8, y=-0.6), H(pitch=-18, turn=10, roll=-6), RA(fwd=54, out=12, twist=-10),
        LA(fwd=30, out=28), RL(fwd=36, out=10), LL(fwd=-34, out=10), e="in")
    a.k(0.55, T(pitch=-8, turn=8, roll=-8, y=0.05), H(pitch=-10, roll=4), RA(fwd=182, out=14), LA(fwd=-12, out=34),
        RL(fwd=4, out=4), LL(fwd=-4, out=4), e="out")
    a.k(0.8, *M_HOLD)
    a.mark(0.3, "Grab")
    a.props = [prop(MEDIUM_GRIP, appear=0.3)]
    a.preview_panels = FULL_PANELS
    return a


def medium_hold():
    a = Anim("MediumHold", 1.6, loop=True, priority="Action", category="Objects/Medium", default_ease="smooth",
             export_joints=("ra",), upper_only=True,
             description="Carry a medium object raised one-handed over the shoulder. Only the right arm is "
                         "animated, so the other arm keeps the Walk/Sprint swing.")
    a.k(0.0, RA(fwd=162, out=12))
    a.k(0.8, RA(fwd=158, out=15, twist=3))
    a.close_loop()
    a.props = [prop(MEDIUM_GRIP)]
    a.preview_panels = UB_PANELS
    return a


def medium_throw():
    a = Anim("MediumThrow", 0.86, priority="Action2", category="Objects/Medium",
             description="Pitcher-style one-hand throw: chest coils away and arches back over a knee lift, "
                         "then whips round and crunches down through the release.")
    a.k(0.0, *M_HOLD)
    a.k(0.28, T(turn=44, pitch=-14, roll=10, y=0.04), H(turn=-38, pitch=-4, roll=-6), RA(fwd=206, out=22, twist=10),
        LA(fwd=86, out=28, yaw=24), RL(fwd=-4, out=4), LL(fwd=56, out=10), e="io")
    a.k(0.4, T(turn=12, pitch=6, roll=4, y=-0.3), H(turn=-12, pitch=-8, roll=-2), RA(fwd=184, out=20), LA(fwd=60, out=32),
        RL(fwd=-34, out=6), LL(fwd=38, out=8), e="in")
    a.k(0.46, T(turn=-44, pitch=28, roll=-12, y=-0.4, z=0.25), H(turn=30, pitch=-18, roll=8), RA(fwd=86, out=8, yaw=-6, z=0.3),
        LA(fwd=-34, out=42), RL(fwd=-40, out=8, twist=20), LL(fwd=36, out=8), e="out")
    a.k(0.6, T(turn=-52, pitch=36, roll=-14, y=-0.45, z=0.3), H(turn=34, pitch=-20, roll=9), RA(fwd=30, out=6, yaw=-46),
        LA(fwd=-40, out=46), RL(fwd=-12, out=10), LL(fwd=36, out=8), e="io")
    a.k(0.86, *RELAXED)
    a.mark(0.05, "Windup")
    a.mark(0.46, "Release")
    a.props = [prop(MEDIUM_GRIP, release=0.46, throw_vel=(0, 11, -52), spin=(-720, 60, 0))]
    a.preview_panels = FULL_PANELS
    return a


def medium_swing():
    a = Anim("MediumSwing", 0.8, priority="Action2", category="Objects/Medium",
             description="One-handed overhead smash: rise and lean back with the chest open, then crash down "
                         "with the body rolled over the swinging arm.")
    a.k(0.0, *M_HOLD)
    a.k(0.24, T(pitch=-16, turn=20, roll=8, y=0.08), H(pitch=-8, turn=-14, roll=-5), RA(fwd=212, out=20),
        LA(fwd=40, out=38, yaw=10), RL(fwd=-10, out=4), LL(fwd=30, out=6), e="in")
    a.k(0.36, T(pitch=36, turn=-14, roll=-10, y=-0.55, z=0.2), H(pitch=-22, turn=10, roll=6), RA(fwd=80, out=8, yaw=-6, z=0.2),
        LA(fwd=-24, out=38), RL(fwd=-38, out=8), LL(fwd=42, out=8), e="out")
    a.k(0.48, T(pitch=30, turn=-12, roll=-8, y=-0.5, z=0.18), H(pitch=-18, turn=8, roll=5), RA(fwd=92, out=8, yaw=-6),
        LA(fwd=-20, out=36), RL(fwd=-38, out=8), LL(fwd=42, out=8), e="io")
    a.k(0.8, *M_HOLD)
    a.mark(0.27, "Swing")
    a.mark(0.36, "Hit")
    a.props = [prop(MEDIUM_GRIP)]
    a.preview_panels = FULL_PANELS
    return a


def medium_swing_blocked():
    a = Anim("MediumSwingBlocked", 0.66, priority="Action3", category="Objects/Medium",
             description="Medium smash slams into a block and rebounds overhead; chest thrown back and open, stagger.")
    a.k(0.0, T(pitch=26, turn=-12, roll=-8, y=-0.4, z=0.15), H(pitch=-18, turn=10, roll=5), RA(fwd=104, out=8, yaw=-6),
        LA(fwd=-20, out=36), RL(fwd=-36, out=8), LL(fwd=40, out=8), e="out")
    a.k(0.07, T(pitch=-14, turn=22, roll=8, y=-0.22, z=-0.3), H(pitch=-24, turn=-8, roll=-5), RA(fwd=200, out=34, twist=10),
        LA(fwd=22, out=44), RL(fwd=-30, out=8), LL(fwd=10, out=8), e="io")
    a.k(0.26, T(pitch=-4, turn=10, roll=4, y=-0.3, z=-0.45), H(pitch=-10, roll=-2), RA(fwd=178, out=24), LA(fwd=12, out=38),
        RL(fwd=18, out=8), LL(fwd=-14, out=8))
    a.k(0.66, *M_HOLD)
    a.mark(0.0, "Blocked")
    a.props = [prop(MEDIUM_GRIP)]
    a.preview_panels = FULL_PANELS
    return a


M_BLOCK_STRONG = [T(pitch=12, turn=8, roll=-4, y=-0.25), H(pitch=4, turn=-6, roll=3),
                  RA(fwd=96, out=4, yaw=-26, twist=-4), LA(fwd=86, out=6, yaw=-34, twist=-6),
                  RL(fwd=-22, out=12, twist=12), LL(fwd=22, out=10)]
M_BLOCK_WEAK = [T(pitch=24, turn=3, roll=-9, y=-0.5), H(pitch=16, roll=5),
                RA(fwd=72, out=8, yaw=-18, z=-0.15), LA(fwd=64, out=10, yaw=-24, z=-0.15),
                RL(fwd=-34, out=14, twist=12), LL(fwd=24, out=12)]


def medium_block(upper=False):
    return _block("MediumBlock_UB" if upper else "MediumBlock", "Medium", M_HOLD, M_BLOCK_STRONG, M_BLOCK_WEAK,
                  MEDIUM_GRIP, period=0.1, upper=upper,
                  desc="Object held out front as a shield with the off hand bracing, chest turned behind it.")


def medium_block_break():
    a = Anim("MediumBlockBreak", 0.86, priority="Action3", category="Objects/Medium",
             description="Shield-object knocked up and away, chest flung open, big stumble back.")
    a.k(0.0, *M_BLOCK_WEAK, e="out")
    a.k(0.07, T(pitch=-28, turn=16, roll=9, y=-0.2, z=-0.45), H(pitch=-32, turn=-10, roll=-6), RA(fwd=196, out=40, twist=10),
        LA(fwd=122, out=64), RL(fwd=28, out=8), LL(fwd=-38, out=8), e="io")
    a.k(0.3, T(pitch=-12, turn=6, roll=-5, y=-0.42, z=-0.7), H(pitch=-12, roll=3), RA(fwd=168, out=30), LA(fwd=74, out=58),
        RL(fwd=-24, out=8), LL(fwd=18, out=8), e="io")
    a.k(0.52, T(pitch=16, roll=-3, y=-0.4, z=-0.55), H(pitch=-6), RA(fwd=150, out=18), LA(fwd=30, out=28),
        RL(fwd=16, out=8), LL(fwd=-20, out=8))
    a.k(0.86, *M_HOLD)
    a.mark(0.03, "Break")
    a.props = [prop(MEDIUM_GRIP)]
    a.preview_panels = FULL_PANELS
    return a


# =============================================================================
# LARGE - two hands overhead, heavy
# =============================================================================

L_HOLD = [T(pitch=-2, roll=-3, y=-0.18), H(pitch=-4, roll=2), RA(fwd=174, out=18), LA(fwd=174, out=18),
          RL(fwd=-8, out=16, twist=8), LL(fwd=8, out=16, twist=8)]


def large_pickup():
    a = Anim("LargePickup", 1.1, priority="Action2", category="Objects/Large",
             description="Deep squat, grip underneath, a strained beat, then an explosive two-hand lift that "
                         "arches the chest back under it.")
    a.k(0.0, *RELAXED)
    low = [T(pitch=34, roll=3, y=-1.0), H(pitch=-26, roll=-2), RA(fwd=36, out=24, twist=-10), LA(fwd=36, out=24, twist=-10),
           RL(fwd=46, out=24), LL(fwd=-48, out=26)]
    a.k(0.34, *low, e="io")
    strain(a, 0.4, 0.5, lambda t: low, 0.08, 0.8, 1.2)
    a.k(0.72, T(pitch=-12, roll=-4, y=0.06), H(pitch=-16, roll=3), RA(fwd=186, out=16), LA(fwd=186, out=16),
        RL(fwd=6, out=16), LL(fwd=-6, out=16), e="out")
    a.k(0.88, T(pitch=-4, roll=-5, y=-0.32), H(pitch=-6, roll=3), RA(fwd=172, out=19), LA(fwd=172, out=19),
        RL(fwd=-8, out=18), LL(fwd=8, out=18), e="io")
    a.k(1.1, *L_HOLD)
    a.mark(0.4, "Grab")
    a.mark(0.86, "Settle")
    a.props = [prop(LARGE_GRIP, lift=(0.48, 0.74), ground_pos=(0, 0, -2.9))]
    a.preview_panels = BIG_PANELS
    return a


def large_hold():
    a = Anim("LargeHold", 2.0, loop=True, priority="Action", category="Objects/Large", default_ease="io",
             export_joints=("ra", "la"), upper_only=True,
             description="Large object held overhead with both arms, a slow straining sway. Arms only, so the "
                         "legs and torso come from Idle/Walk/Sprint.")
    a.k(0.0, RA(fwd=174, out=18), LA(fwd=174, out=18))
    a.k(0.5, RA(fwd=176, out=20), LA(fwd=173, out=16))
    a.k(1.0, RA(fwd=175, out=17), LA(fwd=176, out=19))
    a.k(1.5, RA(fwd=173, out=16), LA(fwd=175, out=20))
    a.k(2.0, RA(fwd=174, out=18), LA(fwd=174, out=18))
    a.props = [prop(LARGE_GRIP)]
    a.preview_panels = BIG_UB_PANELS
    return a


def large_throw():
    a = Anim("LargeThrow", 1.1, priority="Action2", category="Objects/Large",
             description="Two-hand overhead heave: arch way back, step in, launch, and fold the chest down "
                         "through a long follow-through.")
    a.k(0.0, *L_HOLD)
    a.k(0.38, T(pitch=-26, roll=-4, y=-0.46), H(pitch=-18, roll=3), RA(fwd=212, out=18), LA(fwd=212, out=18),
        RL(fwd=-26, out=12), LL(fwd=28, out=12), e="in3")
    a.k(0.5, T(pitch=24, roll=2, y=-0.26, z=0.2), H(pitch=-16), RA(fwd=132, out=14), LA(fwd=132, out=14),
        RL(fwd=-36, out=12), LL(fwd=40, out=12), e="lin")
    a.k(0.55, T(pitch=36, roll=4, y=-0.3, z=0.35), H(pitch=-20, roll=-2), RA(fwd=108, out=12), LA(fwd=108, out=12),
        RL(fwd=-38, out=12), LL(fwd=42, out=12), e="out")
    a.k(0.72, T(pitch=42, roll=5, y=-0.5, z=0.35), H(pitch=-22, roll=-3), RA(fwd=56, out=16), LA(fwd=56, out=16),
        RL(fwd=-36, out=12), LL(fwd=42, out=12), e="io")
    a.k(1.1, *RELAXED)
    a.mark(0.05, "Windup")
    a.mark(0.55, "Release")
    a.props = [prop(LARGE_GRIP, release=0.55, throw_vel=(0, 13, -40), spin=(-260, 0, 0))]
    a.preview_panels = BIG_PANELS
    return a


def large_swing():
    a = Anim("LargeSwing", 1.0, priority="Action2", category="Objects/Large",
             description="Two-handed overhead slam: rise up on the toes and arch back, then crash it into the "
                         "ground with the chest folded over it.")
    a.k(0.0, *L_HOLD)
    a.k(0.34, T(pitch=-24, roll=-4, y=0.1), H(pitch=-14, roll=3), RA(fwd=210, out=16), LA(fwd=210, out=16),
        RL(fwd=-12, out=12), LL(fwd=24, out=12), e="in3")
    a.k(0.5, T(pitch=46, roll=5, y=-0.95, z=0.2), H(pitch=-30, roll=-3), RA(fwd=96, out=14), LA(fwd=96, out=14),
        RL(fwd=-44, out=16), LL(fwd=48, out=16), e="out")
    a.k(0.64, T(pitch=43, roll=4, y=-0.9, z=0.2), H(pitch=-26, roll=-3), RA(fwd=100, out=14), LA(fwd=100, out=14),
        RL(fwd=-44, out=16), LL(fwd=48, out=16), e="io")
    a.k(1.0, *L_HOLD)
    a.mark(0.36, "Swing")
    a.mark(0.5, "Hit")
    a.props = [prop(LARGE_GRIP)]
    a.preview_panels = BIG_PANELS
    return a


def large_swing_blocked():
    a = Anim("LargeSwingBlocked", 0.9, priority="Action3", category="Objects/Large",
             description="Slam stopped by a block: object bounces back overhead, chest thrown back and tilted, "
                         "heavy stagger.")
    a.k(0.0, T(pitch=30, roll=4, y=-0.6, z=0.15), H(pitch=-22, roll=-3), RA(fwd=128, out=14), LA(fwd=128, out=14),
        RL(fwd=-40, out=14), LL(fwd=42, out=14), e="out")
    a.k(0.08, T(pitch=-20, roll=-8, turn=8, y=-0.35, z=-0.35), H(pitch=-26, roll=5), RA(fwd=204, out=24), LA(fwd=204, out=24),
        RL(fwd=-30, out=14), LL(fwd=14, out=14), e="io")
    a.k(0.34, T(pitch=-6, roll=-4, turn=4, y=-0.45, z=-0.55), H(pitch=-10, roll=2), RA(fwd=182, out=20), LA(fwd=182, out=20),
        RL(fwd=16, out=14), LL(fwd=-16, out=14), e="io")
    a.k(0.9, *L_HOLD)
    a.mark(0.0, "Blocked")
    a.props = [prop(LARGE_GRIP)]
    a.preview_panels = BIG_PANELS
    return a


L_BLOCK_STRONG = [T(pitch=18, turn=6, roll=-3, y=-0.5), H(pitch=-8, turn=-5, roll=2),
                  RA(fwd=92, out=20, yaw=-8), LA(fwd=92, out=20, yaw=-8),
                  RL(fwd=-30, out=14, twist=10), LL(fwd=26, out=12)]
L_BLOCK_WEAK = [T(pitch=8, turn=2, roll=-8, y=-0.82, z=-0.3), H(pitch=6, roll=5),
                RA(fwd=78, out=24, yaw=-6, z=-0.3), LA(fwd=78, out=24, yaw=-6, z=-0.3),
                RL(fwd=-44, out=18, twist=10), LL(fwd=30, out=16)]


def large_block(upper=False):
    return _block("LargeBlock_UB" if upper else "LargeBlock", "Large", L_HOLD, L_BLOCK_STRONG, L_BLOCK_WEAK,
                  LARGE_GRIP, period=0.13, upper=upper, panels=BIG_PANELS,
                  desc="Object braced in front as a wall with both arms, chest leaning into it.")


def large_block_break():
    a = Anim("LargeBlockBreak", 1.1, priority="Action3", category="Objects/Large",
             description="The weight crushes the guard: buckle down to a knee with the chest twisted under it, "
                         "shake, then heave it back up.")
    a.k(0.0, *L_BLOCK_WEAK, e="out")
    low = [T(pitch=30, roll=-10, turn=6, y=-1.35, z=-0.25), H(pitch=-8, roll=6), RA(fwd=52, out=32), LA(fwd=52, out=32),
           RL(fwd=-62, out=16), LL(fwd=60, out=12)]
    a.k(0.08, *low, e="io")
    strain(a, 0.16, 0.5, lambda t: low, 0.13, 2.4, 1.6)
    a.k(0.78, T(pitch=0, roll=-4, y=-0.4), H(pitch=-8, roll=2), RA(fwd=150, out=20), LA(fwd=150, out=20),
        RL(fwd=-20, out=16), LL(fwd=16, out=16), e="io")
    a.k(1.1, *L_HOLD)
    a.mark(0.04, "Break")
    a.props = [prop(LARGE_GRIP)]
    a.preview_panels = BIG_PANELS
    return a


# =============================================================================
# HUGE - trains / planes (2-3x character size)
# =============================================================================

HU_HOLD = [T(pitch=-3, roll=-3, y=-0.32), H(pitch=-6, roll=2), RA(fwd=176, out=28), LA(fwd=176, out=28),
           RL(fwd=-10, out=24, twist=10), LL(fwd=10, out=24, twist=10)]


def huge_pickup():
    a = Anim("HugePickup", 1.5, priority="Action2", category="Objects/Huge",
             description="Titan lift: squat under it, strain with the chest rocking, then explode it up overhead.")
    a.k(0.0, *RELAXED)
    low = [T(pitch=38, roll=4, y=-1.15), H(pitch=-30, roll=-3), RA(fwd=34, out=34, twist=-10), LA(fwd=34, out=34, twist=-10),
           RL(fwd=40, out=32), LL(fwd=-46, out=32)]
    rise = [T(pitch=28, roll=-4, y=-0.9), H(pitch=-28, roll=3), RA(fwd=36, out=34, twist=-10), LA(fwd=36, out=34, twist=-10),
            RL(fwd=34, out=32), LL(fwd=-40, out=32)]
    a.k(0.4, *low, e="io")
    strain(a, 0.48, 0.84, lambda t: blend(low, rise, (t - 0.48) / 0.36), 0.16, 1.5, 3.0)
    a.k(1.12, T(pitch=-14, roll=-5, y=0.02), H(pitch=-18, roll=3), RA(fwd=186, out=26), LA(fwd=186, out=26),
        RL(fwd=6, out=24), LL(fwd=-6, out=24), e="out")
    a.k(1.28, T(pitch=-4, roll=-6, y=-0.55), H(pitch=-4, roll=4), RA(fwd=172, out=30), LA(fwd=172, out=30),
        RL(fwd=-14, out=26), LL(fwd=14, out=26), e="io")
    a.k(1.5, *HU_HOLD)
    a.mark(0.44, "Grab")
    a.mark(0.84, "Lift")
    a.mark(1.26, "Settle")
    a.props = [prop(HUGE_GRIP, lift=(0.84, 1.14), ground_pos=(0, 0.05, -3.3))]
    a.preview_panels = [("front", None, 0, "body (object hidden)", {"frame": "char"}), ("back", None, 0, "behind")]
    a.preview_hold = 0.5
    return a


def huge_hold():
    a = Anim("HugeHold", 2.4, loop=True, priority="Action", category="Objects/Huge", default_ease="io",
             export_joints=("ra", "la"), upper_only=True,
             description="Train/plane balanced overhead, arms wide, slow heavy see-saw wobble. Arms only.")
    a.k(0.0, RA(fwd=176, out=28), LA(fwd=176, out=28))
    a.k(0.6, RA(fwd=178, out=32), LA(fwd=175, out=24))
    a.k(1.2, RA(fwd=176, out=28), LA(fwd=176, out=28))
    a.k(1.8, RA(fwd=175, out=24), LA(fwd=178, out=32))
    a.k(2.4, RA(fwd=176, out=28), LA(fwd=176, out=28))
    a.props = [prop(HUGE_GRIP)]
    a.preview_panels = BIG_UB_PANELS
    return a


def huge_throw():
    a = Anim("HugeThrow", 1.6, priority="Action2", category="Objects/Huge",
             description="Deep dip, a huge arch back, then a full-body launch with the chest folding down after it.")
    a.k(0.0, *HU_HOLD)
    a.k(0.5, T(pitch=-30, roll=-5, y=-0.85), H(pitch=-20, roll=3), RA(fwd=210, out=26), LA(fwd=210, out=26),
        RL(fwd=-30, out=20), LL(fwd=30, out=20), e="in3")
    a.k(0.64, T(pitch=10, roll=2, y=-0.4, z=0.2), H(pitch=-16), RA(fwd=160, out=24), LA(fwd=160, out=24),
        RL(fwd=-38, out=18), LL(fwd=40, out=18), e="lin")
    a.k(0.72, T(pitch=34, roll=5, y=-0.35, z=0.4), H(pitch=-22, roll=-3), RA(fwd=118, out=22), LA(fwd=118, out=22),
        RL(fwd=-42, out=18), LL(fwd=46, out=18), e="out")
    a.k(0.95, T(pitch=44, roll=6, y=-0.62, z=0.4), H(pitch=-24, roll=-4), RA(fwd=60, out=24), LA(fwd=60, out=24),
        RL(fwd=-42, out=18), LL(fwd=46, out=18), e="io")
    a.k(1.6, *RELAXED)
    a.mark(0.05, "Windup")
    a.mark(0.72, "Release")
    a.props = [prop(HUGE_GRIP, release=0.72, throw_vel=(0, 12, -30), spin=(-120, 0, 0), gravity=30)]
    a.preview_panels = BIG_PANELS
    return a


HU_SWEEP_R = [T(turn=72, pitch=8, roll=8, y=-0.55), H(turn=-58, pitch=-6, roll=-5), RA(fwd=96, out=6, yaw=22),
              LA(fwd=96, out=6, yaw=-22), RL(fwd=-22, out=26, twist=24), LL(fwd=30, out=22)]


def huge_swing():
    a = Anim("HugeSwing", 1.6, priority="Action2", category="Objects/Huge",
             description="Bring it down to chest height, coil the chest right, then sweep it through a wide "
                         "horizontal arc like a giant plank, rolling the body over the follow-through.")
    a.k(0.0, *HU_HOLD)
    a.k(0.42, *HU_SWEEP_R, e="in3")
    a.k(0.64, T(turn=-8, pitch=16, roll=-4, y=-0.62, z=0.2), H(turn=6, pitch=-10, roll=2), RA(fwd=92, out=4, yaw=0),
        LA(fwd=92, out=4, yaw=0), RL(fwd=-30, out=26, twist=20), LL(fwd=36, out=22, twist=-10), e="lin")
    a.k(0.8, T(turn=-74, pitch=12, roll=-12, y=-0.58, z=0.2), H(turn=52, pitch=-8, roll=7), RA(fwd=88, out=4, yaw=-22),
        LA(fwd=88, out=4, yaw=22), RL(fwd=-30, out=26, twist=30), LL(fwd=36, out=22, twist=-30), e="out")
    a.k(1.0, T(turn=-66, pitch=14, roll=-10, y=-0.5, z=0.2), H(turn=46, pitch=-8, roll=6), RA(fwd=80, out=6, yaw=-20),
        LA(fwd=80, out=6, yaw=20), RL(fwd=-30, out=26, twist=30), LL(fwd=36, out=22, twist=-30), e="io")
    a.k(1.6, *HU_HOLD)
    a.mark(0.46, "Swing")
    a.mark(0.64, "Hit")
    a.props = [prop(HUGE_GRIP)]
    a.preview_panels = [("front", None, 0, "body (object hidden)", {"frame": "char"}), ("top", None, 0, "from above")]
    return a


def huge_swing_blocked():
    a = Anim("HugeSwingBlocked", 1.1, priority="Action3", category="Objects/Huge",
             description="The sweep is stopped dead by a block; the recoil twists the chest back the other way "
                         "and you stagger.")
    a.k(0.0, T(turn=-8, pitch=16, roll=-4, y=-0.62, z=0.2), H(turn=6, pitch=-10, roll=2), RA(fwd=92, out=4),
        LA(fwd=92, out=4), RL(fwd=-30, out=26, twist=20), LL(fwd=36, out=22, twist=-10), e="out")
    a.k(0.1, T(turn=46, pitch=-8, roll=9, y=-0.5, z=-0.3), H(turn=-36, pitch=-18, roll=-6), RA(fwd=104, out=8, yaw=18),
        LA(fwd=104, out=8, yaw=-18), RL(fwd=-36, out=26), LL(fwd=12, out=22), e="io")
    a.k(0.4, T(turn=26, pitch=-2, roll=4, y=-0.62, z=-0.5), H(turn=-20, pitch=-6, roll=-3), RA(fwd=120, out=12, yaw=12),
        LA(fwd=120, out=12, yaw=-12), RL(fwd=16, out=26), LL(fwd=-20, out=22), e="io")
    a.k(1.1, *HU_HOLD)
    a.mark(0.0, "Blocked")
    a.props = [prop(HUGE_GRIP)]
    a.preview_panels = [("front", None, 0, "body (object hidden)", {"frame": "char"}), ("top", None, 0, "from above")]
    return a


HU_BLOCK_STRONG = [T(pitch=20, turn=5, roll=-3, y=-0.66), H(pitch=-10, turn=-4, roll=2),
                   RA(fwd=96, out=30, yaw=-6), LA(fwd=96, out=30, yaw=-6),
                   RL(fwd=-34, out=24, twist=10), LL(fwd=30, out=22)]
HU_BLOCK_WEAK = [T(pitch=4, turn=2, roll=-9, y=-1.0, z=-0.4), H(pitch=8, roll=6),
                 RA(fwd=84, out=34, z=-0.35), LA(fwd=84, out=34, z=-0.35),
                 RL(fwd=-48, out=28, twist=10), LL(fwd=34, out=26)]


def huge_block(upper=False):
    return _block("HugeBlock_UB" if upper else "HugeBlock", "Huge", HU_HOLD, HU_BLOCK_STRONG, HU_BLOCK_WEAK,
                  HUGE_GRIP, period=0.16, upper=upper, panels=BIG_PANELS,
                  desc="Vehicle held up in front like a wall, legs wide, chest driven into it.")


def huge_block_break():
    a = Anim("HugeBlockBreak", 1.4, priority="Action3", category="Objects/Huge",
             description="Crushed under the weight: driven down low with the chest twisted, shaking, then a "
                         "last-second heave back up.")
    a.k(0.0, *HU_BLOCK_WEAK, e="out")
    low = [T(pitch=34, roll=-11, turn=6, y=-1.45, z=-0.3), H(pitch=-6, roll=7), RA(fwd=44, out=38), LA(fwd=44, out=38),
           RL(fwd=-64, out=24), LL(fwd=62, out=20)]
    a.k(0.1, *low, e="io")
    strain(a, 0.2, 0.7, lambda t: low, 0.16, 3.0, 2.0)
    a.k(1.0, T(pitch=-6, roll=-4, y=-0.5), H(pitch=-12, roll=2), RA(fwd=160, out=28), LA(fwd=160, out=28),
        RL(fwd=-20, out=24), LL(fwd=18, out=24), e="io")
    a.k(1.4, *HU_HOLD)
    a.mark(0.05, "Break")
    a.props = [prop(HUGE_GRIP)]
    a.preview_panels = BIG_PANELS
    return a


# =============================================================================

def build() -> List[Anim]:
    out = []
    out += [small_pickup(), small_hold(), small_throw(), _ub_variant(small_throw, "SmallThrow_UB"),
            small_swing(), _ub_variant(small_swing, "SmallSwing_UB"), small_swing_blocked(),
            small_block(), small_block(True), small_block_break()]
    out += [medium_pickup(), medium_hold(), medium_throw(), _ub_variant(medium_throw, "MediumThrow_UB"),
            medium_swing(), _ub_variant(medium_swing, "MediumSwing_UB", fold=("turn", "pitch")), medium_swing_blocked(),
            medium_block(), medium_block(True), medium_block_break()]
    out += [large_pickup(), large_hold(), large_throw(),
            _ub_variant(large_throw, "LargeThrow_UB", fold=("turn", "pitch"), panels=BIG_UB_PANELS),
            large_swing(), _ub_variant(large_swing, "LargeSwing_UB", fold=("turn", "pitch"), panels=BIG_UB_PANELS),
            large_swing_blocked(), large_block(), large_block(True), large_block_break()]
    out += [huge_pickup(), huge_hold(), huge_throw(),
            _ub_variant(huge_throw, "HugeThrow_UB", fold=("turn", "pitch"), panels=BIG_UB_PANELS),
            huge_swing(), _ub_variant(huge_swing, "HugeSwing_UB", fold=("turn", "pitch"), panels=BIG_UB_PANELS),
            huge_swing_blocked(), huge_block(), huge_block(True), huge_block_break()]
    out += [_block_hit("Small", S_BLOCK_STRONG, SMALL_GRIP, 1.0, 0.4),
            _block_hit("Medium", M_BLOCK_STRONG, MEDIUM_GRIP, 1.3, 0.5),
            _block_hit("Large", L_BLOCK_STRONG, LARGE_GRIP, 1.6, 0.6, panels=BIG_PANELS),
            _block_hit("Huge", HU_BLOCK_STRONG, HUGE_GRIP, 1.8, 0.75, panels=BIG_PANELS)]
    return out
