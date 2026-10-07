"""
Object handling for four weight classes.

  Small   (rock, can, brick ...)        one hand, light and quick
  Medium  (crate, barrel, chair ...)    one hand, big dramatic wind-ups
  Large   (car, boulder, dumpster ...)  two hands overhead, heavy impacts
  Huge    (train car, plane, bus ...)   2-3x the character, titan-sized two-hand moves

Per class: Pickup, Hold (loop, upper body), Throw (+_UB), Swing (+_UB),
SwingBlocked, Block (+_UB, weakens over 4 s), BlockBreak.

Markers (use AnimationTrack:GetMarkerReachedSignal):
  Pickup:        Grab
  Throw:         Windup, Release
  Swing:         Swing (whoosh), Hit
  SwingBlocked:  Blocked
  Block:         Raised, Weakening, Critical, Exhausted
  BlockBreak:    Break
"""

from __future__ import annotations

import math
import zlib
from typing import List

from r6anim.core import Anim, PropSpec
from .common import (H, LA, LL, RA, RL, T, RELAXED, add, blend, smoothstep, tremble)

UB_PANELS = [("front", "Idle", 0, "over Idle"), ("side", "Sprint", 9.5, "over Sprint")]
FULL_PANELS = [("front", None, 0, ""), ("side", None, 0, "")]

# grip offsets (preview objects only)
SMALL_GRIP = dict(kind="small", mode="r", offset=(0, -0.36, -0.05))
MEDIUM_GRIP = dict(kind="medium", mode="r", offset=(0, -1.12, 0), rot=(0, 0, 0))
LARGE_GRIP = dict(kind="large", mode="both", align="arm", offset=(0, 1.28, 0), rot=(180, 0, 0))
HUGE_GRIP = dict(kind="huge", mode="both", align="arm", offset=(0, 1.86, 0), rot=(180, 0, 0))


def prop(base: dict, **kw) -> PropSpec:
    d = dict(base)
    d.update(kw)
    return PropSpec(**d)


def _ub_variant(src_builder, name: str, fold=("turn",), export=None):
    a = src_builder()
    a.name = name
    a.upper_only = True
    a.fold = fold
    if export:
        a.export_joints = export
    a.description = a.description.split(".")[0] + ". Upper-body only: plays over Walk/Sprint, legs keep running."
    a.preview_panels = UB_PANELS
    return a


def _block(name: str, size: str, start: list, strong: list, weak: list, grip: dict, amp=(0.6, 5.0),
           slow=1.0, upper=False, export=None, desc="", length=4.0):
    """Block that holds strong, then trembles and sags over `length` seconds.
    Scale its duration in-game with track:AdjustSpeed(4 / blockSeconds)."""
    a = Anim(name, length, priority="Action2", category=f"Objects/{size}", default_ease="smooth",
             description=desc or f"{size} object block that weakens over {length:.0f}s (AdjustSpeed to fit 3-5 s).")
    a.k(0.0, *start, e="out")
    a.k(0.16, *strong, e="smooth")
    step = 0.05
    t = 0.25
    seed = zlib.crc32(name.encode()) & 0xFFFF
    while t <= length + 1e-6:
        w = smoothstep((t - 0.55) / (length - 0.75)) ** 1.25
        pose = blend(strong, weak, min(1.0, w))
        amp_t = amp[0] + (amp[1] - amp[0]) * w ** 1.5
        tt = t * slow
        shake = [T(pitch=tremble(tt, seed + 1, amp_t * 0.35), roll=tremble(tt, seed + 2, amp_t * 0.25),
                   y=tremble(tt, seed + 3, amp_t * 0.006)),
                 H(pitch=tremble(tt, seed + 4, amp_t * 0.5), roll=tremble(tt, seed + 5, amp_t * 0.4)),
                 RA(fwd=tremble(tt, seed + 6, amp_t), out=tremble(tt, seed + 7, amp_t * 0.6)),
                 LA(fwd=tremble(tt, seed + 8, amp_t), out=tremble(tt, seed + 9, amp_t * 0.6))]
        a.k(round(t, 4), *add(pose, shake))
        t += step
    a.mark(0.16, "Raised")
    a.mark(round(length * 0.4, 2), "Weakening")
    a.mark(round(length * 0.78, 2), "Critical")
    a.mark(length, "Exhausted")
    a.props = [prop(grip)]
    a.preview_panels = FULL_PANELS
    a.preview_hold = 0.6
    if upper:
        a.upper_only = True
        a.export_joints = export
        a.description += " Upper-body only: plays over Walk/Sprint."
        a.preview_panels = UB_PANELS
    return a


# =============================================================================
# SMALL - one hand, light
# =============================================================================

S_ARM = dict(fwd=24, out=10, twist=-12)
S_HOLD_FULL = add(RELAXED, [RA(fwd=20, out=3, twist=-16)])


def small_pickup():
    a = Anim("SmallPickup", 0.55, priority="Action2", category="Objects/Small",
             description="Quick one-hand scoop of a small object.")
    a.k(0.0, *RELAXED)
    a.k(0.2, T(pitch=50, y=-0.5, turn=-10), H(pitch=-14, turn=8), RA(fwd=62, out=10, twist=-10),
        LA(fwd=18, out=24), RL(fwd=34, out=8), LL(fwd=-30, out=8), e="io")
    a.k(0.26, T(pitch=48, y=-0.48, turn=-10), H(pitch=-14, turn=8), RA(fwd=60, out=10, twist=-14),
        LA(fwd=18, out=24), RL(fwd=34, out=8), LL(fwd=-30, out=8), e="io")
    a.k(0.55, *S_HOLD_FULL)
    a.mark(0.22, "Grab")
    a.props = [prop(SMALL_GRIP, appear=0.22)]
    a.preview_panels = FULL_PANELS
    return a


