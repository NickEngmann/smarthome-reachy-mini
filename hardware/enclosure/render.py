#!/usr/bin/env python3
"""Shaded views of the dungarees enclosure on Reachy Mini (no GPU: STL triangles painted with
matplotlib, the reMixTape render.py approach - everything in ONE Poly3DCollection so depth
sorting works).

    python render.py            # reads out/stl/*.stl, writes out/render/*.png

Reachy is its body mesh (cad/reachy-mini/reachy_mini_body.stl, robot frame); the display is
Elecrow's STEP as STL with the flex tails clipped, moved into the robot frame by geom.placement().
"""
import os, sys, struct, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geom as G

REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out")
RDIR = os.path.join(OUT, "render")
PRE = "reachy-crowpanel"

REACHY = (0.93, 0.93, 0.91)
DENIM = (0.25, 0.40, 0.62)
DENIM_DARK = (0.19, 0.30, 0.48)
BOARD = (0.08, 0.10, 0.14)


def load_stl(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    return np.frombuffer(d, np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)["v"].astype(float)


def subdivide(T, maxedge=8.0, depth=0):
    if depth > 3 or not len(T):
        return T
    e = np.stack([np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1),
                  np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], axis=1)
    big = e.max(axis=1) > maxedge
    if not big.any():
        return T
    B = T[big]
    m01, m12, m20 = (B[:, 0] + B[:, 1]) / 2, (B[:, 1] + B[:, 2]) / 2, (B[:, 2] + B[:, 0]) / 2
    S = np.concatenate([np.stack([B[:, 0], m01, m20], 1), np.stack([m01, B[:, 1], m12], 1),
                        np.stack([m20, m12, B[:, 2]], 1), np.stack([m01, m12, m20], 1)])
    return np.concatenate([T[~big], subdivide(S, maxedge, depth + 1)])


def shade(T, base, light=(0.55, -0.35, 0.75)):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1
    n = n / ln[:, None]
    l = np.array(light) / np.linalg.norm(light)
    k = 0.30 + 0.70 * np.abs(n @ l)
    return np.clip(np.array(base)[None, :] * k[:, None], 0, 1)


def draw(parts, name, elev, azim, title, lims=None, zoom=1.2, light=(0.55, -0.35, 0.75)):
    fig = plt.figure(figsize=(14, 10), dpi=100)
    ax = fig.add_subplot(111, projection="3d")
    parts = [(T, c) for T, c in parts if len(T)]
    allT = np.concatenate([T for T, _ in parts])
    allC = np.concatenate([shade(T, c, light) for T, c in parts])
    if lims is not None:
        (x0, x1), (y0, y1), (z0, z1) = lims
        cen = allT.mean(axis=1)
        m = (cen[:, 0] > x0) & (cen[:, 0] < x1) & (cen[:, 1] > y0) & (cen[:, 1] < y1) & (cen[:, 2] > z0) & (cen[:, 2] < z1)
        allT, allC = allT[m], allC[m]
    ax.add_collection3d(Poly3DCollection(allT, facecolors=allC, edgecolors=allC, linewidths=0.2, antialiased=False))
    mn, mx = allT.reshape(-1, 3).min(0), allT.reshape(-1, 3).max(0)
    ext = mx - mn + 1.0
    ax.set_xlim(mn[0], mx[0]); ax.set_ylim(mn[1], mx[1]); ax.set_zlim(mn[2], mx[2])
    ax.set_box_aspect(tuple(ext / ext.max()), zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=13, pad=2)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=0.96)
    fig.savefig(os.path.join(RDIR, name + ".png"), facecolor="white")
    plt.close(fig)
    print("wrote render/%s.png (%d triangles)" % (name, len(allT)))


