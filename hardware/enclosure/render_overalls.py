#!/usr/bin/env python3
"""Renders of the bib straps on the dressed robot, and the sections that show how they fit.

    python render_overalls.py            # everything
    python render_overalls.py --section  # just the sections (fast: no 3-D painting)

Two kinds of picture, because they answer different questions:

  * The 3-D views (render.py's painter: STL triangles in one Poly3DCollection, no GPU) say what it
    LOOKS like. They read the three existing enclosure STLs unchanged and add the strap pair.
  * The SECTIONS say how it fits. Every part is cut by a plane and drawn as filled outlines, so the
    rim hook sitting on the shell's top edge, the 1.5 mm the run stands off the body and the spring
    finger's nub pressed into the collar band are visible as geometry rather than as a claim. A 3-D render of a
    2 mm strap against a curved shell cannot show a 1 mm gap; a section can.

There is no tight 3-D close-up of either end, for a related reason: render.py depth-sorts a single
Poly3DCollection by centroid, which breaks down at close range on the shell's coarse triangles -
the first attempt put shell facets through the strap. The sections are the close-ups.
"""
import os, sys, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as R
import overalls as O

OUT = os.path.join(HERE, "out")
RDIR = os.path.join(OUT, "render")
STRAP = (0.30, 0.46, 0.70)          # a shade lighter than the denim, so the strap reads against the shell
CUT_STRAP = (0.93, 0.55, 0.20)       # the cutaways: orange, as in the sections, so it stands out from the cradle

# Three cuts, because the foot is not the same shape all the way across. THROUGH_STRAP runs down the
# strap's own centre, rim hook to finger tip. THROUGH_FINGER is a closer look at the spring, where
# the nub is well into the band slot. THROUGH_TONGUE is inboard of the finger, where the tongue
# alone rests on the collar band's top edge.
# All are nudged 0.37 mm off a whole millimetre: the loft's slices sit on whole millimetres, so a
# cut exactly on one runs along a ring of shared edges, every edge comes back twice (once per
# adjoining triangle) and the section falls apart into dozens of two-segment scraps.
THROUGH_STRAP = O.STRAP_C + 0.37                                          # 40.87
THROUGH_FINGER = O.STRAP_C + 2.37                                         # 42.87
THROUGH_TONGUE = O.STRAP_Y - O.FOOT_W / 2 + 3.37                          # 30.87, inboard of the finger
SECTION_Y = THROUGH_STRAP
# From `overalls.py --check-only` (2026-09-30, v3). Titles quote them; re-run the check and update
# these when the geometry changes.
RIM_GAP = "0.64 mm"
MEASURED = "Measured: 0.81 mm from the run to the shell,\n%s at the rim hook, and the nub presses 0.54-0.80 mm into the band once seated." % RIM_GAP


def load(name):
    return R.subdivide(R.load_stl(os.path.join(OUT, "stl", "%s-%s.stl" % (R.PRE, name))))


def raw(name):
    return R.load_stl(os.path.join(OUT, "stl", "%s-%s.stl" % (R.PRE, name))).reshape(-1, 3, 3)


# --------------------------------------------------------------------- sectioning (robot XZ)
def slice_y(T, y):
    """Segments [(x0,z0),(x1,z1)] where the plane Y = y cuts the triangles T (n, 3, 3)."""
    T = T[(T[:, :, 1].min(1) <= y) & (T[:, :, 1].max(1) >= y)]
    out, seen = [], set()
    for tri in T:
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            ya, yb = tri[a, 1], tri[b, 1]
            if ya != yb and (ya - y) * (yb - y) <= 0:
                f = (y - ya) / (yb - ya)
                pts.append((tri[a, 0] + f * (tri[b, 0] - tri[a, 0]), tri[a, 2] + f * (tri[b, 2] - tri[a, 2])))
        if len(pts) != 2 or math.dist(pts[0], pts[1]) < 1e-6:
            continue
        k = tuple(sorted((round(pts[0][0], 3), round(pts[0][1], 3)))), tuple(sorted((round(pts[1][0], 3), round(pts[1][1], 3))))
        k = tuple(sorted(k))
        if k in seen:                                  # two triangles sharing an edge in the plane
            continue
        seen.add(k)
        out.append((pts[0], pts[1]))
    return out