def small_hold():
    a = Anim("SmallHold", 1.6, loop=True, priority="Action", category="Objects/Small", default_ease="smooth",
             export_joints=("ra",), upper_only=True,
             description="Carry a small object in the right hand. Only the right arm is animated, "
                         "so the other arm keeps swinging with Walk/Sprint.")
    a.k(0.0, RA(**S_ARM))
    a.k(0.8, RA(fwd=29, out=11, twist=-12))
    a.close_loop()
    a.props = [prop(SMALL_GRIP)]
    a.preview_panels = UB_PANELS
    return a


def small_throw():
    a = Anim("SmallThrow", 0.5, priority="Action2", category="Objects/Small",
             description="Light one-hand flick throw.")
    a.k(0.0, *S_HOLD_FULL)
    a.k(0.12, T(turn=24, pitch=-5, y=-0.05), H(turn=-18), RA(fwd=152, out=24, twist=20),
        LA(fwd=34, out=18, yaw=10), RL(fwd=-8, out=4), LL(fwd=14, out=4), e="in")
    a.k(0.2, T(turn=-18, pitch=11, y=-0.12, z=0.12), H(turn=12, pitch=-6), RA(fwd=74, out=6, yaw=-10, z=0.2),
        LA(fwd=-14, out=24), RL(fwd=-18, out=4, twist=14), LL(fwd=20, out=4), e="out")
    a.k(0.3, T(turn=-24, pitch=14, y=-0.14, z=0.12), H(turn=16, pitch=-6), RA(fwd=24, out=4, yaw=-36),
        LA(fwd=-20, out=26), RL(fwd=-18, out=4, twist=14), LL(fwd=20, out=4))
    a.k(0.5, *RELAXED)
    a.mark(0.02, "Windup")
    a.mark(0.2, "Release")
    a.props = [prop(SMALL_GRIP, release=0.2, throw_vel=(0, 7, -60), spin=(-900, 0, 0))]
    a.preview_panels = FULL_PANELS
    return a


def small_swing():
    a = Anim("SmallSwing", 0.45, priority="Action2", category="Objects/Small",
             description="Fast overhand smack with a small object.")
    a.k(0.0, *S_HOLD_FULL)
    a.k(0.1, T(turn=16, pitch=-5), H(turn=-10), RA(fwd=160, out=20, twist=10), LA(fwd=26, out=20), RL(fwd=-6), LL(fwd=8), e="in")
    a.k(0.18, T(turn=-14, pitch=14, y=-0.14, z=0.12), H(turn=8, pitch=-8), RA(fwd=48, out=6, yaw=-14, z=0.18),
        LA(fwd=-10, out=20), RL(fwd=-16, out=4, twist=10), LL(fwd=18, out=4), e="out")
    a.k(0.27, T(turn=-12, pitch=12, y=-0.12, z=0.1), H(turn=8, pitch=-6), RA(fwd=58, out=8, yaw=-12),
        LA(fwd=-8, out=20), RL(fwd=-16, out=4, twist=10), LL(fwd=18, out=4))
    a.k(0.45, *S_HOLD_FULL)
    a.mark(0.1, "Swing")
    a.mark(0.18, "Hit")
    a.props = [prop(SMALL_GRIP)]
    a.fx = [(0.18, "hit", "prop")]
    a.preview_panels = FULL_PANELS
    return a


def small_swing_blocked():
    a = Anim("SmallSwingBlocked", 0.5, priority="Action3", category="Objects/Small",
             description="Small-object hit bounces off a block: arm knocked back, half-step back.")
    a.k(0.0, T(turn=-14, pitch=14, y=-0.14, z=0.12), H(turn=8, pitch=-8), RA(fwd=48, out=6, yaw=-14, z=0.18),
        LA(fwd=-10, out=20), RL(fwd=-16, out=4, twist=10), LL(fwd=18, out=4), e="out")
    a.k(0.06, T(turn=20, pitch=-10, y=-0.12, z=-0.18), H(turn=-8, pitch=-16), RA(fwd=132, out=34, twist=20),
        LA(fwd=12, out=32), RL(fwd=-22, out=6), LL(fwd=8, out=6), e="io")
    a.k(0.2, T(turn=12, pitch=-4, y=-0.16, z=-0.22), H(pitch=-8), RA(fwd=104, out=28, twist=14), LA(fwd=10, out=28),
        RL(fwd=-18, out=6), LL(fwd=-2, out=6))
    a.k(0.5, *S_HOLD_FULL)
    a.mark(0.0, "Blocked")
    a.props = [prop(SMALL_GRIP)]
    a.fx = [(0.0, "block", "prop")]
    a.preview_panels = FULL_PANELS
    return a


S_BLOCK_STRONG = [T(pitch=10, y=-0.25, turn=8), H(pitch=6, turn=-6), RA(fwd=102, out=2, yaw=-42, twist=-26),
                  LA(fwd=74, out=8, yaw=-26, twist=-10), RL(fwd=-18, out=10, twist=12), LL(fwd=18, out=10)]
S_BLOCK_WEAK = [T(pitch=22, y=-0.46, turn=4), H(pitch=20, turn=-2), RA(fwd=76, out=8, yaw=-30, twist=-20),
                LA(fwd=50, out=14, yaw=-14), RL(fwd=-26, out=12, twist=12), LL(fwd=20, out=12)]


