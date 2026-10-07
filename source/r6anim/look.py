"""
Classic Roblox R6 look for previews: round "Head" mesh with the classic smile,
red shirt with the old Roblox logo, grey shorts, skin-coloured limbs.
Everything is built as triangles with per-vertex colours for the rasteriser.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import List, Tuple

import numpy as np

SKIN = np.array([204, 150, 112.0])
SHIRT = np.array([178, 28, 28.0])
SHORTS = np.array([150, 151, 155.0])
STRIPE = np.array([178, 28, 28.0])
FACE = np.array([22, 22, 22.0])
LOGO_W = np.array([236, 236, 236.0])
LOGO_R = np.array([178, 28, 28.0])

LIGHT = np.array([-0.42, 0.78, -0.46])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
FILL = np.array([0.6, 0.25, 0.75])
FILL = FILL / np.linalg.norm(FILL)


def shade(normals: np.ndarray, base: np.ndarray) -> np.ndarray:
    """Roblox-ish plastic: strong ambient, soft key, weak fill, sky from above."""
    d = np.clip(normals @ LIGHT, 0, None)
    f = np.clip(normals @ FILL, 0, None)
    up = np.clip(normals[..., 1], -1, 1)
    k = 0.50 + 0.46 * d + 0.12 * f + 0.07 * up
    return np.clip(base * k[..., None], 0, 255)


class TriBatch:
    """Triangles with per-vertex colours."""

    def __init__(self):
        self.p: List[np.ndarray] = []   # (n,3,3)
        self.c: List[np.ndarray] = []   # (n,3,3)

    def add(self, pts: np.ndarray, cols: np.ndarray):
        self.p.append(pts)
        self.c.append(cols)

    def arrays(self):
        if not self.p:
            return np.zeros((0, 3, 3)), np.zeros((0, 3, 3))
        return np.concatenate(self.p), np.concatenate(self.c)


# ---------------------------------------------------------------------------
# boxes
# ---------------------------------------------------------------------------

_C = np.array([[sx, sy, sz] for sx in (-0.5, 0.5) for sy in (-0.5, 0.5) for sz in (-0.5, 0.5)])
_F = [((0, 1, 3, 2), (-1, 0, 0)), ((4, 6, 7, 5), (1, 0, 0)), ((0, 4, 5, 1), (0, -1, 0)),
      ((2, 3, 7, 6), (0, 1, 0)), ((0, 2, 6, 4), (0, 0, -1)), ((1, 5, 7, 3), (0, 0, 1))]


def box(batch: TriBatch, m: np.ndarray, size, color, center=(0, 0, 0)):
    size = np.asarray(size, float)
    pts = (_C * size + np.asarray(center, float)) @ m[:3, :3].T + m[:3, 3]
    color = np.asarray(color, float)
    tris, cols = [], []
    for idx, n in _F:
        nw = m[:3, :3] @ np.array(n, float)
        c = shade(nw[None], color)[0]
        a, b, cc, d = (pts[i] for i in idx)
        tris += [[a, b, cc], [a, cc, d]]
        cols += [[c, c, c], [c, c, c]]
    batch.add(np.array(tris), np.array(cols))


def quad_on(batch: TriBatch, m: np.ndarray, corners_local: np.ndarray, normal_local, color):
    pts = corners_local @ m[:3, :3].T + m[:3, 3]
    c = shade((m[:3, :3] @ np.asarray(normal_local, float))[None], np.asarray(color, float))[0]
    a, b, cc, d = pts
    batch.add(np.array([[a, b, cc], [a, cc, d]]), np.array([[c, c, c], [c, c, c]]))


# ---------------------------------------------------------------------------
# head mesh (revolved profile, like the classic SpecialMesh "Head" x1.25)
# ---------------------------------------------------------------------------

HEAD_R = 0.62     # radius of the cylinder
HEAD_H = 1.22     # total height
HEAD_BEVEL = 0.30
SEG = 28


@lru_cache(maxsize=1)
def _head_local():
    # profile from bottom centre to top centre: (r, y, nr, ny)
    prof = []
    hb = HEAD_H / 2
    rb = HEAD_BEVEL
    prof.append((0.0, -hb, 0.0, -1.0))
    for i in range(0, 7):
        a = math.pi / 2 * (i / 6)          # 0 -> 90 deg around the lower bevel
        r = (HEAD_R - rb) + rb * math.sin(a)
        y = -hb + rb - rb * math.cos(a)
        prof.append((r, y, math.sin(a), -math.cos(a)))
    for i in range(0, 7):
        a = math.pi / 2 * (i / 6)
        r = (HEAD_R - rb) + rb * math.cos(a)
        y = hb - rb + rb * math.sin(a)
        prof.append((r, y, math.cos(a), math.sin(a)))
    prof.append((0.0, hb, 0.0, 1.0))
    verts = np.zeros((len(prof), SEG, 3))
    norms = np.zeros((len(prof), SEG, 3))
    for j, (r, y, nr, ny) in enumerate(prof):
        for s in range(SEG):
            th = 2 * math.pi * s / SEG
            verts[j, s] = (r * math.sin(th), y, -r * math.cos(th))
            n = np.array([nr * math.sin(th), ny, -nr * math.cos(th)])
            norms[j, s] = n / max(np.linalg.norm(n), 1e-9)
    tri_idx = []
    for j in range(len(prof) - 1):
        for s in range(SEG):
            s2 = (s + 1) % SEG
            tri_idx.append(((j, s), (j + 1, s), (j + 1, s2)))
            tri_idx.append(((j, s), (j + 1, s2), (j, s2)))
    face = _face_polys()
    return verts, norms, tri_idx, face


def _surface(th: float, y: float, off=0.012):
    """Point on the head's side surface at angle th (0 = front) and height y."""
    hb = HEAD_H / 2
    rb = HEAD_BEVEL
    if abs(y) <= hb - rb:
        r = HEAD_R
    else:
        dy = abs(y) - (hb - rb)
        r = (HEAD_R - rb) + math.sqrt(max(rb * rb - dy * dy, 0.0))
    r += off
    return np.array([r * math.sin(th), y, -r * math.cos(th)])


