"""
Build everything:

    python3 build.py                 # bake + export .rbxmx + render every GIF
    python3 build.py --no-gifs       # export only
    python3 build.py --only Sprint Walk
    python3 build.py --sheet Sprint  # contact sheet PNG (for quick checks)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from r6anim import core, render  # noqa: E402
from anims import locomotion  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT_ANIM = os.path.join(ROOT, "animations")
OUT_GIF = os.path.join(ROOT, "previews")


def all_anims():
    anims = []
    anims += locomotion.build()
    try:
        from anims import combat
        anims += combat.build()
    except ImportError:
        pass
    try:
        from anims import objects
        anims += objects.build()
    except ImportError:
        pass
    names = [a.name for a in anims]
    dup = {n for n in names if names.count(n) > 1}
    assert not dup, dup
    return anims


class _LazyBaked(dict):
    """name -> Baked, baking each animation the first time it is asked for."""

    def __init__(self):
        super().__init__()
        self.anims = {a.name: a for a in all_anims()}

    def __missing__(self, name):
        b = core.bake(self.anims[name])
        self[name] = b
        return b

    def keys(self):
        return self.anims.keys()

    def values(self):
        return [self[n] for n in self.anims]

    def items(self):
        return [(n, self[n]) for n in self.anims]

    def __iter__(self):
        return iter(self.anims)

    def __len__(self):
        return len(self.anims)


_BAKED = None


def baked(name=None):
    global _BAKED
    if _BAKED is None:
        _BAKED = _LazyBaked()
    return _BAKED if name is None else _BAKED[name]


def panels_for(a, bk):
    out = []
    for view, base, scroll, label in a.preview_panels or [("front", None, 0, ""), ("side", None, 0, "")]:
        out.append(dict(view=view, base=bk[base] if base else None, scroll=scroll, label=label))
    return out


def subtitle(a):
    bits = [a.priority]
    if a.loop:
        bits.append("Looped")
    if a.upper_only or a.export_joints:
        bits.append("upper body only")
    return " · ".join(bits)


def _render_one(name):
    bk = baked()
    b = bk[name]
    a = b.anim
    path = os.path.join(OUT_GIF, f"{name}.gif")
    fps = 15 if a.length > 2.5 and not a.loop else 20
    render.render_gif(b, path, panels_for(a, bk), subtitle=subtitle(a), fps=fps)
    return name, os.path.getsize(path)


def sheet(name, n=12, cols=6, out=None):
    from PIL import Image
    bk = baked()
    b = bk[name]
    a = b.anim
    pans = panels_for(a, bk)
    ts = [a.length * i / (n - (0 if a.loop else 1)) for i in range(n)]
    W = H = 230
    tiles = []
    # reuse render_gif machinery by rendering a temporary short gif per time is wasteful; render frames directly
    import numpy as np
    frames = render.render_gif(b, os.path.join(os.environ.get("SHEET_DIR", "/tmp"), "_sheet.gif"), pans, panel=(W, H), ss=1, fps=max(1, int(round(n / a.length))))
    step = max(1, len(frames) // n)
    pick = frames[::step][:n]
    fw, fh = pick[0].size
    rows = (len(pick) + cols - 1) // cols
    cols2 = max(1, cols // len(pans))
    rows = (len(pick) + cols2 - 1) // cols2
    img = Image.new("RGB", (fw * cols2, fh * rows), (0, 0, 0))
    for i, fr in enumerate(pick):
        img.paste(fr, ((i % cols2) * fw, (i // cols2) * fh))
    out = out or os.path.join(os.environ.get("SHEET_DIR", "/tmp"), f"sheet_{name}.png")
    img.save(out)
    return out


def export_all(bk):
    os.makedirs(OUT_ANIM, exist_ok=True)
    groups = {}
    for name, b in bk.items():
        groups.setdefault(b.anim.category, []).append(b)
    for cat, items in groups.items():
        d = os.path.join(OUT_ANIM, cat.replace(" ", ""))
        os.makedirs(d, exist_ok=True)
        for b in items:
            core.write_single(b, os.path.join(d, f"{b.anim.name}.rbxmx"))
    flat = list(bk.values())
    core.write_folder(flat, os.path.join(OUT_ANIM, "AnimSaves_ALL.rbxmx"), "AnimSaves", "Model")
    core.write_folder(flat, os.path.join(OUT_ANIM, "R6Animations_ByCategory.rbxmx"), "R6Animations", "Folder",
                      groups={k: v for k, v in groups.items()})
    manifest = []
    for name, b in bk.items():
        a = b.anim
        manifest.append(dict(name=name, category=a.category, length=round(a.length, 3), loop=a.loop,
                             priority=a.priority, upperBodyOnly=bool(a.upper_only or a.export_joints),
                             joints=[core.MOTORS[j].name for j in b.frames[0].keys()],
                             markers=[dict(time=round(t, 3), name=n) for t, n in b.markers],
                             keyframes=len(b.times), description=a.description))
    with open(os.path.join(OUT_ANIM, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-gifs", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--sheet", nargs="*")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--frames", nargs="*", help="Name t1 t2 ...")
    args = ap.parse_args()
    bk = baked()
    if args.frames:
        print(frame_png(args.frames[0], [float(x) for x in args.frames[1:]]))
        return
    if args.sheet:
        for n in args.sheet:
            print(sheet(n))
        return
    manifest = export_all(bk)
    print(f"exported {len(manifest)} animations")
    if args.no_gifs:
        return
    os.makedirs(OUT_GIF, exist_ok=True)
    names = args.only or list(bk.keys())
    with Pool(args.jobs) as pool:
        for name, size in pool.imap_unordered(_render_one, names):
            print(f"  {name}.gif  {size / 1024:.0f} KB", flush=True)


def frame_png(name, times, out=None, size=300):
    """Render specific times of an animation side by side (for checking)."""
    from PIL import Image
    bk = baked()
    b = bk[name]
    a = b.anim
    pans = panels_for(a, bk)
    # temporarily render a clip containing only the wanted times
    imgs = []
    for t in times:
        sub = core.Baked(a, b.times, b.frames, b.names, b.markers)
        frames = render.render_gif_times(sub, pans, [t], panel=(size, size))
        imgs.append(frames[0])
    W = sum(i.width for i in imgs)
    img = Image.new("RGB", (W, imgs[0].height))
    x = 0
    for i in imgs:
        img.paste(i, (x, 0))
        x += i.width
    out = out or os.path.join(os.environ.get("SHEET_DIR", "/tmp"), f"frame_{name}.png")
    img.save(out)
    return out


if __name__ == "__main__":
    main()