def small_block(upper=False):
    return _block("SmallBlock_UB" if upper else "SmallBlock", "Small", S_HOLD_FULL, S_BLOCK_STRONG, S_BLOCK_WEAK,
                  SMALL_GRIP, amp=(0.5, 4.5), upper=upper, export=("ra", "la", "head") if upper else None,
                  desc="Forearm guard with the small object across the face; trembles and sags over 4 s.")


def small_block_break():
    a = Anim("SmallBlockBreak", 0.72, priority="Action3", category="Objects/Small",
             description="Guard knocked wide open, stumble back.")
    a.k(0.0, *S_BLOCK_WEAK, e="out")
    a.k(0.06, T(pitch=-24, y=-0.15, z=-0.35, turn=12), H(pitch=-30, turn=-8), RA(fwd=146, out=52, twist=20),
        LA(fwd=112, out=60), RL(fwd=24, out=6), LL(fwd=-34, out=8), e="io")
    a.k(0.26, T(pitch=-10, y=-0.34, z=-0.55, turn=6), H(pitch=-12), RA(fwd=82, out=50), LA(fwd=70, out=55),
        RL(fwd=-20, out=8), LL(fwd=16, out=8), e="io")
    a.k(0.46, T(pitch=16, y=-0.34, z=-0.45), H(pitch=-4), RA(fwd=32, out=22), LA(fwd=26, out=24), RL(fwd=16, out=8), LL(fwd=-18, out=8))
    a.k(0.72, *S_HOLD_FULL)
    a.mark(0.03, "Break")
    a.props = [prop(SMALL_GRIP)]
    a.fx = [(0.03, "break", "hands")]
    a.preview_panels = FULL_PANELS
    return a


# =============================================================================
# MEDIUM - one hand, dramatic
# =============================================================================

M_HOLD_FULL = add(RELAXED, [RA(fwd=162, out=12, twist=0), T(roll=-3), H(roll=2)])


def medium_pickup():
    a = Anim("MediumPickup", 0.8, priority="Action2", category="Objects/Medium",
             description="Bend, grab the object one-handed and swing it up overhead.")
    a.k(0.0, *RELAXED)
    a.k(0.25, T(pitch=52, y=-0.62, turn=-10), H(pitch=-18, turn=8), RA(fwd=56, out=12, twist=-10),
        LA(fwd=30, out=26), RL(fwd=36, out=10), LL(fwd=-34, out=10), e="io")
    a.k(0.32, T(pitch=50, y=-0.6, turn=-10), H(pitch=-18, turn=8), RA(fwd=54, out=12, twist=-10),
        LA(fwd=30, out=26), RL(fwd=36, out=10), LL(fwd=-34, out=10), e="in")
    a.k(0.55, T(pitch=-8, y=0.05, turn=6, roll=-4), H(pitch=-10), RA(fwd=182, out=14), LA(fwd=-12, out=32),
        RL(fwd=4, out=4), LL(fwd=-4, out=4), e="out")
    a.k(0.8, *M_HOLD_FULL)
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
             description="Pitcher-style one-hand throw: knee lift, big stride, whip release.")
    a.k(0.0, *M_HOLD_FULL)
    a.k(0.28, T(turn=42, pitch=-14, y=0.04), H(turn=-36, pitch=-4), RA(fwd=206, out=22, twist=10),
        LA(fwd=86, out=26, yaw=24), RL(fwd=-4, out=4), LL(fwd=56, out=10), e="io")
    a.k(0.4, T(turn=10, pitch=6, y=-0.3), H(turn=-10, pitch=-8), RA(fwd=184, out=20), LA(fwd=60, out=30),
        RL(fwd=-34, out=6), LL(fwd=38, out=8), e="in")
    a.k(0.46, T(turn=-44, pitch=28, y=-0.4, z=0.25), H(turn=30, pitch=-18), RA(fwd=86, out=8, yaw=-6, z=0.3),
        LA(fwd=-34, out=40), RL(fwd=-40, out=8, twist=20), LL(fwd=36, out=8), e="out")
    a.k(0.6, T(turn=-52, pitch=36, y=-0.45, z=0.3), H(turn=34, pitch=-20), RA(fwd=30, out=6, yaw=-46),
        LA(fwd=-40, out=44), RL(fwd=-12, out=10), LL(fwd=36, out=8), e="io")
    a.k(0.86, *RELAXED)
    a.mark(0.05, "Windup")
    a.mark(0.46, "Release")
    a.props = [prop(MEDIUM_GRIP, release=0.46, throw_vel=(0, 11, -52), spin=(-720, 60, 0))]
    a.fx = [(0.4, "dust", "feet")]
    a.preview_panels = FULL_PANELS
    return a


def medium_swing():
    a = Anim("MediumSwing", 0.8, priority="Action2", category="Objects/Medium",
             description="One-handed overhead smash with the object.")
    a.k(0.0, *M_HOLD_FULL)
    a.k(0.24, T(pitch=-16, turn=18, y=0.08), H(pitch=-8, turn=-12), RA(fwd=212, out=20), LA(fwd=40, out=36, yaw=10),
        RL(fwd=-10, out=4), LL(fwd=30, out=6), e="in")
    a.k(0.36, T(pitch=36, turn=-12, y=-0.55, z=0.2), H(pitch=-22, turn=8), RA(fwd=80, out=8, yaw=-6, z=0.2),
        LA(fwd=-24, out=36), RL(fwd=-38, out=8), LL(fwd=42, out=8), e="out")
    a.k(0.48, T(pitch=30, turn=-10, y=-0.5, z=0.18), H(pitch=-18, turn=6), RA(fwd=92, out=8, yaw=-6),
        LA(fwd=-20, out=34), RL(fwd=-38, out=8), LL(fwd=42, out=8), e="io")
    a.k(0.8, *M_HOLD_FULL)
    a.mark(0.27, "Swing")
    a.mark(0.36, "Hit")
    a.props = [prop(MEDIUM_GRIP)]
    a.fx = [(0.36, "bighit", "prop"), (0.36, "dust", "propground")]
    a.preview_panels = FULL_PANELS
    return a