def chains(segs, tol=1e-3):
    """Walk the segments into loops. Consumes EDGES, and grows each chain from both ends.

    The obvious version - mark nodes seen and walk forward - splits a closed loop into two pieces
    whenever it starts in the middle of one, which is what made the first section drawing look as
    though the strap had a hole in it between z 144 and 148. It had no hole: a long quad's cut has
    no vertex in the middle, and the chain simply has to be followed through it."""
    key = lambda p: (round(p[0] / tol), round(p[1] / tol))
    inc = {}
    for i, (a, b) in enumerate(segs):
        inc.setdefault(key(a), []).append(i)
        inc.setdefault(key(b), []).append(i)
    used = [False] * len(segs)
    out = []
    for i0 in range(len(segs)):
        if used[i0]:
            continue
        used[i0] = True
        a, b = segs[i0]
        path = [a, b]
        for grow_end in (True, False):
            cur = key(path[-1] if grow_end else path[0])
            while True:
                nxt = next((j for j in inc.get(cur, []) if not used[j]), None)
                if nxt is None:
                    break
                used[nxt] = True
                p, q = segs[nxt]
                far = q if key(p) == cur else p
                path.append(far) if grow_end else path.insert(0, far)
                cur = key(far)
                if cur == key(path[0] if grow_end else path[-1]):
                    break
        if len(path) >= 3:
            out.append(np.array(path))
    return out


def draw_section(parts, name, title, xlim=None, zlim=None, notes=(), figsize=(13, 10), y=None):
    """parts: [(triangles, facecolour, edgecolour, label)] - each cut at the plane y and filled."""
    y = SECTION_Y if y is None else y
    fig, ax = plt.subplots(figsize=figsize, dpi=110)
    handles = []
    for T, fc, ec, label in parts:
        first = True
        for lp in chains(slice_y(T, y)):
            ax.add_patch(MplPolygon(lp, closed=True, facecolor=fc, edgecolor=ec, linewidth=0.9, zorder=2))
            if first:
                handles.append(MplPolygon([(0, 0)], facecolor=fc, edgecolor=ec, label=label))
                first = False
    for (x, z), (tx, tz), text in notes:
        ax.annotate(text, xy=(x, z), xytext=(tx, tz), fontsize=10, zorder=5,
                    ha="left" if tx > x else "right", va="center",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.9),
                    arrowprops=dict(arrowstyle="-", lw=0.9, color="0.25",
                                    connectionstyle="arc3,rad=0.12"))
    ax.set_aspect("equal")
    if xlim:
        ax.set_xlim(*xlim)
    if zlim:
        ax.set_ylim(*zlim)
    else:
        ax.autoscale_view()
    x0, x1 = ax.get_xlim(); z0, z1 = ax.get_ylim()          # a 10 mm scale bar in the corner
    bx, bz = x0 + (x1 - x0) * 0.05, z0 + (z1 - z0) * 0.05
    ax.plot([bx, bx + 10], [bz, bz], color="0.2", lw=2.5, zorder=6)
    ax.text(bx + 5, bz + (z1 - z0) * 0.012, "10 mm", ha="center", va="bottom", fontsize=9, color="0.2")
    ax.set_axis_off()
    ax.set_title(title, fontsize=12, pad=6)
    ax.legend(handles=handles, loc="upper right", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(RDIR, name + ".png"), facecolor="white")
    plt.close(fig)
    print("wrote render/%s.png" % name)


