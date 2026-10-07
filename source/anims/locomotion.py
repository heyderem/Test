"""Movement set.

Remade from the two reference videos (V1 = Ironpeak Movement System V6,
V2 = Movement System showcase; see reference/NOTES.md for timestamps), plus
jump / landing / ledge pieces in the same style.

Style rules taken from the videos:
  * arms never hang straight - they flare out from the body, and in the air
    they spread wide like wings
  * the torso leads and leans, the head counter-rotates to stay level
  * contacts and swings snap in 2-3 frames, then the pose holds and drifts
  * silhouettes read from a chase camera: limbs spread sideways, not hidden
"""

from __future__ import annotations

from r6anim.core import Anim
from r6anim.secondary import Overlap
from .common import (H, LA, LL, RA, RL, T, RELAXED, add, blend, cyc, ledge, mirror, smoothstep,
                     wall_front, wall_side)

CAT = "Movement"
TUMBLE = Overlap(drag=0.08, head=0.1, bounce=4, settle=0.3)   # for flips/rolls (torso spins)
FRONT_SIDE = [("front", None, 0, ""), ("side", None, 0, "")]

# moment of the sprint just after a footfall - actions that end in a run end here
RUN_READY = [T(pitch=24, turn=0, y=0.0), H(pitch=-19), RA(fwd=8, out=25, twist=6), LA(fwd=20, out=24, twist=4),
             RL(fwd=6, out=2, twist=4), LL(fwd=-10, out=3, twist=6)]
# arms spread like wings (every airborne moment in V1)
WINGS = [T(pitch=-3, y=0.05), H(pitch=-10), RA(fwd=16, out=88, twist=8), LA(fwd=8, out=92, twist=8),
         RL(fwd=34, out=6), LL(fwd=-22, out=8)]
FALL_A = [T(pitch=-5, roll=-3), H(pitch=-10, roll=3), RA(fwd=14, out=102, twist=10), LA(fwd=4, out=86, twist=6),
          RL(fwd=26, out=10), LL(fwd=-16, out=12)]
FALL_B = [T(pitch=-3, roll=3), H(pitch=-8, roll=-3), RA(fwd=4, out=88, twist=6), LA(fwd=14, out=102, twist=10),
          RL(fwd=-14, out=12), LL(fwd=24, out=10)]


# =============================================================================
# idle / walk / sprint
# =============================================================================

def idle():
    a = Anim("Idle", 2.4, loop=True, priority="Idle", default_ease="smooth", category=CAT,
             description="Relaxed breathing idle: arms hang a little away from the body (V1 38.5 s, V2 0.0 s).")
    a.k(0.0, *RELAXED)
    a.k(1.2, T(pitch=3.4, y=-0.035), H(pitch=1.2, roll=1.2), RA(fwd=6, out=9.5, twist=5), LA(fwd=6, out=10, twist=5),
        RL(out=3, twist=5), LL(out=3, twist=5))
    a.close_loop()
    a.preview_panels = FRONT_SIDE
    return a


def walk():
    L = 1.0
    a = Anim("Walk", L, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Walk cycle matched to V2 (30-frame cycle): arms swing with a slight outward flare, "
                         "small shoulder counter-twist. AdjustSpeed(speed / 16).")
    contact = [T(pitch=3, turn=5, y=-0.06), H(pitch=-2, turn=-4), RA(fwd=-30, out=5, twist=4),
               LA(fwd=32, out=4, yaw=-3, twist=4), RL(fwd=30, out=2, twist=4), LL(fwd=-38, out=2, twist=4)]
    passing = [T(pitch=3, y=0.04, roll=2), H(pitch=-2, roll=-1.5), RA(fwd=-2, out=4, twist=3), LA(fwd=5, out=4, twist=3),
               RL(fwd=-10, out=2, twist=4), LL(fwd=16, out=3, twist=4)]
    a.k(0.0, *contact)
    a.k(L * 0.25, *passing)
    a.k(L * 0.5, *mirror(contact))
    a.k(L * 0.75, *mirror(passing))
    a.close_loop()
    a.mark(0.0, "Footstep")
    a.mark(L * 0.5, "Footstep")
    a.preview_panels = [("back", None, 5.2, "behind"), ("side", None, 5.2, "")]
    return a