def medium_swing_blocked():
    a = Anim("MediumSwingBlocked", 0.66, priority="Action3", category="Objects/Medium",
             description="Medium smash slams into a block and rebounds overhead; stagger back.")
    a.k(0.0, T(pitch=26, turn=-10, y=-0.4, z=0.15), H(pitch=-18, turn=8), RA(fwd=104, out=8, yaw=-6),
        LA(fwd=-20, out=34), RL(fwd=-36, out=8), LL(fwd=40, out=8), e="out")
    a.k(0.07, T(pitch=-14, turn=20, y=-0.22, z=-0.3), H(pitch=-24, turn=-6), RA(fwd=200, out=34, twist=10),
        LA(fwd=22, out=42), RL(fwd=-30, out=8), LL(fwd=10, out=8), e="io")
    a.k(0.26, T(pitch=-4, turn=8, y=-0.3, z=-0.45), H(pitch=-10), RA(fwd=178, out=24), LA(fwd=12, out=36),
        RL(fwd=18, out=8), LL(fwd=-14, out=8))
    a.k(0.66, *M_HOLD_FULL)
    a.mark(0.0, "Blocked")
    a.props = [prop(MEDIUM_GRIP)]
    a.fx = [(0.0, "block", "prop")]
    a.preview_panels = FULL_PANELS
    return a


M_BLOCK_STRONG = [T(pitch=12, y=-0.3, turn=6), H(pitch=4, turn=-4), RA(fwd=96, out=4, yaw=-26, twist=-4),
                  LA(fwd=86, out=6, yaw=-34, twist=-6), RL(fwd=-22, out=12, twist=12), LL(fwd=22, out=10)]
M_BLOCK_WEAK = [T(pitch=24, y=-0.56, turn=2), H(pitch=16), RA(fwd=72, out=8, yaw=-18, z=-0.15),
                LA(fwd=64, out=10, yaw=-24, z=-0.15), RL(fwd=-34, out=14, twist=12), LL(fwd=24, out=12)]


def medium_block(upper=False):
    return _block("MediumBlock_UB" if upper else "MediumBlock", "Medium", M_HOLD_FULL, M_BLOCK_STRONG, M_BLOCK_WEAK,
                  MEDIUM_GRIP, amp=(0.6, 5.0), upper=upper, export=("ra", "la", "head") if upper else None,
                  desc="Object held out front as a shield, off-hand bracing; trembles, sags and gets pushed back over 4 s.")


def medium_block_break():
    a = Anim("MediumBlockBreak", 0.86, priority="Action3", category="Objects/Medium",
             description="Shield-object knocked up and away, big stumble back.")
    a.k(0.0, *M_BLOCK_WEAK, e="out")
    a.k(0.07, T(pitch=-28, y=-0.2, z=-0.45, turn=14), H(pitch=-32, turn=-10), RA(fwd=196, out=40, twist=10),
        LA(fwd=122, out=62), RL(fwd=28, out=8), LL(fwd=-38, out=8), e="io")
    a.k(0.3, T(pitch=-12, y=-0.42, z=-0.7, turn=6), H(pitch=-12), RA(fwd=168, out=30), LA(fwd=74, out=56),
        RL(fwd=-24, out=8), LL(fwd=18, out=8), e="io")
    a.k(0.52, T(pitch=16, y=-0.4, z=-0.55), H(pitch=-6), RA(fwd=150, out=18), LA(fwd=30, out=26), RL(fwd=16, out=8), LL(fwd=-20, out=8))
    a.k(0.86, *M_HOLD_FULL)
    a.mark(0.03, "Break")
    a.props = [prop(MEDIUM_GRIP)]
    a.fx = [(0.03, "break", "prop")]
    a.preview_panels = FULL_PANELS
    return a


# =============================================================================
# LARGE - two hands overhead, heavy
# =============================================================================

L_BRACE = [RL(fwd=-8, out=16, twist=8), LL(fwd=8, out=16, twist=8)]
L_HOLD_FULL = [T(pitch=-2, y=-0.18), H(pitch=-4), RA(fwd=174, out=18), LA(fwd=174, out=18)] + L_BRACE