def sections():
    body = R.load_stl(os.path.join(R.REPO, "cad", "reachy-mini", "reachy_mini_body.stl")).reshape(-1, 3, 3)
    board = R.board_in_robot().reshape(-1, 3, 3)
    parts = [(body, (0.90, 0.90, 0.88), (0.55, 0.55, 0.53), "Reachy's shell (Pollen CAD)"),
             (board, (0.14, 0.15, 0.20), (0.05, 0.05, 0.08), "CrowPanel"),
             (raw("tray-cradle"), (0.26, 0.40, 0.62), (0.13, 0.22, 0.38), "tray-cradle (ribs, collar)"),
             (raw("backstrap"), (0.26, 0.40, 0.62), (0.13, 0.22, 0.38), "backstrap"),
             (raw("bezel"), (0.19, 0.30, 0.48), (0.09, 0.16, 0.28), "bezel"),
             (raw("%s-left" % O.NAME), (0.93, 0.55, 0.20), (0.55, 0.30, 0.06), "bib strap")]
    ys, yf, yt = THROUGH_STRAP, THROUGH_FINGER, THROUGH_TONGUE
    xr, zr = O.rim(ys)
    ff = lambda z: O.back_x(z) - O.FINGER_G - O.FINGER_T / 2              # the finger blade's mid-line
    tongue = lambda y: (O.back_x(132.0) - O.FOOT_G - 2.0, 132.0)
    nub = lambda y: (O._nub(y)[0] + 0.3, O.NUB_Z)

    draw_section(
        parts, "overalls-section",
        "Bib strap in section, down the strap's centre (robot Y = %.1f): one closed loop from the rim hook\n"
        "over the robot's shoulder to the spring finger down behind the panel. %s" % (ys, MEASURED),
        xlim=(18, 118), zlim=(26, 196), y=ys,
        notes=[((xr, zr), (xr - 34, zr + 6), "rim hook: a 4.5 mm slot\nover a ~2 mm rim"),
               ((O.shell_x(ys, 160) + 2.6, 160.0), (30, 158), "shell run:\n1.5 mm off the body"),
               ((70.0, 148.0), (34, 136), "gap run: leans forward\ninto the gap behind the panel"),
               (tongue(ys), (102, 132), "TONGUE: fills the slot\nbetween two cradle ribs"),
               ((ff(100.0), 100.0), (34, 100), "spring FINGER, down into\nthe collar band's slot"),
               ((90.0, 80.0), (112, 72), "the bib's face is untouched")])

    draw_section(
        parts, "overalls-section-rim",
        "Rim hook: the C drops over the shell's top edge - %s measured at the closest point" % RIM_GAP,
        xlim=(38, 72), zlim=(162, 192), figsize=(11, 10), y=ys,
        notes=[((xr, zr), (xr - 14, zr + 7), "the shell's own rim"),
               ((xr - 4.0, zr - 2.0), (xr - 15, zr - 7), "reaches 3 mm\ndown inside"),
               ((O.shell_x(ys, 168) + 2.6, 168.0), (66, 166), "1.5 mm\noff the shell")])

    draw_section(
        parts, "overalls-section-foot",
        "The foot through the spring FINGER (Y = %.1f). Its nub is modelled %.1f mm into the collar band: the\n"
        "strap moves %.2f forward onto the tray's back wall and the rest bends the finger - so the strap is\n"
        "clamped between two faces of the tray-cradle. The overlap you see IS the preload." % (
            yf, O.FINGER_PRELOAD + O.FOOT_G, O.FOOT_G),
        xlim=(44, 110), zlim=(86, 146), figsize=(12, 11), y=yf,
        notes=[(tongue(yf), (95, 128), "tongue, %.2f mm off\nthe tray's back wall" % O.FOOT_G),
               ((ff(112.0), 112.0), (95, 114), "finger: %.2f thick, %.1f mm\nclear of the wall to bend into"
                % (O.FINGER_T, O.FINGER_G)),
               (nub(yf), (48, 96), "nub, pressing\nthe collar band"),
               ((O.back_x(94.0) - 1.0, 93.0), (95, 95), "45 deg lead-in on the tip\nand under the nub")])

    draw_section(
        parts, "overalls-section-tongue",
        "Inboard of the finger (Y = %.1f) there is no room for a spring - the band comes within ~1.4 mm of the\n"
        "tray's back wall - so the tongue stops %.1f mm above the band's top edge and cannot drop past it."
        % (yt, O.TONGUE_BOT - O.BAND_TOP),
        xlim=(44, 110), zlim=(100, 146), figsize=(12, 10), y=yt,
        notes=[(tongue(yt), (95, 128), "tongue, in the slot\nbetween the ribs"),
               ((O.back_x(O.TONGUE_BOT) - 3.0, O.TONGUE_BOT), (48, 132), "its flat bottom, just\nover the band's top edge"),
               ((O.back_x(112.0) - 3.0, 112.0), (48, 106), "the collar band")])


