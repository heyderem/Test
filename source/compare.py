"""
Side-by-side comparison of reference-video clips with our animations.

    python3 compare.py Sprint_v2            # PNG grid: video row over render row
    python3 compare.py Sprint_v2 --gif      # animated side-by-side GIF
    python3 compare.py --list

Clips live in reference/clips.py.  Each clip maps a stretch of a reference
video onto an animation (start time + playback speed) and gives the camera
angle that matches the video's chase camera.
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build  # noqa: E402
from r6anim import core, render  # noqa: E402
from reference.clips import CLIPS, VIDEOS  # noqa: E402

OUT = os.environ.get("CMP_DIR", os.path.join(os.path.dirname(HERE), "comparisons"))


def video_frames(clip, fps=30):
    src = VIDEOS[clip["video"]]
    x, y, w, h = clip["crop"]
    tmp = tempfile.mkdtemp(prefix="cmp_")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{clip['t0']:.3f}", "-t", f"{clip['t1'] - clip['t0']:.3f}",
                        "-i", src, "-vf", f"fps={fps},crop={w}:{h}:{x}:{y}", os.path.join(tmp, "f_%04d.png")],
                       check=True)
        files = sorted(os.listdir(tmp))
        frames = [Image.open(os.path.join(tmp, f)).convert("RGB") for f in files]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    times = [clip["t0"] + i / fps for i in range(len(frames))]
    return times, frames


def crop_fov(clip, video_fov=70.0):
    """Vertical FOV covered by the crop, given Roblox's default 70 degree camera."""
    from reference.clips import VIDEO_H
    h = clip["crop"][3]
    return math.degrees(2 * math.atan(h / VIDEO_H[clip["video"]] * math.tan(math.radians(video_fov / 2))))


def camera_for(clip, center, radius, W, H):
    if clip.get("dist") and "fov" not in clip:
        clip = dict(clip, fov=crop_fov(clip))
    az, el = clip.get("az", 180), clip.get("el", 18)
    fov = clip.get("fov", 34.0)
    dist = clip.get("dist") or radius / math.sin(math.radians(fov / 2)) * 1.02
    a, e = math.radians(az), math.radians(el)
    eye = center + dist * np.array([math.sin(a) * math.cos(e), math.sin(e), -math.cos(a) * math.cos(e)])
    return render.Camera(eye, center, W, H, fov)


def anim_time(clip, t_video, length, loop):
    t = clip.get("anim_t0", 0.0) + (t_video - clip["t0"]) * clip.get("speed", 1.0)
    if loop:
        return t % length
    return min(max(t, 0.0), length)


def render_clip(clip, times, size):
    bk = build.baked()
    b = bk[clip["anim"]]
    a = b.anim
    base = bk[clip["base"]] if clip.get("base") else None
    W, H = size
    ss = 2
    ats = [anim_time(clip, t, a.length, a.loop) for t in times]
    pts = []
    for t in ats[:: max(1, len(ats) // 12)] + [ats[-1]]:
        parts = core.pose_parts(render.compose(b, base, t, None if base is None else t % base.anim.length))
        for name in ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg"):
            pts.append(parts[name][:3, 3])
    pts = np.array(pts)
    center = (pts.min(0) + pts.max(0)) / 2
    center[1] = min(center[1], -0.4)
    radius = clip.get("radius", 3.6)
    cam = camera_for(clip, center, radius, W * ss, H * ss)
    scene = render.Scene(cam, a.preview_ground)
    out = []
    for t in ats:
        tr = render.compose(b, base, t, None if base is None else t % base.anim.length)
        parts = core.pose_parts(tr)
        scroll = clip.get("scroll", 0.0) * t
        tiles = render.render_frame([scene], [cam], parts, [], [], W, H, ss, scroll,
                                    render.scenery_boxes(a.preview_scenery, t) if clip.get("scenery") else [])
        out.append((t, tiles[0]))
    return out


def label(im, text, sub=None):
    d = ImageDraw.Draw(im)
    f = render.font(13)
    d.rectangle([0, 0, d.textlength(text, font=f) + 8, 18], fill=(15, 17, 22))
    d.text((4, 2), text, font=f, fill=(255, 255, 255))
    if sub:
        fs = render.font(11, False)
        w = d.textlength(sub, font=fs)
        d.rectangle([im.width - w - 8, 0, im.width, 16], fill=(15, 17, 22))
        d.text((im.width - w - 4, 2), sub, font=fs, fill=(200, 205, 215))
    return im


def grid(name, cols=10, every=1, tile=200, start=0):
    clip = CLIPS[name]
    times, frames = video_frames(clip)
    sel = list(range(start, len(frames), every))[:cols]
    vt = [times[i] for i in sel]
    vf = [frames[i] for i in sel]
    W = tile
    Hh = int(round(tile * clip["crop"][3] / clip["crop"][2]))
    rend = render_clip(clip, vt, (W, Hh))
    img = Image.new("RGB", (W * len(sel), Hh * 2 + 4), (10, 10, 12))
    for k, (t, fr) in enumerate(zip(vt, vf)):
        v = fr.resize((W, Hh), Image.LANCZOS)
        img.paste(label(v, f"{t - clip['t0']:.3f}"), (k * W, 0))
        at, r = rend[k]
        img.paste(label(r, f"{at:.2f}"), (k * W, Hh + 4))
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"{name}.png")
    img.save(p)
    return p


def gif(name, tile=300, fps=15, out=None):
    clip = CLIPS[name]
    times, frames = video_frames(clip, fps=fps)
    W = tile
    Hh = int(round(tile * clip["crop"][3] / clip["crop"][2]))
    rend = render_clip(clip, times, (W, Hh))
    seq = []
    for t, fr, (at, r) in zip(times, frames, rend):
        canvas = Image.new("RGB", (W * 2 + 4, Hh + 26), (20, 22, 28))
        canvas.paste(fr.resize((W, Hh), Image.LANCZOS), (0, 26))
        canvas.paste(r, (W + 4, 26))
        d = ImageDraw.Draw(canvas)
        d.text((6, 6), "Reference video", font=render.font(13), fill=(235, 238, 245))
        d.text((W + 10, 6), f"{clip['anim']}", font=render.font(13), fill=(235, 238, 245))
        seq.append(canvas)
    pal = seq[len(seq) // 2].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    q = [s.quantize(palette=pal, dither=Image.Dither.NONE) for s in seq]
    os.makedirs(OUT, exist_ok=True)
    p = out or os.path.join(OUT, f"{name}.gif")
    q[0].save(p, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, disposal=1)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--gif", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--cols", type=int, default=10)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--tile", type=int, default=200)
    args = ap.parse_args()
    if args.list:
        for k, c in CLIPS.items():
            print(f"{k:24s} {c['anim']:16s} {c['video']} {c['t0']:.2f}-{c['t1']:.2f}")
        return
    for n in args.names:
        if args.gif:
            print(gif(n))
        else:
            print(grid(n, cols=args.cols, every=args.every, tile=args.tile, start=args.start))


if __name__ == "__main__":
    main()