def large_pickup():
    a = Anim("LargePickup", 1.1, priority="Action2", category="Objects/Large",
             description="Deep squat, grip underneath, explosive two-hand lift to overhead.")
    a.k(0.0, *RELAXED)
    a.k(0.34, T(pitch=34, y=-1.0), H(pitch=-26), RA(fwd=36, out=24, twist=-10), LA(fwd=36, out=24, twist=-10),
        RL(fwd=46, out=24), LL(fwd=-48, out=26), e="io")
    a.k(0.44, T(pitch=30, y=-0.98), H(pitch=-24), RA(fwd=34, out=24, twist=-10), LA(fwd=34, out=24, twist=-10),
        RL(fwd=46, out=24), LL(fwd=-48, out=26), e="in")
    a.k(0.72, T(pitch=-12, y=0.06), H(pitch=-16), RA(fwd=186, out=16), LA(fwd=186, out=16),
        RL(fwd=6, out=16), LL(fwd=-6, out=16), e="out")
    a.k(0.88, T(pitch=-4, y=-0.32), H(pitch=-6), RA(fwd=172, out=19), LA(fwd=172, out=19),
        RL(fwd=-8, out=18), LL(fwd=8, out=18), e="io")
    a.k(1.1, *L_HOLD_FULL)
    a.mark(0.4, "Grab")
    a.mark(0.86, "Settle")
    a.props = [prop(LARGE_GRIP, offset=(0, 1.32, 0), lift=(0.44, 0.74), ground_pos=(0, 0, -2.9), rest_rot=(0, 0, 0))]
    a.fx = [(0.88, "dust", "feet")]
    a.preview_panels = FULL_PANELS
    return a


def large_hold():
    a = Anim("LargeHold", 2.0, loop=True, priority="Action", category="Objects/Large", default_ease="smooth",
             export_joints=("ra", "la"), upper_only=True,
             description="Large object held overhead with both arms, straining. Arms only, so legs/torso come "
                         "from Idle/Walk/Sprint.")
    for i in range(0, 21):
        t = i * 0.1
        a.k(round(t, 3), RA(fwd=174 + 2.5 * math.sin(t * math.pi) + tremble(t, 11, 0.8), out=18 + tremble(t, 12, 0.6)),
            LA(fwd=174 + 2.5 * math.sin(t * math.pi) + tremble(t, 13, 0.8), out=18 + tremble(t, 14, 0.6)))
    a.k(2.0, RA(fwd=174 + tremble(0, 11, 0.8), out=18 + tremble(0, 12, 0.6)),
        LA(fwd=174 + tremble(0, 13, 0.8), out=18 + tremble(0, 14, 0.6)))
    a.props = [prop(LARGE_GRIP)]
    a.preview_panels = UB_PANELS
    return a


def large_throw():
    a = Anim("LargeThrow", 1.1, priority="Action2", category="Objects/Large",
             description="Two-hand overhead heave: arch back, step and launch with full-body follow-through.")
    a.k(0.0, *L_HOLD_FULL)
    a.k(0.38, T(pitch=-26, y=-0.46), H(pitch=-18), RA(fwd=212, out=18), LA(fwd=212, out=18),
        RL(fwd=-26, out=12), LL(fwd=28, out=12), e="in3")
    a.k(0.5, T(pitch=24, y=-0.26, z=0.2), H(pitch=-16), RA(fwd=132, out=14), LA(fwd=132, out=14),
        RL(fwd=-36, out=12), LL(fwd=40, out=12), e="lin")
    a.k(0.55, T(pitch=36, y=-0.3, z=0.35), H(pitch=-20), RA(fwd=108, out=12), LA(fwd=108, out=12),
        RL(fwd=-38, out=12), LL(fwd=42, out=12), e="out")
    a.k(0.72, T(pitch=42, y=-0.5, z=0.35), H(pitch=-22), RA(fwd=56, out=16), LA(fwd=56, out=16),
        RL(fwd=-36, out=12), LL(fwd=42, out=12), e="io")
    a.k(1.1, *RELAXED)
    a.mark(0.05, "Windup")
    a.mark(0.55, "Release")
    a.props = [prop(LARGE_GRIP, release=0.55, throw_vel=(0, 13, -40), spin=(-260, 0, 0))]
    a.fx = [(0.55, "dust", "feet")]
    a.preview_panels = FULL_PANELS
    return a


def large_swing():
    a = Anim("LargeSwing", 1.0, priority="Action2", category="Objects/Large",
             description="Two-handed overhead slam: rise, arch back, crash it into the ground.")
    a.k(0.0, *L_HOLD_FULL)
    a.k(0.34, T(pitch=-24, y=0.1), H(pitch=-14), RA(fwd=210, out=16), LA(fwd=210, out=16),
        RL(fwd=-12, out=12), LL(fwd=24, out=12), e="in3")
    a.k(0.5, T(pitch=46, y=-0.95, z=0.2), H(pitch=-30), RA(fwd=96, out=14), LA(fwd=96, out=14),
        RL(fwd=-44, out=16), LL(fwd=48, out=16), e="out")
    a.k(0.64, T(pitch=43, y=-0.9, z=0.2), H(pitch=-26), RA(fwd=100, out=14), LA(fwd=100, out=14),
        RL(fwd=-44, out=16), LL(fwd=48, out=16), e="io")
    a.k(1.0, *L_HOLD_FULL)
    a.mark(0.36, "Swing")
    a.mark(0.5, "Hit")
    a.props = [prop(LARGE_GRIP)]
    a.fx = [(0.5, "bighit", "propground"), (0.5, "dust", "propground")]
    a.preview_panels = FULL_PANELS
    return a


def large_swing_blocked():
    a = Anim("LargeSwingBlocked", 0.9, priority="Action3", category="Objects/Large",
             description="Slam stopped by a block: object bounces back overhead, heavy stagger.")
    a.k(0.0, T(pitch=30, y=-0.6, z=0.15), H(pitch=-22), RA(fwd=128, out=14), LA(fwd=128, out=14),
        RL(fwd=-40, out=14), LL(fwd=42, out=14), e="out")
    a.k(0.08, T(pitch=-20, y=-0.35, z=-0.35), H(pitch=-26), RA(fwd=204, out=24), LA(fwd=204, out=24),
        RL(fwd=-30, out=14), LL(fwd=14, out=14), e="io")
    a.k(0.34, T(pitch=-6, y=-0.45, z=-0.55), H(pitch=-10), RA(fwd=182, out=20), LA(fwd=182, out=20),
        RL(fwd=16, out=14), LL(fwd=-16, out=14), e="io")
    a.k(0.9, *L_HOLD_FULL)
    a.mark(0.0, "Blocked")
    a.props = [prop(LARGE_GRIP)]
    a.fx = [(0.0, "block", "prop")]
    a.preview_panels = FULL_PANELS
    return a