def board_in_robot():
    T = load_stl(os.path.join(REPO, "cad", "crowpanel-advanced-7in-esp32-p4", "CrowPanel-Advanced-7in-ESP32-P4_no-flex-tails.stl"))
    T = T[~(T[:, :, 2] < -53.0).any(axis=1)]                  # drop the optional camera drawn below the board
    X0, Z0 = G.placement()
    t = math.radians(-G.TILT)
    x, y, z = T[..., 1], -T[..., 0], T[..., 2]                # Rz(-90)
    xr = x * math.cos(t) + z * math.sin(t) + X0
    zr = -x * math.sin(t) + z * math.cos(t) + Z0
    return np.stack([xr, y, zr], axis=-1)


def main():
    os.makedirs(RDIR, exist_ok=True)
    reachy = load_stl(os.path.join(REPO, "cad", "reachy-mini", "reachy_mini_body.stl"))
    P = {n: subdivide(load_stl(os.path.join(OUT, "stl", "%s-%s.stl" % (PRE, n)))) for n in ("bezel", "tray-cradle", "backstrap")}
    board = board_in_robot()
    full = [(reachy, REACHY), (board, BOARD), (P["tray-cradle"], DENIM), (P["backstrap"], DENIM), (P["bezel"], DENIM_DARK)]
    draw(full, "hero", 20, 38, "Reachy Mini in dungarees: CrowPanel 7\" P4 as the bib (body only shown)")
    draw(full, "front", 4, 0, "front: stitched bib, buttons, heart")
    draw(full, "side-usb", 6, 90, "robot's left: USB-C x2 + switch slot, strap & buckle, full-height side joint")
    draw(full, "back", 18, 180, "back: crossed straps, buttons, pockets, belt loops, spring tabs, cuff/gutter", light=(-0.6, 0.3, 0.75))
    draw(full, "back-three-quarter", 22, 215, "back three-quarter", light=(-0.6, 0.3, 0.75))
    draw([(board, BOARD), (P["tray-cradle"], DENIM), (P["backstrap"], DENIM), (P["bezel"], DENIM_DARK)], "enclosure-only", 22, 140,
         "enclosure without the robot", light=(-0.4, 0.5, 0.75))
    draw(full, "joint-closeup", 10, 70, "side joint: tongue over the strip, two flex tabs with pull lips, side buttons",
         lims=((-34.0, 26.0), (60.0, 100.0), (26.0, 128.0)), zoom=1.0)
    # close-ups with a low, raking light so shallow stitching and engraving read
    draw([(P["bezel"], DENIM_DARK), (board, BOARD)], "bib-closeup", 8, 12, "bib: stitched border, buttons, heart (engraved, face-down print)",
         lims=((90.0, 120.0), (-95.0, 95.0), (25.0, 150.0)), zoom=1.1, light=(0.35, 0.9, 0.25))
    draw([(P["backstrap"], DENIM)], "back-closeup", 10, 180, "back: edge-stitched crossed straps, buttons, pockets, waistband stitching, belt loops",
         lims=((-100.0, -30.0), (-80.0, 80.0), (26.0, 128.0)), zoom=1.1, light=(-0.35, 0.85, 0.35))
    ex = [(reachy, REACHY), (board + np.array([30.0, 0, 0]), BOARD), (P["tray-cradle"], DENIM),
          (P["backstrap"] + np.array([-45.0, 0, 0]), DENIM), (P["bezel"] + np.array([60.0, 0, 0]), DENIM_DARK)]
    draw(ex, "exploded", 22, 35, "exploded: backstrap slides on from behind, bezel snaps on the front")
    cut = [(T[(T[:, :, 1] < 0).all(axis=1)], c) for T, c in full]
    draw(cut, "section", 2, 90, "section at robot y = 0: tray back, ribs, collar, spring nub against the shell")
    for n, c in (("bezel", DENIM_DARK), ("tray-cradle", DENIM), ("backstrap", DENIM)):
        T = subdivide(load_stl(os.path.join(OUT, "print", "%s-%s-print.stl" % (PRE, n))))
        draw([(T, c)], "print-" + n, 35, -60, "%s - as printed (on the bed)" % n)


if __name__ == "__main__":
    main()
