"""Movement set - remade from the reference video (Ironpeak Movement System V6)
plus jump / landing / ledge pieces in the same style."""

from __future__ import annotations

from r6anim.core import Anim, PropSpec
from .common import (H, LA, LL, RA, RL, T, RELAXED, RUN_READY, add, blend, mirror, tremble, smoothstep,
                     wall_front, wall_side, ledge)

CAT = "Movement"


def idle():
    a = Anim("Idle", 2.4, loop=True, priority="Idle", default_ease="smooth", category=CAT,
             description="Relaxed breathing idle, arms hanging slightly away from the body like the video.")
    a.k(0.0, *RELAXED)
    a.k(1.2, T(pitch=3.6, y=-0.035), H(pitch=1.5, roll=1.5), RA(fwd=6.5, out=10, twist=5), LA(fwd=6.5, out=10.5, twist=5),
        RL(out=3, twist=5), LL(out=3, twist=5))
    a.close_loop()
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def walk():
    L = 0.8
    a = Anim("Walk", L, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Walk cycle (0.8 s). Play speed = WalkSpeed / 16.")
    contact = [T(pitch=4, turn=5, y=-0.06), H(pitch=-2, turn=-4), RA(fwd=-34, out=10, twist=4),
               LA(fwd=36, out=7, twist=4, yaw=-4), RL(fwd=30, out=2, twist=4), LL(fwd=-28, out=2, twist=4)]
    passing = [T(pitch=4, y=0.035, roll=2.5), H(pitch=-2, roll=-1.5), RA(fwd=-3, out=8), LA(fwd=5, out=8),
               RL(fwd=-3, out=2, twist=4), LL(fwd=6, out=4, twist=4)]
    a.k(0.0, *contact)
    a.k(L * 0.25, *passing)
    a.k(L * 0.5, *mirror(contact))
    a.k(L * 0.75, *mirror(passing))
    a.close_loop()
    a.mark(0.0, "Footstep")
    a.mark(L * 0.5, "Footstep")
    a.preview_panels = [("front", None, 5.2, ""), ("side", None, 5.2, "")]
    return a


SPRINT_L = 0.56


def sprint():
    L = SPRINT_L
    a = Anim("Sprint", L, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Big arm-pumping sprint with forward lean (0.56 s cycle). Back arm flares out like the video.")
    contact = [T(pitch=18, turn=9, y=-0.2, roll=-2), H(pitch=-15, turn=-7), RA(fwd=-58, out=30, twist=10),
               LA(fwd=74, out=9, yaw=-10, twist=-6), RL(fwd=47, out=2, twist=4), LL(fwd=-50, out=3, twist=6)]
    passing = [T(pitch=17, turn=0, y=0.06, roll=3), H(pitch=-14, roll=-2), RA(fwd=4, out=18),
               LA(fwd=10, out=17), RL(fwd=-12, out=2), LL(fwd=16, out=4)]
    a.k(0.0, *contact)
    a.k(L * 0.25, *passing)
    a.k(L * 0.5, *mirror(contact))
    a.k(L * 0.75, *mirror(passing))
    a.close_loop()
    a.mark(0.02, "Footstep")
    a.mark(L * 0.5 + 0.02, "Footstep")
    a.preview_panels = [("back", None, 9.5, "behind"), ("side", None, 9.5, "")]
    return a


CROUCH = [T(pitch=20, y=-0.85), H(pitch=-14), RA(fwd=26, out=13, twist=8), LA(fwd=22, out=15, twist=8),
          RL(fwd=50, out=24, twist=10), LL(fwd=-42, out=30, twist=12)]


def crouch_idle():
    a = Anim("CrouchIdle", 2.0, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Low crouch, head down, arms hanging forward (video crouch).")
    a.k(0.0, *CROUCH)
    a.k(1.0, *add(CROUCH, [T(pitch=2, y=-0.04), H(pitch=2), RA(fwd=3, out=2), LA(fwd=3, out=2)]))
    a.close_loop()
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def crouch_walk():
    L = 1.0
    a = Anim("CrouchWalk", L, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Crouched waddle (1.0 s cycle). Play speed = crouch WalkSpeed / 8.")
    contact = [T(pitch=21, y=-0.86, turn=6, roll=-2), H(pitch=-15, turn=-5), RA(fwd=6, out=16, twist=8),
               LA(fwd=36, out=12, twist=8), RL(fwd=50, out=22, twist=10), LL(fwd=-44, out=28, twist=12)]
    passing = [T(pitch=19, y=-0.62, roll=3), H(pitch=-14, roll=-2), RA(fwd=20, out=14), LA(fwd=22, out=14),
               RL(fwd=-8, out=34, twist=10), LL(fwd=14, out=36, twist=12)]
    a.k(0.0, *contact)
    a.k(L * 0.25, *passing)
    a.k(L * 0.5, *mirror(contact))
    a.k(L * 0.75, *mirror(passing))
    a.close_loop()
    a.mark(0.0, "Footstep")
    a.mark(L * 0.5, "Footstep")
    a.preview_panels = [("front", None, 2.2, ""), ("side", None, 2.2, "")]
    return a


JUMP_AIR = [T(pitch=-4, y=0.05), H(pitch=-8), RA(fwd=30, out=78, twist=10), LA(fwd=24, out=80, twist=10),
            RL(fwd=32, out=5), LL(fwd=-8, out=6)]
FALL_A = [T(pitch=-6, roll=-3), H(pitch=-12, roll=3), RA(fwd=40, out=128, twist=12), LA(fwd=14, out=96, twist=8),
          RL(fwd=26, out=8), LL(fwd=-20, out=12)]


def jump():
    a = Anim("Jump", 0.45, priority="Movement", category=CAT,
             description="Take-off: arms whip up and out, knee drives up. Holds into Fall.")
    a.k(0.0, T(pitch=10, y=-0.2), H(pitch=-4), RA(fwd=-24, out=26), LA(fwd=-22, out=26), RL(fwd=12, out=4), LL(fwd=-6, out=4), e="out")
    a.k(0.11, T(pitch=-7, y=0.12), H(pitch=-12), RA(fwd=64, out=56, twist=10), LA(fwd=48, out=62, twist=10),
        RL(fwd=44, out=4), LL(fwd=-16, out=5), e="io")
    a.k(0.45, *JUMP_AIR)
    a.mark(0.0, "Jump")
    a.fx = [(0.0, "dust", "feet")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def fall():
    a = Anim("Fall", 0.9, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Free-fall: arms raised up and out, legs paddling (video fall pose).")
    b = [T(pitch=-2, roll=3), H(pitch=-8, roll=-3), RA(fwd=14, out=96, twist=8), LA(fwd=40, out=128, twist=12),
         RL(fwd=-20, out=12), LL(fwd=26, out=8)]
    a.k(0.0, *FALL_A)
    a.k(0.45, *b)
    a.close_loop()
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def land():
    a = Anim("Land", 0.42, priority="Movement", category=CAT,
             description="Normal landing: quick knee-dip absorb, arms out for balance.")
    a.k(0.0, *JUMP_AIR, e="out")
    a.k(0.07, T(pitch=18, y=-0.55), H(pitch=-8), RA(fwd=26, out=40, twist=8), LA(fwd=20, out=42, twist=8),
        RL(fwd=34, out=12), LL(fwd=-30, out=12), e="io")
    a.k(0.2, T(pitch=10, y=-0.25), H(pitch=-5), RA(fwd=12, out=24), LA(fwd=10, out=24), RL(fwd=20, out=8), LL(fwd=-16, out=8))
    a.k(0.42, *RELAXED)
    a.mark(0.05, "Land")
    a.fx = [(0.05, "dust", "feet")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def land_heavy():
    a = Anim("LandHeavy", 1.0, priority="Action", category=CAT,
             description="Superhero landing from a big drop: fist to the floor, then rise.")
    low = [T(pitch=38, y=-1.42, turn=-6), H(pitch=-34, turn=6), RA(fwd=46, out=8, twist=10),
           LA(fwd=-34, out=56, twist=20), RL(fwd=72, out=10, twist=6), LL(fwd=-68, out=14, twist=10)]
    a.k(0.0, *FALL_A, e="out5")
    a.k(0.07, *low, e="io")
    a.k(0.42, *add(low, [T(y=0.05, pitch=-2), H(pitch=-2), LA(out=-4)]), e="io")
    a.k(0.7, T(pitch=12, y=-0.35), H(pitch=-8), RA(fwd=16, out=18), LA(fwd=-8, out=22), RL(fwd=24, out=6), LL(fwd=-22, out=8))
    a.k(1.0, *RELAXED)
    a.mark(0.07, "Impact")
    a.fx = [(0.07, "dust", "feet"), (0.07, "bighit", "pt:0.4,-2.9,-1.6")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def _roll_keys(a: Anim, t0: float, start_pose, end_arms_out=True):
    """Forward shoulder roll (torso rotates a full 360 degrees)."""
    a.world_legs = False
    a.k(t0, *start_pose)
    a.k(t0 + 0.09, T(pitch=55, y=-1.05, z=0.35, piv=-0.3), H(pitch=38), RA(fwd=118, out=22), LA(fwd=112, out=26),
        RL(fwd=40, out=6), LL(fwd=-28, out=6), e="lin")
    a.k(t0 + 0.19, T(pitch=125, y=-1.55, z=0.45, piv=0), H(pitch=45), RA(fwd=70, out=18), LA(fwd=66, out=20),
        RL(fwd=105, out=8), LL(fwd=92, out=10), e="lin")
    a.k(t0 + 0.30, T(pitch=215, y=-1.5, z=0.45, piv=0), H(pitch=45), RA(fwd=60, out=22), LA(fwd=58, out=24),
        RL(fwd=118, out=8), LL(fwd=108, out=10), e="lin")
    a.k(t0 + 0.41, T(pitch=295, y=-1.35, z=0.35, piv=0), H(pitch=30), RA(fwd=24, out=62 if end_arms_out else 30),
        LA(fwd=22, out=64 if end_arms_out else 30), RL(fwd=86, out=8), LL(fwd=60, out=10), e="lin")
    a.k(t0 + 0.52, T(pitch=348, y=-0.85, z=0.2, piv=-0.6), H(pitch=-6), RA(fwd=-6, out=58), LA(fwd=4, out=60),
        RL(fwd=44, out=6), LL(fwd=-14, out=8), e="io")


def roll():
    a = Anim("Roll", 0.78, priority="Action", category=CAT,
             description="Dodge / forward shoulder roll from the video (arms spread as you come up).")
    start = [T(pitch=14, y=-0.25), H(pitch=-8), RA(fwd=30, out=18), LA(fwd=26, out=20), RL(fwd=28, out=4), LL(fwd=-8, out=4)]
    _roll_keys(a, 0.0, start)
    a.k(0.78, T(pitch=372, y=-0.12, piv=-1), H(pitch=-10), RA(fwd=22, out=16), LA(fwd=-18, out=20), RL(fwd=24), LL(fwd=-6))
    a.mark(0.09, "Roll")
    a.mark(0.6, "Recover")
    a.fx = [(0.09, "dust", "feet")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def land_roll():
    a = Anim("LandRoll", 0.86, priority="Action", category=CAT,
             description="Landing from a high fall into a forward roll, then straight into a run (video).")
    a.k(0.0, *FALL_A, e="out")
    start = [T(pitch=16, y=-0.6), H(pitch=-4), RA(fwd=40, out=34), LA(fwd=36, out=36), RL(fwd=34, out=8), LL(fwd=-4, out=8)]
    a.k(0.06, *start)
    _roll_keys(a, 0.06, start)
    a.k(0.86, T(pitch=375, y=-0.15, piv=-1), H(pitch=-12), RA(fwd=-26, out=24), LA(fwd=34, out=12), RL(fwd=-20), LL(fwd=30))
    a.mark(0.05, "Land")
    a.mark(0.15, "Roll")
    a.fx = [(0.05, "dust", "feet")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


SLIDE = [T(pitch=-52, y=-1.5, roll=-7, turn=-10), H(pitch=40, turn=8, roll=4),
         RA(fwd=-60, out=50, twist=12), LA(fwd=-38, out=62, twist=8),
         RL(fwd=96, out=4, twist=6), LL(fwd=80, out=18, twist=-8)]


def slide_start():
    a = Anim("SlideStart", 0.26, priority="Action", category=CAT,
             description="Drop from a sprint into the feet-first slide. Chain into Slide (loop).")
    a.k(0.0, T(pitch=16, y=-0.15), H(pitch=-12), RA(fwd=-40, out=30), LA(fwd=55, out=10), RL(fwd=35), LL(fwd=-40), e="out")
    a.k(0.1, T(pitch=-18, y=-0.95, roll=-3), H(pitch=14), RA(fwd=-30, out=50), LA(fwd=30, out=52), RL(fwd=70, out=4), LL(fwd=40, out=12), e="out")
    a.k(0.26, *SLIDE)
    a.mark(0.08, "Slide")
    a.fx = [(0.12, "dust", "feet")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def slide_loop():
    a = Anim("Slide", 0.6, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Feet-first slide hold with a little ground shake (video slide pose).")
    a.k(0.0, *SLIDE)
    a.k(0.2, *add(SLIDE, [T(y=0.025, roll=1), H(pitch=-2, roll=-2), RA(out=3), LA(out=-3), RL(fwd=2)]))
    a.k(0.4, *add(SLIDE, [T(y=-0.01, roll=-1), H(pitch=1, roll=1), RA(out=-2), LA(out=2), LL(fwd=-2)]))
    a.close_loop()
    a.preview_panels = [("front", None, 14, ""), ("side", None, 14, "")]
    return a


def slide_end():
    a = Anim("SlideEnd", 0.4, priority="Action", category=CAT,
             description="Pop back up out of the slide into a run.")
    a.k(0.0, *SLIDE, e="out")
    a.k(0.16, T(pitch=4, y=-0.62), H(pitch=-4), RA(fwd=58, out=34), LA(fwd=40, out=36), RL(fwd=42, out=6), LL(fwd=-12, out=6))
    a.k(0.4, *RUN_READY)
    a.mark(0.12, "Stand")
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


HANG = [T(pitch=-4), H(pitch=-22), RA(fwd=160, out=12, twist=4), LA(fwd=160, out=12, twist=4), RL(fwd=6, out=4), LL(fwd=-4, out=6)]
LEDGE_TOP = 1.9
LEDGE_FACE = -0.62


def ledge_hang():
    a = Anim("LedgeHang", 1.6, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Hanging from a ledge by both hands, legs swaying.")
    a.k(0.0, *HANG)
    a.k(0.8, *add(HANG, [T(roll=2, pitch=-2), H(pitch=3), RA(fwd=-1, out=-1), LA(fwd=1, out=1), RL(fwd=-8), LL(fwd=8)]))
    a.close_loop()
    a.preview_ground = -12
    a.preview_scenery = ledge(LEDGE_FACE, LEDGE_TOP)
    a.preview_panels = [("back", None, 0, "behind"), ("side", None, 0, "")]
    return a


def ledge_climb():
    a = Anim("LedgeClimb", 0.75, priority="Action", category=CAT,
             description="Pull-up and mantle over a ledge; arms fly out wide at the top (video climb). "
                         "Tween the HumanoidRootPart up/forward ~0.05-0.5 s while it plays.")
    a.k(0.0, *HANG)
    a.k(0.12, T(pitch=24, y=0.25), H(pitch=-12), RA(fwd=128, out=16), LA(fwd=124, out=18), RL(fwd=42, out=4), LL(fwd=-12, out=6))
    a.k(0.25, T(pitch=40, y=0.15), H(pitch=-22), RA(fwd=24, out=22), LA(fwd=22, out=24), RL(fwd=96, out=6), LL(fwd=-22, out=8), e="out")
    a.k(0.4, T(pitch=20, y=0.05), H(pitch=-10), RA(fwd=34, out=86, twist=10), LA(fwd=26, out=82, twist=10), RL(fwd=40, out=4), LL(fwd=-52, out=6))
    a.k(0.56, T(pitch=13, y=-0.28), H(pitch=-10), RA(fwd=-22, out=40), LA(fwd=40, out=34), RL(fwd=-32), LL(fwd=40))
    a.k(0.75, *RUN_READY)
    a.mark(0.0, "Grab")
    a.mark(0.25, "Push")
    a.mark(0.55, "Land")
    a.preview_ground = -12
    a.preview_scenery = ledge(LEDGE_FACE, LEDGE_TOP)
    a.preview_root = lambda t: (0.0, (LEDGE_TOP + 3.0) * smoothstep((t - 0.04) / 0.38), -1.9 * smoothstep((t - 0.17) / 0.33))
    a.preview_panels = [("back", None, 0, "behind"), ("side", None, 0, "")]
    return a


def wall_climb():
    L = 0.48
    a = Anim("WallClimb", L, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Running straight up a wall: alternating high reaches and knee drives (video climb).")
    w0 = [T(pitch=8, turn=7, roll=-2), H(pitch=-24, turn=-5), RA(fwd=166, out=26, twist=6), LA(fwd=70, out=36, twist=6),
          RL(fwd=32, out=4), LL(fwd=-16, out=6)]
    a.k(0.0, *w0)
    a.k(L * 0.5, *mirror(w0))
    a.close_loop()
    a.mark(0.0, "Step")
    a.mark(L * 0.5, "Step")
    a.preview_ground = -40
    a.preview_scenery = wall_front(-1.1, -8, 8, -10, 10, scroll_v=-8.0)
    a.preview_panels = [("back_low", None, 0, "behind"), ("side", None, 0, "")]
    return a


def _wallrun(name: str, side: int):
    L = 0.5
    a = Anim(name, L, loop=True, priority="Movement", default_ease="smooth", category=CAT, world_legs=False,
             description=f"Wall run with the wall on the {'right' if side > 0 else 'left'}: body tilts away so "
                         "the feet press the wall, outer arm pumps wide (video wall run).")
    # authored for a wall on the right; mirrored for the left
    c = [T(roll=-24, pitch=14, turn=6, y=-0.15, x=-0.15), H(roll=20, pitch=-10, turn=-6),
         RA(fwd=-12, out=74, twist=10), LA(fwd=48, out=112, twist=-6), RL(fwd=44, out=6), LL(fwd=-44, out=6)]
    p = [T(roll=-22, pitch=13, y=0.0, x=-0.15), H(roll=19, pitch=-10), RA(fwd=6, out=70), LA(fwd=14, out=120),
         RL(fwd=-8, out=6), LL(fwd=14, out=6)]
    c2 = [T(roll=-24, pitch=14, turn=-6, y=-0.15, x=-0.15), H(roll=20, pitch=-10, turn=6),
          RA(fwd=24, out=72, twist=10), LA(fwd=-24, out=108, twist=-6), RL(fwd=-44, out=6), LL(fwd=44, out=6)]
    p2 = [T(roll=-22, pitch=13, y=0.0, x=-0.15), H(roll=19, pitch=-10), RA(fwd=6, out=70), LA(fwd=12, out=118),
          RL(fwd=14, out=6), LL(fwd=-8, out=6)]
    seq = [c, p, c2, p2]
    if side < 0:
        seq = [mirror(s) for s in seq]
    for i, s in enumerate(seq):
        a.k(L * i / 4, *s)
    a.close_loop()
    a.mark(0.0, "Step")
    a.mark(L * 0.5, "Step")
    a.preview_ground = -40
    a.preview_scenery = wall_side(side * 1.75, -14, 14, -9, 9, scroll_u=12.0)
    a.preview_panels = [("back_r" if side > 0 else "back", None, 0, "behind"), ("front_l" if side > 0 else "front", None, 0, "")]
    return a


def wall_jump():
    a = Anim("WallJump", 0.5, priority="Action", category=CAT,
             description="Tuck against the wall then explode off it (video wall kick).")
    a.k(0.0, T(pitch=-14, y=0.25), H(pitch=-12), RA(fwd=104, out=40), LA(fwd=98, out=44), RL(fwd=96, out=10), LL(fwd=82, out=14), e="io")
    a.k(0.08, T(pitch=-6, y=0.3), H(pitch=-6), RA(fwd=60, out=34), LA(fwd=56, out=36), RL(fwd=100, out=10), LL(fwd=90, out=12), e="out")
    a.k(0.2, T(pitch=-22, y=0.1), H(pitch=-16), RA(fwd=150, out=46), LA(fwd=140, out=50), RL(fwd=-14, out=6), LL(fwd=-30, out=8), e="io")
    a.k(0.5, *JUMP_AIR)
    a.mark(0.1, "Kick")
    a.preview_ground = -14
    a.preview_scenery = wall_front(-1.75, -7, 7, -14, 8)
    a.preview_root = lambda t: (0.0, 3.2 * smoothstep((t - 0.06) / 0.44) - 0.6 * smoothstep((t - 0.3) / 0.2), 2.6 * smoothstep((t - 0.07) / 0.43))
    a.preview_panels = [("back", None, 0, "behind"), ("side", None, 0, "")]
    return a


def vault():
    a = Anim("Vault", 0.62, priority="Action", category=CAT,
             description="Speed vault over a waist-high wall: left hand plants, legs swing through to the side "
                         "(video vault). Move the root up ~1.5 studs and forward while it plays.")
    a.k(0.0, *RUN_READY, e="io")
    a.k(0.1, T(pitch=30, turn=-10, roll=-6, y=0.1), H(pitch=-16, turn=8), RA(fwd=60, out=50, twist=10),
        LA(fwd=70, out=8, twist=-10), RL(fwd=70, out=6), LL(fwd=30, out=10), e="out")
    a.k(0.22, T(pitch=24, turn=-38, roll=-40, y=0.25), H(pitch=-14, turn=30, roll=26), RA(fwd=40, out=90, twist=14),
        LA(fwd=58, out=-4, twist=-10, yaw=-10), RL(fwd=86, out=40, yaw=40), LL(fwd=74, out=48, yaw=36), e="io")
    a.k(0.36, T(pitch=10, turn=-24, roll=-22, y=0.2), H(pitch=-10, turn=18, roll=12), RA(fwd=24, out=86, twist=10),
        LA(fwd=12, out=40), RL(fwd=40, out=26, yaw=20), LL(fwd=18, out=30, yaw=16), e="io")
    a.k(0.5, T(pitch=14, y=-0.3), H(pitch=-10), RA(fwd=-24, out=34), LA(fwd=40, out=30), RL(fwd=-20, out=6), LL(fwd=36, out=6))
    a.k(0.62, *RUN_READY)
    a.mark(0.1, "Plant")
    a.mark(0.48, "Land")
    a.preview_scenery = [("box", (0, -2.0, -1.3), (6.0, 2.0, 1.0), (128, 52, 58))]
    a.preview_root = lambda t: (0.0, 1.0 * smoothstep(t / 0.2) - 1.0 * smoothstep((t - 0.3) / 0.2), 3.0 - 6.0 * smoothstep(t / 0.55))
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def hit_react():
    a = Anim("HitReact", 0.5, priority="Action3", category="Hit Reactions",
             description="Light hit flinch from the video: arms jolt up and out, head snaps back.")
    a.k(0.0, *RELAXED, e="out")
    a.k(0.05, T(pitch=-12, y=-0.1, z=-0.18), H(pitch=-22, roll=8, turn=6), RA(fwd=22, out=56, twist=20),
        LA(fwd=16, out=50, twist=16), RL(fwd=12, out=4), LL(fwd=-22, out=5), e="io")
    a.k(0.17, T(pitch=-7, y=-0.12, z=-0.2), H(pitch=-11, roll=6), RA(fwd=16, out=45, twist=14), LA(fwd=12, out=42, twist=12),
        RL(fwd=10, out=4), LL(fwd=-18, out=5))
    a.k(0.5, *RELAXED)
    a.mark(0.0, "Hit")
    a.fx = [(0.0, "hit", "front")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def hit_heavy():
    a = Anim("HitHeavy", 0.9, priority="Action3", category="Hit Reactions",
             description="Heavy hit: knocked back, stumbling steps, hunched recovery.")
    a.k(0.0, *RELAXED, e="out")
    a.k(0.06, T(pitch=-30, y=-0.25, z=-0.4, roll=6), H(pitch=-32, roll=-6), RA(fwd=72, out=50, twist=20),
        LA(fwd=56, out=56, twist=20), RL(fwd=30, out=6), LL(fwd=-34, out=8), e="io")
    a.k(0.26, T(pitch=-14, y=-0.4, z=-0.6, roll=-4), H(pitch=-14, roll=4), RA(fwd=40, out=46), LA(fwd=28, out=40),
        RL(fwd=-28, out=8), LL(fwd=20, out=8), e="io")
    a.k(0.48, T(pitch=18, y=-0.42, z=-0.45), H(pitch=-6), RA(fwd=36, out=22, yaw=-8), LA(fwd=34, out=22, yaw=-8),
        RL(fwd=22, out=10), LL(fwd=-26, out=10), e="io")
    a.k(0.9, *RELAXED)
    a.mark(0.0, "Hit")
    a.mark(0.26, "Stumble")
    a.fx = [(0.0, "bighit", "front")]
    a.preview_panels = [("front", None, 0, ""), ("side", None, 0, "")]
    return a


def build():
    return [idle(), walk(), sprint(), crouch_idle(), crouch_walk(), jump(), fall(), land(), land_heavy(),
            land_roll(), roll(), slide_start(), slide_loop(), slide_end(), ledge_hang(), ledge_climb(),
            wall_climb(), _wallrun("WallRunRight", 1), _wallrun("WallRunLeft", -1), wall_jump(), vault(),
            hit_react(), hit_heavy()]