L_BLOCK_STRONG = [T(pitch=18, y=-0.5), H(pitch=-8), RA(fwd=92, out=20, yaw=-8), LA(fwd=92, out=20, yaw=-8),
                  RL(fwd=-30, out=14, twist=10), LL(fwd=26, out=12)]
L_BLOCK_WEAK = [T(pitch=8, y=-0.82, z=-0.3), H(pitch=6), RA(fwd=78, out=24, yaw=-6, z=-0.3), LA(fwd=78, out=24, yaw=-6, z=-0.3),
                RL(fwd=-44, out=18, twist=10), LL(fwd=30, out=16)]


def large_block(upper=False):
    return _block("LargeBlock_UB" if upper else "LargeBlock", "Large", L_HOLD_FULL, L_BLOCK_STRONG, L_BLOCK_WEAK,
                  dict(LARGE_GRIP, offset=(0, 1.0, 0)), amp=(0.7, 5.5), slow=0.8, upper=upper,
                  export=("ra", "la", "head") if upper else None,
                  desc="Object braced in front as a wall with both arms; pushed back, buckling and shaking over 4 s.")


def large_block_break():
    a = Anim("LargeBlockBreak", 1.1, priority="Action3", category="Objects/Large",
             description="The weight crushes the guard: buckle down to a knee, then heave back up.")
    a.k(0.0, *L_BLOCK_WEAK, e="out")
    a.k(0.08, T(pitch=30, y=-1.35, z=-0.25), H(pitch=-8), RA(fwd=52, out=32), LA(fwd=52, out=32),
        RL(fwd=-62, out=16), LL(fwd=60, out=12), e="io")
    for i, t in enumerate((0.16, 0.24, 0.32, 0.4, 0.48)):
        a.k(t, T(pitch=30 + tremble(t, 21, 2), y=-1.35 + tremble(t, 22, 0.03), z=-0.25), H(pitch=-8 + tremble(t, 23, 3)),
            RA(fwd=52 + tremble(t, 24, 4), out=32), LA(fwd=52 + tremble(t, 25, 4), out=32), RL(fwd=-62, out=16), LL(fwd=60, out=12))
    a.k(0.78, T(pitch=0, y=-0.4), H(pitch=-8), RA(fwd=150, out=20), LA(fwd=150, out=20), RL(fwd=-20, out=16), LL(fwd=16, out=16), e="io")
    a.k(1.1, *L_HOLD_FULL)
    a.mark(0.04, "Break")
    a.props = [prop(LARGE_GRIP, offset=(0, 1.0, 0))]
    a.fx = [(0.04, "break", "prop"), (0.08, "dust", "feet")]
    a.preview_panels = FULL_PANELS
    return a


# =============================================================================
# HUGE - trains / planes (2-3x character size)
# =============================================================================

HU_BRACE = [RL(fwd=-10, out=24, twist=10), LL(fwd=10, out=24, twist=10)]
HU_HOLD_FULL = [T(pitch=-3, y=-0.32), H(pitch=-6), RA(fwd=176, out=28), LA(fwd=176, out=28)] + HU_BRACE


def huge_pickup():
    a = Anim("HugePickup", 1.5, priority="Action2", category="Objects/Huge",
             description="Titan lift: squat under it, strain, then explode it up overhead.")
    a.k(0.0, *RELAXED)
    a.k(0.4, T(pitch=38, y=-1.15), H(pitch=-30), RA(fwd=34, out=34, twist=-10), LA(fwd=34, out=34, twist=-10),
        RL(fwd=40, out=32), LL(fwd=-46, out=32), e="io")
    for t in (0.5, 0.58, 0.66, 0.74, 0.82):
        k = (t - 0.5) / 0.32
        a.k(t, T(pitch=38 - 10 * k + tremble(t, 31, 1.5), y=-1.15 + 0.25 * k + tremble(t, 32, 0.02)),
            H(pitch=-30 + tremble(t, 33, 3)), RA(fwd=34 + tremble(t, 34, 3), out=34), LA(fwd=34 + tremble(t, 35, 3), out=34),
            RL(fwd=40 - 6 * k, out=32), LL(fwd=-46 + 6 * k, out=32))
    a.k(1.12, T(pitch=-14, y=0.02), H(pitch=-18), RA(fwd=186, out=26), LA(fwd=186, out=26),
        RL(fwd=6, out=24), LL(fwd=-6, out=24), e="out")
    a.k(1.28, T(pitch=-4, y=-0.55), H(pitch=-4), RA(fwd=172, out=30), LA(fwd=172, out=30),
        RL(fwd=-14, out=26), LL(fwd=14, out=26), e="io")
    a.k(1.5, *HU_HOLD_FULL)
    a.mark(0.44, "Grab")
    a.mark(0.84, "Lift")
    a.mark(1.26, "Settle")
    a.props = [prop(HUGE_GRIP, lift=(0.82, 1.14), ground_pos=(0, 0.05, -3.3), rest_rot=(0, 0, 0))]
    a.fx = [(1.26, "dust", "feet")]
    a.preview_panels = [("back", None, 0, "behind"), ("side", None, 0, "")]
    a.preview_hold = 0.5
    return a