def _face_polys():
    """Classic smile: two upright oval eyes and a thin smile arc."""
    polys = []
    for ex in (-0.21, 0.21):
        n = 14
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            th = ex + 0.055 * math.cos(a)
            y = 0.13 + 0.115 * math.sin(a)
            pts.append(_surface(th, y))
        polys.append(np.array(pts))
    # smile: band between two arcs
    n = 16
    outer, inner = [], []
    for i in range(n + 1):
        u = -1 + 2 * i / n
        th = 0.38 * u
        yc = -0.06 - 0.17 * (1 - u * u) ** 0.9
        w = 0.022 + 0.018 * (1 - u * u)
        outer.append(_surface(th, yc - w))
        inner.append(_surface(th, yc + w))
    polys.append(np.array(outer + inner[::-1]))
    return polys


def head(batch: TriBatch, m: np.ndarray):
    verts, norms, tri_idx, face = _head_local()
    R, t = m[:3, :3], m[:3, 3]
    v = verts @ R.T + t
    n = norms @ R.T
    cols = shade(n, SKIN)
    P = np.array([[v[a], v[b], v[c]] for a, b, c in tri_idx])
    C = np.array([[cols[a], cols[b], cols[c]] for a, b, c in tri_idx])
    batch.add(P, C)
    for poly in face:
        pw = poly @ R.T + t
        cen = pw.mean(0)
        nn = (poly.mean(0) * np.array([1, 0, 1]))
        nn = R @ (nn / max(np.linalg.norm(nn), 1e-9))
        c = shade(nn[None], FACE)[0]
        if len(poly) > 20:   # smile band: triangulate as strip
            k = len(poly) // 2
            o, i_ = poly[:k], poly[k:][::-1]
            tris = []
            for s in range(k - 1):
                tris.append([o[s], o[s + 1], i_[s + 1]])
                tris.append([o[s], i_[s + 1], i_[s]])
            tw = np.array(tris) @ R.T + t
        else:
            tris = [[cen, pw[s], pw[(s + 1) % len(pw)]] for s in range(len(pw))]
            tw = np.array(tris)
        batch.add(tw, np.tile(c, (len(tw), 3, 1)))


# ---------------------------------------------------------------------------
# full character
# ---------------------------------------------------------------------------

def character(batch: TriBatch, parts):
    torso = parts["Torso"]
    box(batch, torso, (2, 2, 1), SHIRT)
    # old Roblox logo on the left chest: tilted white square with a red centre
    lm = torso
    ang = math.radians(18)
    ca, sa = math.cos(ang), math.sin(ang)

    def sq(cx, cy, h, z):
        pts = []
        for dx, dy in ((-h, -h), (h, -h), (h, h), (-h, h)):
            pts.append([cx + dx * ca - dy * sa, cy + dx * sa + dy * ca, z])
        return np.array(pts)

    quad_on(batch, lm, sq(-0.55, 0.5, 0.17, -0.505), (0, 0, -1), LOGO_W)
    quad_on(batch, lm, sq(-0.55, 0.5, 0.05, -0.51), (0, 0, -1), LOGO_R)
    for name in ("Right Arm", "Left Arm"):
        box(batch, parts[name], (1, 2, 1), SKIN)
    for name in ("Right Leg", "Left Leg"):
        m = parts[name]
        box(batch, m, (1, 0.82, 1), SHORTS, center=(0, 0.59, 0))
        box(batch, m, (1.006, 0.09, 1.006), STRIPE, center=(0, 0.14, 0))
        box(batch, m, (1, 1.10, 1), SKIN, center=(0, -0.45, 0))
    head(batch, parts["Head"])
