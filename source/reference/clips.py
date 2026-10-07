"""Reference clips: which stretch of which video corresponds to which animation.

crop = (x, y, w, h) in video pixels around the character.
anim_t0 / speed map video time onto animation time.
az / el = camera azimuth (0 = in front of the character, 180 = behind) and elevation.
"""

import os

UPLOADS = os.environ.get("REF_DIR", "/root/.claude/uploads/b041f1f9-94fd-503c-bf38-f386495f5efe")
VIDEOS = {
    "v1": os.path.join(UPLOADS, "074e4085-ROBLOX_-_ADVANCED_MOVEMENT_SYSTEM_SALE.mp4"),
    "v2": os.path.join(UPLOADS, "17e21298-Roblox_studio_-_Movement_system_SHOWCASE.mp4"),
}

VIDEO_H = {"v1": 1080, "v2": 692}
CLIPS = {}


def clip(name, **kw):
    CLIPS[name] = kw

# --- V1 (Ironpeak V6) -------------------------------------------------------
clip("Sprint_v1", anim="Sprint", video="v1", t0=19.55, t1=20.55, crop=(590, 490, 180, 170),
     az=180, el=30, dist=28, anim_t0=0.0, speed=1.0)

# --- V2 (showcase) ------------------------------------------------------------
clip("Sprint_v2", anim="Sprint", video="v2", t0=18.15, t1=19.05, crop=(530, 320, 220, 210),
     az=180, el=30, dist=17, anim_t0=0.0, speed=0.85)
clip("Walk_v2", anim="Walk", video="v2", t0=2.0, t1=3.0, crop=(460, 300, 260, 260),
     az=180, el=30, dist=13, anim_t0=0.5, speed=1.0)
clip("CrouchWalk_v2", anim="CrouchWalk", video="v2", t0=21.2, t1=22.2, crop=(500, 320, 280, 230),
     az=180, el=22, dist=11, anim_t0=0.0, speed=1.0)
clip("Idle_v2", anim="Idle", video="v2", t0=28.6, t1=29.6, crop=(540, 320, 200, 240),
     az=0, el=8, fov=40, anim_t0=0.0, speed=1.0, radius=3.4)
clip("Roll_v1", anim="Roll", video="v1", t0=21.9, t1=22.6, crop=(430, 390, 450, 450),
     az=180, el=40, fov=40, anim_t0=0.0, speed=1.0, radius=3.6)
clip("Roll_v1b", anim="Roll", video="v1", t0=48.35, t1=49.15, crop=(500, 420, 560, 420),
     az=180, el=14, dist=16, anim_t0=0.0, speed=1.0)
clip("Slide_v1", anim="SlideStart", video="v1", t0=0.36, t1=0.66, crop=(430, 390, 450, 450),
     az=180, el=16, dist=11, anim_t0=0.0, speed=1.0)
clip("SlideHold_v1", anim="Slide", video="v1", t0=0.5, t1=0.7, crop=(430, 390, 450, 450),
     az=180, el=16, dist=11, anim_t0=0.0, speed=1.0)
clip("SlideEnd_v1", anim="SlideEnd", video="v1", t0=0.85, t1=1.3, crop=(430, 390, 450, 450),
     az=180, el=16, dist=11, anim_t0=0.0, speed=1.0)
clip("HitReact_v1", anim="HitReact", video="v1", t0=35.9, t1=36.4, crop=(430, 390, 450, 450),
     az=-20, el=10, dist=13, anim_t0=-0.03, speed=1.0)
clip("HitReact_v1b", anim="HitReact", video="v1", t0=37.95, t1=38.5, crop=(430, 390, 450, 450),
     az=0, el=10, dist=13, anim_t0=-0.03, speed=1.0)
clip("LandRoll_v1", anim="LandRoll", video="v1", t0=10.95, t1=11.75, crop=(430, 390, 450, 450),
     az=150, el=20, fov=40, anim_t0=0.0, speed=1.0, radius=3.8)