def huge_hold():
    a = Anim("HugeHold", 2.4, loop=True, priority="Action", category="Objects/Huge", default_ease="smooth",
             export_joints=("ra", "la"), upper_only=True,
             description="Train/plane balanced overhead, arms wide, slow heavy wobble. Arms only.")
    for i in range(0, 25):
        t = i * 0.1
        sw = math.sin(t * 2 * math.pi / 2.4)
        a.k(round(t, 3), RA(fwd=176 + 2 * sw + tremble(t, 41, 1.0), out=28 + 2.5 * sw + tremble(t, 42, 0.8)),
            LA(fwd=176 + 2 * sw + tremble(t, 43, 1.0), out=28 - 2.5 * sw + tremble(t, 44, 0.8)))
    a.k(2.4, RA(fwd=176 + tremble(0, 41, 1.0), out=28 + tremble(0, 42, 0.8)),
        LA(fwd=176 + tremble(0, 43, 1.0), out=28 + tremble(0, 44, 0.8)))
    a.props = [prop(HUGE_GRIP)]
    a.preview_panels = UB_PANELS
    return a


def huge_throw():
    a = Anim("HugeThrow", 1.6, priority="Action2", category="Objects/Huge",
             description="Deep dip, arch and full-body launch of a vehicle-sized object.")
    a.k(0.0, *HU_HOLD_FULL)
    a.k(0.5, T(pitch=-30, y=-0.85), H(pitch=-20), RA(fwd=210, out=26), LA(fwd=210, out=26),
        RL(fwd=-30, out=20), LL(fwd=30, out=20), e="in3")
    a.k(0.64, T(pitch=10, y=-0.4, z=0.2), H(pitch=-16), RA(fwd=160, out=24), LA(fwd=160, out=24),
        RL(fwd=-38, out=18), LL(fwd=40, out=18), e="lin")
    a.k(0.72, T(pitch=34, y=-0.35, z=0.4), H(pitch=-22), RA(fwd=118, out=22), LA(fwd=118, out=22),
        RL(fwd=-42, out=18), LL(fwd=46, out=18), e="out")
    a.k(0.95, T(pitch=44, y=-0.62, z=0.4), H(pitch=-24), RA(fwd=60, out=24), LA(fwd=60, out=24),
        RL(fwd=-42, out=18), LL(fwd=46, out=18), e="io")
    a.k(1.6, *RELAXED)
    a.mark(0.05, "Windup")
    a.mark(0.72, "Release")
    a.props = [prop(HUGE_GRIP, release=0.72, throw_vel=(0, 12, -30), spin=(-120, 0, 0), gravity=30)]
    a.fx = [(0.72, "dust", "feet")]
    a.preview_panels = FULL_PANELS
    a.preview_zoom = 1.0
    return a


def huge_swing():
    a = Anim("HugeSwing", 1.7, priority="Action2", category="Objects/Huge",
             description="Grab it by one end and sweep it like a giant bat (wide horizontal arc).")
    a.k(0.0, *HU_HOLD_FULL)
    a.k(0.45, T(turn=70, pitch=10, y=-0.55), H(turn=-58, pitch=-6), RA(fwd=90, out=0, yaw=50), LA(fwd=90, out=0, yaw=-50),
        RL(fwd=-20, out=26, twist=20), LL(fwd=30, out=22), e="in3")
    a.k(0.68, T(turn=-10, pitch=16, y=-0.62, z=0.2), H(turn=6, pitch=-10), RA(fwd=94, out=0, yaw=6), LA(fwd=94, out=0, yaw=-6),
        RL(fwd=-30, out=26, twist=20), LL(fwd=36, out=22, twist=-10), e="lin")
    a.k(0.82, T(turn=-72, pitch=12, y=-0.58, z=0.2), H(turn=50, pitch=-8), RA(fwd=88, out=0, yaw=-44), LA(fwd=88, out=0, yaw=44),
        RL(fwd=-30, out=26, twist=30), LL(fwd=36, out=22, twist=-30), e="out")
    a.k(1.02, T(turn=-62, pitch=14, y=-0.5, z=0.2), H(turn=44, pitch=-8), RA(fwd=70, out=4, yaw=-40), LA(fwd=70, out=4, yaw=40),
        RL(fwd=-30, out=26, twist=30), LL(fwd=36, out=22, twist=-30), e="io")
    a.k(1.7, *HU_HOLD_FULL)
    a.mark(0.5, "Swing")
    a.mark(0.68, "Hit")
    a.props = [prop(HUGE_GRIP, keys=[(0.0, (0, 1.86, 0), (180, 0, 0)), (0.42, (0, 6.6, 0), (180, 0, 90)),
                                     (1.1, (0, 6.6, 0), (180, 0, 90)), (1.6, (0, 1.86, 0), (180, 0, 0))])]
    a.fx = [(0.68, "bighit", "pt:0,0,-8"), (0.45, "dust", "feet")]
    a.preview_panels = [("front", None, 0, ""), ("top", None, 0, "")]
    return a