SPRINT_L = 17 / 30   # 17 frames, measured from V1 19.55 s


def sprint():
    """Matched to V1: each arm holds at the back (flared out) or the front for
    ~7 frames and snaps across in 2-3; the back leg kicks up high."""
    L = SPRINT_L
    a = Anim("Sprint", L, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Ironpeak-style sprint: arms hold back/front and snap across, back arm flared wide, "
                         "high back-kick (17-frame cycle). AdjustSpeed(speed / 26).")
    arm = [(0.00, dict(fwd=-34, out=21, twist=12)),
           (0.33, dict(fwd=-28, out=23, twist=12)),
           (0.41, dict(fwd=16, out=24, twist=4)),
           (0.48, dict(fwd=64, out=27, yaw=-4, twist=-4)),
           (0.84, dict(fwd=58, out=29, yaw=-4, twist=-4)),
           (0.92, dict(fwd=6, out=25, twist=6))]
    cyc(a, RA, arm)
    cyc(a, LA, arm, shift=0.5)
    leg = [(0.00, dict(fwd=42, out=2, twist=4)),
           (0.18, dict(fwd=4, out=2, twist=4)),
           (0.34, dict(fwd=-36, out=3, twist=6)),
           (0.50, dict(fwd=-64, out=5, twist=8)),
           (0.72, dict(fwd=8, out=4, twist=4)),
           (0.88, dict(fwd=50, out=3, twist=4))]
    cyc(a, RL, leg)
    cyc(a, LL, leg, shift=0.5)
    # torso: measured from V2 18.2 s - the shoulder line tilts about +-15 degrees on screen each
    # stride (dropping on the side of the arm that swings forward), with a 12 degree shoulder twist
    # and a small sideways shift over the planted foot
    cyc(a, T, [(0.04, dict(pitch=26, turn=12, roll=-20, x=0.1, y=-0.12)),
               (0.29, dict(pitch=24, turn=0, roll=0, x=0.0, y=0.03)),
               (0.54, dict(pitch=26, turn=-12, roll=20, x=-0.1, y=-0.12)),
               (0.79, dict(pitch=24, turn=0, roll=0, x=0.0, y=0.03))])
    cyc(a, H, [(0.04, dict(pitch=-21, turn=-8, roll=13)),
               (0.29, dict(pitch=-19, turn=0, roll=0)),
               (0.54, dict(pitch=-21, turn=8, roll=-13)),
               (0.79, dict(pitch=-19, turn=0, roll=0))])
    a.mark(0.0, "Footstep")
    a.mark(round(L * 0.5, 4), "Footstep")
    a.preview_panels = [("back", None, 9.5, "behind"), ("side", None, 9.5, "")]
    return a


# =============================================================================
# crouch
# =============================================================================

CROUCH = [T(pitch=12, y=-0.62), H(pitch=-10), RA(fwd=16, out=12, twist=8), LA(fwd=12, out=13, twist=8),
          RL(fwd=50, out=8, twist=8), LL(fwd=-36, out=10, twist=10)]