# --------------------------------------------------------------------------------- 3-D views
def cutaway(reachy, base, strap, y=THROUGH_FINGER):
    """The robot's left side with everything nearer than the plane Y = y taken away, so the foot
    shows in 3-D: from outside, the collar band hides it completely. Triangles are kept by centroid,
    so they are split small first (1.5 mm) to keep the cut edge clean; only the region around the
    strap is split, or the body alone would run to millions."""
    box = ((30.0, 112.0), (-10.0, y), (84.0, 196.0))

    def clip(T):
        c = T.mean(axis=1)
        m = ((c[:, 0] > box[0][0] - 10) & (c[:, 0] < box[0][1] + 10) & (c[:, 1] > box[1][0] - 10)
             & (c[:, 1] < y + 10) & (c[:, 2] > box[2][0] - 10) & (c[:, 2] < box[2][1] + 10))
        return R.subdivide(T[m], maxedge=1.5)

    lift = 18.0 * np.array([-O.D_BACK[0], 0.0, -O.D_BACK[1]])
    common = [(clip(reachy.reshape(-1, 3, 3)), R.REACHY), (clip(R.board_in_robot().reshape(-1, 3, 3)), R.BOARD),
              (clip(base["tray-cradle"]), R.DENIM), (clip(base["bezel"]), R.DENIM_DARK)]
    R.draw(common + [(clip(strap), CUT_STRAP)], "overalls-cutaway", 14, 70,
           "cut away at robot Y %.1f, seen from the robot's left: tongue behind the tray's back wall, finger's nub\n"
           "pressing the collar band (strap in orange)" % y, lims=box, zoom=1.0, light=(0.3, 0.9, 0.4))
    R.draw(common + [(clip(strap + lift), CUT_STRAP)], "overalls-cutaway-lifted", 14, 70,
           "the same cut, strap 18 mm up: it slides down along the tray's back wall, and the nub rides over the band's top edge",
           lims=box, zoom=1.0, light=(0.3, 0.9, 0.4))


def views():
    reachy = R.load_stl(os.path.join(R.REPO, "cad", "reachy-mini", "reachy_mini_body.stl"))
    base = {n: load(n) for n in ("bezel", "tray-cradle", "backstrap")}
    straps = [load("%s-%s" % (O.NAME, s)) for s in ("left", "right")]
    full = ([(reachy, R.REACHY), (R.board_in_robot(), R.BOARD), (base["tray-cradle"], R.DENIM),
             (base["backstrap"], R.DENIM), (base["bezel"], R.DENIM_DARK)]
            + [(s, STRAP) for s in straps])
    R.draw(full, "overalls-front", 8, 0, "bib straps: over the rim, down the shell, into the pocket behind the panel")
    R.draw(full, "overalls-hero", 20, 38, "bib straps - three-quarter")
    R.draw(full, "overalls-side", 6, 90, "bib straps - robot's left", light=(0.2, 0.9, 0.35))
    R.draw(full, "overalls-high", 34, 20, "bib straps - from above the shoulder")
    R.draw(full, "overalls-gap", 2, 62, "the gap behind the panel: shell run, lean-in, and the foot in its pocket",
           lims=((30.0, 110.0), (18.0, 60.0), (118.0, 190.0)), zoom=1.0, light=(0.25, 0.85, 0.4))
    lift = [(reachy, R.REACHY), (R.board_in_robot(), R.BOARD), (base["tray-cradle"], R.DENIM),
            (base["backstrap"], R.DENIM), (base["bezel"], R.DENIM_DARK),
            (straps[0] + 32.0 * np.array([-O.D_BACK[0], 0.0, -O.D_BACK[1]]), STRAP), (straps[1], STRAP)]
    R.draw(lift, "overalls-fitting", 14, 40, "fitting: the left strap lifted 32 mm out, along the panel's back face")
    cutaway(reachy, base, straps[0])
    for s in ("left", "right"):
        T = R.subdivide(R.load_stl(os.path.join(OUT, "print", "%s-%s-%s-print.stl" % (R.PRE, O.NAME, s))))
        R.draw([(T, STRAP)], "print-%s-%s" % (O.NAME, s), 32, -60, "bib strap %s - as printed (on the bed)" % s)


def main():
    os.makedirs(RDIR, exist_ok=True)
    sections()
    if "--section" not in sys.argv:
        views()
    print("wrote", RDIR)


if __name__ == "__main__":
    main()
