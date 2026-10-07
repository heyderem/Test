"""Writes ANIMATIONS.md (every animation with its GIF, markers and notes) from
animations/manifest.json.  Run after build.py."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ["Movement", "Hit Reactions", "Combat", "Objects/Small", "Objects/Medium", "Objects/Large", "Objects/Huge"]
INTRO = {
    "Movement": "Remakes of the movement in your reference video, plus walk / jump / landing / ledge pieces in the same style.",
    "Hit Reactions": "Getting hit (the flinch from the video and a heavier knock-back).",
    "Combat": "Unarmed attacks. `_UB` = upper body only (plays on top of Walk/Sprint).",
    "Objects/Small": "Rocks, cans, bricks... **one hand, light and quick.**",
    "Objects/Medium": "Crates, barrels, chairs... **one hand, big dramatic wind-ups.**",
    "Objects/Large": "Cars, boulders, dumpsters... **two hands, heavy impacts.**",
    "Objects/Huge": "Trains, planes, buses (2-3x your height)... **titan-sized two-hand moves.**",
}


def main():
    with open(os.path.join(ROOT, "animations", "manifest.json")) as f:
        manifest = json.load(f)
    by_cat = {}
    for a in manifest:
        by_cat.setdefault(a["category"], []).append(a)
    lines = ["# Animation previews", "",
             "Every GIF is rendered from the exact keyframes in the `.rbxmx` files on a classic R6 rig. "
             "Objects, sparks and dust are preview-only (they are not part of the animation). "
             "Blue ticks on the timeline are markers; the banner shows a marker as it fires.", "",
             "Want something changed? Quote the animation name and what to change "
             "(e.g. *\"MediumThrow: bigger knee lift, release later\"*).", ""]
    lines.append("| Section | Animations |")
    lines.append("|---|---|")
    for cat in ORDER:
        if cat in by_cat:
            anchor = cat.lower().replace("/", "").replace(" ", "-")
            lines.append(f"| [{cat}](#{anchor}) | {len(by_cat[cat])} |")
    lines.append("")
    for cat in ORDER:
        items = by_cat.get(cat, [])
        if not items:
            continue
        lines += [f"## {cat}", "", INTRO.get(cat, ""), ""]
        for a in items:
            flags = [a["priority"], f"{a['length']:.2f}s"]
            if a["loop"]:
                flags.append("looped")
            if a["upperBodyOnly"]:
                flags.append("joints: " + ", ".join(a["joints"]))
            lines.append(f"### {a['name']}")
            lines.append("")
            lines.append(f"`{' · '.join(flags)}`  ")
            lines.append(a["description"] + "  ")
            if a["markers"]:
                mk = ", ".join(f"`{m['name']}` {m['time']:.2f}s" for m in a["markers"])
                lines.append(f"Markers: {mk}")
            lines.append("")
            lines.append(f"![{a['name']}](previews/{a['name']}.gif)")
            lines.append("")
    with open(os.path.join(ROOT, "ANIMATIONS.md"), "w") as f:
        f.write("\n".join(lines))
    print("wrote ANIMATIONS.md")


if __name__ == "__main__":
    main()