def huge_swing_blocked():
    a = Anim("HugeSwingBlocked", 1.1, priority="Action3", category="Objects/Huge",
             description="The sweep is stopped dead by a block; the recoil spins you back and you stagger.")
    a.k(0.0, T(turn=-10, pitch=16, y=-0.62, z=0.2), H(turn=6, pitch=-10), RA(fwd=94, out=0, yaw=6), LA(fwd=94, out=0, yaw=-6),
        RL(fwd=-30, out=26, twist=20), LL(fwd=36, out=22, twist=-10), e="out")
    a.k(0.1, T(turn=46, pitch=-8, y=-0.5, z=-0.3), H(turn=-36, pitch=-18), RA(fwd=104, out=6, yaw=40), LA(fwd=104, out=6, yaw=-40),
        RL(fwd=-36, out=26), LL(fwd=12, out=22), e="io")
    a.k(0.4, T(turn=26, pitch=-2, y=-0.62, z=-0.5), H(turn=-20, pitch=-6), RA(fwd=120, out=12, yaw=26), LA(fwd=120, out=12, yaw=-26),
        RL(fwd=16, out=26), LL(fwd=-20, out=22), e="io")
    a.k(1.1, *HU_HOLD_FULL)
    a.mark(0.0, "Blocked")
    a.props = [prop(HUGE_GRIP, keys=[(0.0, (0, 6.6, 0), (180, 0, 90)), (0.5, (0, 6.6, 0), (180, 0, 90)),
                                     (1.0, (0, 1.86, 0), (180, 0, 0))])]
    a.fx = [(0.0, "block", "pt:0,0,-8")]
    a.preview_panels = [("front", None, 0, ""), ("top", None, 0, "")]
    return a


HU_BLOCK_STRONG = [T(pitch=20, y=-0.66), H(pitch=-10), RA(fwd=96, out=30, yaw=-6), LA(fwd=96, out=30, yaw=-6),
                   RL(fwd=-34, out=24, twist=10), LL(fwd=30, out=22)]
HU_BLOCK_WEAK = [T(pitch=4, y=-1.0, z=-0.4), H(pitch=8), RA(fwd=84, out=34, z=-0.35), LA(fwd=84, out=34, z=-0.35),
                 RL(fwd=-48, out=28, twist=10), LL(fwd=34, out=26)]


def huge_block(upper=False):
    return _block("HugeBlock_UB" if upper else "HugeBlock", "Huge", HU_HOLD_FULL, HU_BLOCK_STRONG, HU_BLOCK_WEAK,
                  dict(HUGE_GRIP, align="torso", offset=(0, 0.2, -2.3), rot=(0, 0, 0)), amp=(0.8, 6.0), slow=0.7,
                  upper=upper, export=("ra", "la", "head") if upper else None,
                  desc="Vehicle held up in front like a wall, legs wide; driven back and buckling over 4 s.")


def huge_block_break():
    a = Anim("HugeBlockBreak", 1.4, priority="Action3", category="Objects/Huge",
             description="Crushed under the weight: driven down low, shaking, then a last-second heave back up.")
    a.k(0.0, *HU_BLOCK_WEAK, e="out")
    a.k(0.1, T(pitch=34, y=-1.45, z=-0.3), H(pitch=-6), RA(fwd=44, out=38), LA(fwd=44, out=38),
        RL(fwd=-64, out=24), LL(fwd=62, out=20), e="io")
    for t in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
        a.k(t, T(pitch=34 + tremble(t, 51, 2.5), y=-1.45 + tremble(t, 52, 0.04), z=-0.3), H(pitch=-6 + tremble(t, 53, 4)),
            RA(fwd=44 + tremble(t, 54, 5), out=38), LA(fwd=44 + tremble(t, 55, 5), out=38), RL(fwd=-64, out=24), LL(fwd=62, out=20))
    a.k(1.0, T(pitch=-6, y=-0.5), H(pitch=-12), RA(fwd=160, out=28), LA(fwd=160, out=28), RL(fwd=-20, out=24), LL(fwd=18, out=24), e="io")
    a.k(1.4, *HU_HOLD_FULL)
    a.mark(0.05, "Break")
    a.props = [prop(HUGE_GRIP, keys=[(0.0, (0, 0.2, -2.3), (0, 0, 0)), (0.7, (0, 0.2, -2.3), (0, 0, 0)),
                                     (1.0, (0, 1.86, 0), (180, 0, 0))], align="arm")]
    a.fx = [(0.05, "break", "hands"), (0.1, "dust", "feet")]
    a.preview_panels = FULL_PANELS
    return a


# =============================================================================

def build() -> List[Anim]:
    out = []
    # small
    out += [small_pickup(), small_hold(), small_throw(), _ub_variant(small_throw, "SmallThrow_UB"),
            small_swing(), _ub_variant(small_swing, "SmallSwing_UB"), small_swing_blocked(),
            small_block(), small_block(True), small_block_break()]
    # medium
    out += [medium_pickup(), medium_hold(), medium_throw(), _ub_variant(medium_throw, "MediumThrow_UB"),
            medium_swing(), _ub_variant(medium_swing, "MediumSwing_UB", fold=("turn", "pitch")), medium_swing_blocked(),
            medium_block(), medium_block(True), medium_block_break()]
    # large
    out += [large_pickup(), large_hold(), large_throw(), _ub_variant(large_throw, "LargeThrow_UB", fold=("turn", "pitch")),
            large_swing(), _ub_variant(large_swing, "LargeSwing_UB", fold=("turn", "pitch")), large_swing_blocked(),
            large_block(), large_block(True), large_block_break()]
    # huge
    out += [huge_pickup(), huge_hold(), huge_throw(), _ub_variant(huge_throw, "HugeThrow_UB", fold=("turn", "pitch")),
            huge_swing(), _ub_variant(huge_swing, "HugeSwing_UB", fold=("turn", "pitch")), huge_swing_blocked(),
            huge_block(), huge_block(True), huge_block_break()]
    return out