def crouch_idle():
    a = Anim("CrouchIdle", 2.0, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Low crouch, one leg forward, arms hanging forward and out (V1 31.3 s).")
    a.k(0.0, *CROUCH)
    a.k(1.0, *add(CROUCH, [T(pitch=2, y=-0.04), H(pitch=2), RA(fwd=3, out=2), LA(fwd=3, out=2)]))
    a.close_loop()
    a.preview_panels = FRONT_SIDE
    return a


def crouch_walk():
    L = 1.0
    a = Anim("CrouchWalk", L, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Crouched sneak (V2 21.2 s, V1 27.5 s): low, legs splayed, arms hanging out to the sides "
                         "and swaying (1.0 s cycle). AdjustSpeed(speed / 8).")
    contact = [T(pitch=12, y=-0.66, turn=6, roll=-2), H(pitch=-10, turn=-5), RA(fwd=-6, out=13, twist=8),
               LA(fwd=26, out=11, twist=8), RL(fwd=50, out=6, twist=8), LL(fwd=-40, out=8, twist=10)]
    passing = [T(pitch=11, y=-0.56, roll=3), H(pitch=-9, roll=-2), RA(fwd=8, out=12), LA(fwd=12, out=12),
               RL(fwd=-26, out=7, twist=8), LL(fwd=30, out=8, twist=10)]
    a.k(0.0, *contact)
    a.k(L * 0.25, *passing)
    a.k(L * 0.5, *mirror(contact))
    a.k(L * 0.75, *mirror(passing))
    a.close_loop()
    a.mark(0.0, "Footstep")
    a.mark(L * 0.5, "Footstep")
    a.preview_panels = [("front", None, 2.2, ""), ("back", None, 2.2, "behind")]
    return a


# =============================================================================
# air
# =============================================================================

def jump():
    a = Anim("Jump", 0.4, priority="Movement", category=CAT, grounded=False,
             description="Take-off: dip, then the arms whip up and spread like wings while a knee drives up "
                         "(V1 5.2 s). Holds into Fall.")
    a.k(0.0, T(pitch=12, y=-0.3), H(pitch=-6), RA(fwd=-28, out=26), LA(fwd=-24, out=26), RL(fwd=18, out=4),
        LL(fwd=-8, out=4), e="out")
    a.k(0.1, T(pitch=-6, y=0.12), H(pitch=-12), RA(fwd=52, out=66, twist=10), LA(fwd=40, out=72, twist=10),
        RL(fwd=46, out=4), LL(fwd=-20, out=5), e="io")
    a.k(0.4, *WINGS)
    a.mark(0.0, "Jump")
    a.preview_panels = FRONT_SIDE
    return a


def fall():
    a = Anim("Fall", 0.9, loop=True, priority="Movement", default_ease="smooth", category=CAT, grounded=False,
             description="Free-fall: arms straight out to the sides with a slow flap, legs paddling (V1 10.0 s).")
    a.k(0.0, *FALL_A)
    a.k(0.45, *FALL_B)
    a.close_loop()
    a.preview_panels = FRONT_SIDE
    return a


def land():
    a = Anim("Land", 0.42, priority="Movement", category=CAT,
             description="Normal landing: quick knee-dip absorb, arms dropping from wings to balance.")
    a.k(0.0, *FALL_A, e="out")
    a.k(0.07, T(pitch=20, y=-0.6), H(pitch=-8), RA(fwd=24, out=48, twist=8), LA(fwd=18, out=50, twist=8),
        RL(fwd=34, out=12), LL(fwd=-30, out=12), e="io")
    a.k(0.2, T(pitch=10, y=-0.25), H(pitch=-5), RA(fwd=12, out=24), LA(fwd=10, out=24), RL(fwd=20, out=8), LL(fwd=-16, out=8))
    a.k(0.42, *RELAXED)
    a.mark(0.05, "Land")
    a.preview_panels = FRONT_SIDE
    return a


def land_heavy():
    a = Anim("LandHeavy", 1.0, priority="Action", category=CAT,
             description="Superhero landing from a big drop: fist to the floor, wings arm out, then rise.")
    low = [T(pitch=38, y=-1.42, turn=-6), H(pitch=-34, turn=6), RA(fwd=48, out=8, twist=10),
           LA(fwd=-30, out=60, twist=20), RL(fwd=72, out=10, twist=6), LL(fwd=-68, out=14, twist=10)]
    a.k(0.0, *FALL_A, e="out5")
    a.k(0.07, *low, e="io")
    a.k(0.42, *add(low, [T(y=0.05, pitch=-2), H(pitch=-2), LA(out=-4)]), e="io")
    a.k(0.7, T(pitch=12, y=-0.35), H(pitch=-8), RA(fwd=16, out=18), LA(fwd=-8, out=22), RL(fwd=24, out=6), LL(fwd=-22, out=8))
    a.k(1.0, *RELAXED)
    a.mark(0.07, "Impact")
    a.preview_panels = FRONT_SIDE
    return a


# =============================================================================
# rolls (V1 11.0, 22.0, 48.5, 52.0 s): dive, go over the head with the arms
# spread wide, come up running
# =============================================================================

def _roll_keys(a: Anim, t0: float, start_pose, k: float = 1.0):
    """Dive onto the hands, pass through an inverted moment with the legs up
    and fairly straight (V1 48.5 s / 52.0 s), arms spread wide coming over,
    tuck and come up on one knee."""
    a.world_legs = False
    a.grounded = False
    a.overlap = TUMBLE
    a.k(t0, *start_pose)
    a.k(t0 + 0.07 * k, T(pitch=70, y=-0.55, z=0.4, piv=-0.4), H(pitch=24), RA(fwd=128, out=34, twist=10),
        LA(fwd=124, out=36, twist=10), RL(fwd=-14, out=4), LL(fwd=6, out=6), e="lin")
    a.k(t0 + 0.16 * k, T(pitch=148, y=-1.05, z=0.55, piv=0), H(pitch=40), RA(fwd=70, out=76, twist=10),
        LA(fwd=66, out=78, twist=10), RL(fwd=18, out=6), LL(fwd=30, out=8), e="lin")
    a.k(t0 + 0.26 * k, T(pitch=196, y=-0.95, z=0.5, piv=0), H(pitch=42), RA(fwd=40, out=88), LA(fwd=38, out=90),
        RL(fwd=34, out=8), LL(fwd=44, out=10), e="lin")
    a.k(t0 + 0.35 * k, T(pitch=252, y=-1.3, z=0.4, piv=0), H(pitch=36), RA(fwd=24, out=90), LA(fwd=22, out=92),
        RL(fwd=86, out=8), LL(fwd=94, out=10), e="lin")
    a.k(t0 + 0.43 * k, T(pitch=308, y=-1.15, z=0.3, piv=0), H(pitch=20), RA(fwd=10, out=82), LA(fwd=8, out=84),
        RL(fwd=100, out=8), LL(fwd=70, out=10), e="lin")
    a.k(t0 + 0.51 * k, T(pitch=350, y=-0.7, z=0.15, piv=-0.6), H(pitch=-10), RA(fwd=-6, out=60), LA(fwd=10, out=62),
        RL(fwd=52, out=6), LL(fwd=-12, out=8), e="io")


def roll():
    a = Anim("Roll", 0.76, priority="Action", category=CAT,
             description="Dodge roll from a run: dive, over the head with the arms spread wide, up running "
                         "(V1 22.0 s, 52.0 s).")
    start = [T(pitch=22, y=-0.2), H(pitch=-14), RA(fwd=36, out=30), LA(fwd=20, out=32), RL(fwd=28, out=4), LL(fwd=-12, out=4)]
    a.k(0.0, *RUN_READY)
    _roll_keys(a, 0.04, start, k=1.12)
    a.k(0.76, T(pitch=384, y=0.0, piv=-1), *RUN_READY[1:])
    a.mark(0.12, "Roll")
    a.mark(0.6, "Recover")
    a.preview_panels = FRONT_SIDE
    return a


def land_roll():
    a = Anim("LandRoll", 0.82, priority="Action", category=CAT,
             description="Landing from a high fall straight into a forward roll, up into a run (V1 11.0 s).")
    a.k(0.0, *FALL_A, e="out")
    start = [T(pitch=16, y=-0.62), H(pitch=-4), RA(fwd=44, out=40), LA(fwd=38, out=42), RL(fwd=36, out=8), LL(fwd=-4, out=8)]
    a.k(0.06, *start)
    _roll_keys(a, 0.06, start)
    a.k(0.82, T(pitch=384, y=0.0, piv=-1), *RUN_READY[1:])
    a.mark(0.05, "Land")
    a.mark(0.13, "Roll")
    a.preview_panels = FRONT_SIDE
    return a


# =============================================================================
# slide (V1 0.4 s and 15.8 s): feet first, leaning back, arms spread flat
# =============================================================================

SLIDE = [T(pitch=-56, y=-1.3, roll=-5, turn=-8), H(pitch=44, turn=6, roll=3),
         RA(fwd=-34, out=68, twist=10), LA(fwd=-26, out=64, twist=10),
         RL(fwd=96, out=4, twist=6), LL(fwd=80, out=16, twist=-8)]


def slide_start():
    a = Anim("SlideStart", 0.22, priority="Action", category=CAT,
             description="Drop from a sprint into the slide (3 frames to the floor like the video). Chain into Slide.")
    a.k(0.0, *RUN_READY, e="out")
    a.k(0.09, T(pitch=-16, y=-0.95, roll=-3), H(pitch=16), RA(fwd=-10, out=62), LA(fwd=6, out=60),
        RL(fwd=70, out=4), LL(fwd=44, out=12), e="out")
    a.k(0.22, *SLIDE)
    a.mark(0.08, "Slide")
    a.preview_panels = FRONT_SIDE
    return a


def slide_loop():
    a = Anim("Slide", 0.6, loop=True, priority="Movement", default_ease="smooth", category=CAT,
             description="Feet-first slide hold, arms spread out flat to the sides, small ground judder.")
    a.k(0.0, *SLIDE)
    a.k(0.2, *add(SLIDE, [T(y=0.025, roll=1), H(pitch=-2, roll=-2), RA(out=3), LA(out=-3), RL(fwd=2)]))
    a.k(0.4, *add(SLIDE, [T(y=-0.01, roll=-1), H(pitch=1, roll=1), RA(out=-2), LA(out=2), LL(fwd=-2)]))
    a.close_loop()
    a.preview_panels = [("back", None, 14, "behind"), ("side", None, 14, "")]
    return a


def slide_end():
    a = Anim("SlideEnd", 0.4, priority="Action", category=CAT,
             description="Pop back up out of the slide straight into a run (V1 0.9 s).")
    a.k(0.0, *SLIDE, e="out")
    a.k(0.16, T(pitch=6, y=-0.66), H(pitch=-4), RA(fwd=46, out=50), LA(fwd=30, out=52), RL(fwd=46, out=6),
        LL(fwd=-14, out=6))
    a.k(0.4, *RUN_READY)
    a.mark(0.12, "Stand")
    a.preview_panels = FRONT_SIDE
    return a


# =============================================================================
# ledges and walls
# =============================================================================

HANG = [T(pitch=-4), H(pitch=-22), RA(fwd=160, out=12, twist=4), LA(fwd=160, out=12, twist=4),
        RL(fwd=6, out=4), LL(fwd=-4, out=6)]
LEDGE_TOP = 1.9
LEDGE_FACE = -0.62


def ledge_hang():
    a = Anim("LedgeHang", 1.6, loop=True, priority="Movement", default_ease="smooth", category=CAT, grounded=False,
             description="Hanging from a ledge by both hands, legs swaying.")
    a.k(0.0, *HANG)
    a.k(0.8, *add(HANG, [T(roll=2, pitch=-2), H(pitch=3), RA(fwd=-1, out=-1), LA(fwd=1, out=1), RL(fwd=-8), LL(fwd=8)]))
    a.close_loop()
    a.preview_ground = -12
    a.preview_scenery = ledge(LEDGE_FACE, LEDGE_TOP)
    a.preview_panels = [("back", None, 0, "behind"), ("side", None, 0, "")]
    return a


def ledge_climb():
    a = Anim("LedgeClimb", 0.7, priority="Action", category=CAT, grounded=False,
             description="Mantle over a ledge: pull, pitch forward over the edge with the arms flung wide, "
                         "knees tucked, land running (V1 2.6 s, 14.1 s, 15.3 s). Move the root up/forward "
                         "during 0.04-0.45 s.")
    a.k(0.0, *HANG)
    a.k(0.1, T(pitch=18, y=0.2), H(pitch=-14), RA(fwd=112, out=24), LA(fwd=108, out=26), RL(fwd=40, out=4),
        LL(fwd=-10, out=6), e="in")
    a.k(0.22, T(pitch=42, y=0.15), H(pitch=-28), RA(fwd=46, out=78, twist=10), LA(fwd=40, out=82, twist=10),
        RL(fwd=92, out=6), LL(fwd=84, out=8), e="out")
    a.k(0.36, T(pitch=26, y=0.05), H(pitch=-16), RA(fwd=24, out=86, twist=10), LA(fwd=20, out=84, twist=10),
        RL(fwd=50, out=4), LL(fwd=-30, out=6))
    a.k(0.5, T(pitch=20, y=-0.3), H(pitch=-14), RA(fwd=-24, out=40), LA(fwd=40, out=34), RL(fwd=-30), LL(fwd=40))
    a.k(0.7, *RUN_READY)
    a.mark(0.0, "Grab")
    a.mark(0.2, "Push")
    a.mark(0.5, "Land")
    a.preview_ground = -12
    a.preview_scenery = ledge(LEDGE_FACE, LEDGE_TOP)
    a.preview_root = lambda t: (0.0, (LEDGE_TOP + 3.0) * smoothstep((t - 0.04) / 0.36), -1.9 * smoothstep((t - 0.15) / 0.32))
    a.preview_panels = [("back", None, 0, "behind"), ("side", None, 0, "")]
    return a


def wall_climb():
    L = 0.48
    a = Anim("WallClimb", L, loop=True, priority="Movement", default_ease="smooth", category=CAT, grounded=False,
             description="Running straight up a wall: arms reach up and out in turn, knees drive (V1 2.2 s, 13.5 s).")
    w0 = [T(pitch=6, turn=6, roll=-2), H(pitch=-26, turn=-5), RA(fwd=150, out=40, twist=6), LA(fwd=50, out=46, twist=6),
          RL(fwd=34, out=4), LL(fwd=-14, out=6)]
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
             grounded=False,
             description=f"Wall run with the wall on the {'right' if side > 0 else 'left'}: body tilts off the "
                         "wall, both arms flared out and pumping, legs running (V1 4.8 s, 7.5 s).")
    c = [T(roll=-20, pitch=12, turn=6, y=-0.15, x=-0.15), H(roll=17, pitch=-10, turn=-6),
         RA(fwd=-24, out=58, twist=10), LA(fwd=46, out=66, twist=-6), RL(fwd=44, out=6), LL(fwd=-44, out=6)]
    p = [T(roll=-18, pitch=11, y=0.0, x=-0.15), H(roll=16, pitch=-10), RA(fwd=10, out=56), LA(fwd=12, out=64),
         RL(fwd=-8, out=6), LL(fwd=14, out=6)]
    c2 = [T(roll=-20, pitch=12, turn=-6, y=-0.15, x=-0.15), H(roll=17, pitch=-10, turn=6),
          RA(fwd=40, out=56, twist=10), LA(fwd=-26, out=70, twist=-6), RL(fwd=-44, out=6), LL(fwd=44, out=6)]
    p2 = [T(roll=-18, pitch=11, y=0.0, x=-0.15), H(roll=16, pitch=-10), RA(fwd=8, out=56), LA(fwd=12, out=66),
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


def _wallrun_enter(name: str, side: int):
    a = Anim(name, 0.32, priority="Action", category=CAT, grounded=False,
             description=f"Tucked spin onto the wall ({'right' if side > 0 else 'left'}), straight into the wall run "
                         "(V1 4.5 s and 7.05 s).")
    a.overlap = TUMBLE
    s = side
    a.k(0.0, *WINGS, e="out")
    a.k(0.06, T(pitch=18, roll=-14 * s, turn=-70 * s, y=0.1), H(pitch=10), RA(fwd=70, out=16), LA(fwd=70, out=16),
        RL(fwd=104, out=6), LL(fwd=96, out=8), e="lin")
    a.k(0.16, T(pitch=22, roll=-26 * s, turn=-210 * s, y=0.1), H(pitch=14), RA(fwd=66, out=12), LA(fwd=66, out=12),
        RL(fwd=110, out=6), LL(fwd=104, out=8), e="lin")
    a.k(0.25, T(pitch=14, roll=-22 * s, turn=-330 * s, y=0.0), H(pitch=-4), RA(fwd=30, out=46), LA(fwd=30, out=50),
        RL(fwd=50, out=6), LL(fwd=-10, out=6), e="out")
    end = [T(roll=-20, pitch=12, turn=-354, y=-0.15, x=-0.15), H(roll=17, pitch=-10, turn=-6),
           RA(fwd=-24, out=58, twist=10), LA(fwd=46, out=66, twist=-6), RL(fwd=44, out=6), LL(fwd=-44, out=6)]
    a.k(0.32, *(end if s > 0 else mirror(end)))
    a.mark(0.22, "Attach")
    a.preview_ground = -40
    a.preview_scenery = wall_side(side * 1.75, -14, 14, -9, 9)
    a.preview_panels = [("back_r" if side > 0 else "back", None, 0, "behind"), ("front_l" if side > 0 else "front", None, 0, "")]
    return a


def wall_jump():
    a = Anim("WallJump", 0.5, priority="Action", category=CAT, grounded=False,
             description="Tuck against the wall, kick off, arms flung out into the wings pose (V1 5.2 s).")
    a.k(0.0, T(pitch=-14, y=0.25), H(pitch=-12), RA(fwd=100, out=42), LA(fwd=96, out=46), RL(fwd=96, out=10),
        LL(fwd=84, out=14), e="io")
    a.k(0.08, T(pitch=-6, y=0.3), H(pitch=-6), RA(fwd=60, out=34), LA(fwd=56, out=36), RL(fwd=100, out=10),
        LL(fwd=90, out=12), e="out")
    a.k(0.2, T(pitch=-18, y=0.1), H(pitch=-16), RA(fwd=70, out=96), LA(fwd=60, out=100), RL(fwd=-14, out=6),
        LL(fwd=-30, out=8), e="io")
    a.k(0.5, *WINGS)
    a.mark(0.1, "Kick")
    a.preview_ground = -14
    a.preview_scenery = wall_front(-1.75, -7, 7, -14, 8)
    a.preview_root = lambda t: (0.0, 3.2 * smoothstep((t - 0.06) / 0.44) - 0.6 * smoothstep((t - 0.3) / 0.2),
                                2.6 * smoothstep((t - 0.07) / 0.43))
    a.preview_panels = [("back", None, 0, "behind"), ("side", None, 0, "")]
    return a


def vault():
    a = Anim("Vault", 0.56, priority="Action", category=CAT, grounded=False, world_legs=False,
             description="Kong vault over a waist-high wall: dive, hands plant, knees tuck through, land running "
                         "(V1 4.3 s, 6.9 s). Move the root up ~1.5 studs and forward while it plays.")
    a.k(0.0, *RUN_READY, e="io")
    a.k(0.09, T(pitch=44, y=0.1), H(pitch=-30), RA(fwd=118, out=20), LA(fwd=114, out=22), RL(fwd=-24, out=4),
        LL(fwd=-48, out=6), e="out")
    a.k(0.2, T(pitch=72, y=0.35, piv=0), H(pitch=-50), RA(fwd=104, out=22), LA(fwd=100, out=24),
        RL(fwd=110, out=10), LL(fwd=118, out=12), e="io")
    a.k(0.32, T(pitch=34, y=0.25), H(pitch=-24), RA(fwd=-24, out=56), LA(fwd=-18, out=60), RL(fwd=90, out=6),
        LL(fwd=60, out=8), e="io")
    a.k(0.44, T(pitch=22, y=-0.3), H(pitch=-16), RA(fwd=-20, out=36), LA(fwd=40, out=30), RL(fwd=46, out=4),
        LL(fwd=-30, out=4))
    a.k(0.56, *RUN_READY)
    a.mark(0.18, "Plant")
    a.mark(0.44, "Land")
    a.preview_scenery = [("box", (0, -2.0, -1.4), (6.0, 2.0, 1.0), (128, 52, 58))]
    a.preview_root = lambda t: (0.0, 1.3 * smoothstep(t / 0.2) - 1.3 * smoothstep((t - 0.3) / 0.16),
                                3.0 - 6.0 * smoothstep(t / 0.5))
    a.preview_panels = FRONT_SIDE
    return a


# =============================================================================
# getting hit
# =============================================================================

def hit_react():
    a = Anim("HitReact", 0.6, priority="Action3", category="Hit Reactions",
             description="Light hit flinch (V1 36.0 s, 38.0 s): head snaps back, arms jolt up in front, "
                         "hold a beat, then lower.")
    a.k(0.0, *RELAXED, e="out")
    a.k(0.05, T(pitch=-9, y=-0.1, z=-0.15), H(pitch=-16, roll=7, turn=5), RA(fwd=36, out=26, twist=14),
        LA(fwd=30, out=24, twist=12), RL(fwd=10, out=7), LL(fwd=-16, out=7), e="io")
    a.k(0.2, T(pitch=-3, y=-0.14, z=-0.18), H(pitch=-6, roll=4), RA(fwd=46, out=16, yaw=-8, twist=8),
        LA(fwd=40, out=14, yaw=-8, twist=6), RL(fwd=8, out=6), LL(fwd=-12, out=6))
    a.k(0.36, T(pitch=0, y=-0.1, z=-0.15), H(pitch=-2, roll=2), RA(fwd=38, out=14, yaw=-6, twist=6),
        LA(fwd=32, out=13, yaw=-6, twist=6), RL(fwd=6, out=5), LL(fwd=-8, out=5))
    a.k(0.6, *RELAXED)
    a.mark(0.0, "Hit")
    a.preview_panels = FRONT_SIDE
    return a


def hit_heavy():
    a = Anim("HitHeavy", 0.9, priority="Action3", category="Hit Reactions",
             description="Heavy hit: knocked back with the arms flung out, stumbling steps, hunched recovery.")
    a.k(0.0, *RELAXED, e="out")
    a.k(0.06, T(pitch=-30, y=-0.25, z=-0.4, roll=6), H(pitch=-32, roll=-6), RA(fwd=60, out=64, twist=20),
        LA(fwd=46, out=70, twist=20), RL(fwd=30, out=6), LL(fwd=-34, out=8), e="io")
    a.k(0.26, T(pitch=-14, y=-0.4, z=-0.6, roll=-4), H(pitch=-14, roll=4), RA(fwd=36, out=52), LA(fwd=26, out=46),
        RL(fwd=-28, out=8), LL(fwd=20, out=8), e="io")
    a.k(0.48, T(pitch=18, y=-0.42, z=-0.45), H(pitch=-6), RA(fwd=36, out=24, yaw=-8), LA(fwd=34, out=24, yaw=-8),
        RL(fwd=22, out=10), LL(fwd=-26, out=10), e="io")
    a.k(0.9, *RELAXED)
    a.mark(0.0, "Hit")
    a.mark(0.26, "Stumble")
    a.preview_panels = FRONT_SIDE
    return a


def build():
    return [idle(), walk(), sprint(), crouch_idle(), crouch_walk(), jump(), fall(), land(), land_heavy(),
            land_roll(), roll(), slide_start(), slide_loop(), slide_end(), ledge_hang(), ledge_climb(),
            wall_climb(), _wallrun("WallRunRight", 1), _wallrun("WallRunLeft", -1),
            _wallrun_enter("WallRunEnterRight", 1), _wallrun_enter("WallRunEnterLeft", -1), wall_jump(), vault(),
            hit_react(), hit_heavy()]
