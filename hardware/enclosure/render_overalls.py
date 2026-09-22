#!/usr/bin/env python3
"""Renders of the bib straps on the dressed robot, and the sections that show how they fit.

    python render_overalls.py            # everything
    python render_overalls.py --section  # just the sections (fast: no 3-D painting)

Two kinds of picture, because they answer different questions:

  * The 3-D views (render.py's painter: STL triangles in one Poly3DCollection, no GPU) say what it
    LOOKS like. They read the three existing enclosure STLs unchanged and add the strap pair.
  * The SECTIONS say how it fits. Every part is cut by a plane and drawn as filled outlines, so the
    rim hook sitting on the shell's top edge, the 1.5 mm the run stands off the body and the foot's
    shoulder bedding on a rib top are visible as geometry rather than as a claim. A 3-D render of a
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

# Two cuts, because the foot is not the same shape all the way across. THROUGH_TONGUE runs down the
# strap's own centre and catches the tongue; THROUGH_SHOULDER is out on a shoulder, where the foot
# stops on a rib top - that one is the mount, and it is invisible in the other.
# Both are nudged 0.37 mm off a whole millimetre: the loft's slices sit on whole millimetres, so a
# cut exactly on one runs along a ring of shared edges, every edge comes back twice (once per
# adjoining triangle) and the section falls apart into dozens of two-segment scraps.
THROUGH_TONGUE = O.STRAP_C + 0.37
THROUGH_SHOULDER = O.STRAP_Y - O.FOOT_W / 2 - O.SHOULDER_W / 2 + 0.37     # 26.37, over the Y 25 rib
SECTION_Y = THROUGH_TONGUE


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
    yt, ysh = THROUGH_TONGUE, THROUGH_SHOULDER
    xr, zr = O.rim(yt)
    rib = O.bp(-2.0, O.FOOT_DZ_RIB)                                   # on the ribs' top plane
    tongue = O.bp(-3.0, O.FOOT_DZ_RIB - O.TONGUE_DROP + 1.0)

    draw_section(
        parts, "overalls-section",
        "Bib strap in section, cut down the strap's centre (robot Y = %.1f) - one closed loop, so it runs\n"
        "unbroken from the rim hook to the foot. Measured: 1.23 mm from the run to the shell, 0.66 mm at the\n"
        "rim hook, 0.40 mm off the panel's back." % yt,
        xlim=(18, 118), zlim=(26, 196), y=yt,
        notes=[((xr, zr), (xr - 34, zr + 6), "rim hook: a 4.5 mm slot\nover a ~2 mm rim"),
               ((O.shell_x(yt, 160) + 2.6, 160.0), (30, 158), "shell run:\n1.5 mm off the body"),
               ((70.0, 148.0), (34, 134), "gap run: leans forward\ninto the gap behind the panel"),
               (tongue, (102, 118), "the foot's TONGUE, in the slot\nbetween two of the cradle's ribs"),
               ((90.0, 100.0), (112, 92), "the bib's face is untouched")])

    draw_section(
        parts, "overalls-section-rim",
        "Rim hook: the C drops over the shell's top edge - 0.66 mm measured at the closest point",
        xlim=(38, 72), zlim=(162, 192), figsize=(11, 10), y=yt,
        notes=[((xr, zr), (xr - 14, zr + 7), "the shell's own rim"),
               ((xr - 4.0, zr - 2.0), (xr - 15, zr - 7), "reaches 3 mm\ndown inside"),
               ((O.shell_x(yt, 168) + 2.6, 168.0), (66, 166), "1.5 mm\noff the shell")])

    draw_section(
        parts, "overalls-section-foot",
        "The foot through the TONGUE (Y = %.1f): it hangs into the slot between the ribs, 0.40 mm off the\n"
        "panel's back, and stops short of the collar band - the ribs carry the strap, not the band." % yt,
        xlim=(56, 92), zlim=(116, 150), figsize=(12, 10), y=yt,
        notes=[(tongue, (59, 122), "tongue, in the slot"),
               ((O.back_x(134.0) - 0.2, 134.0), (86, 127), "0.40 mm off the\npanel's back face"),
               ((69.5, 124.5), (61, 145), "the collar band's top edge:\ndeliberately NOT touched")])

    draw_section(
        parts, "overalls-section-shoulder",
        "The mount, through a SHOULDER (Y = %.1f, over the rib at Y 25): it beds on the rib's own top edge.\n"
        "The tongue is not in this plane - it is inboard, hanging in the slot." % ysh,
        xlim=(56, 92), zlim=(116, 150), figsize=(12, 10), y=ysh,
        notes=[(rib, (59, 127), "shoulder resting on\nthe rib's top edge"),
               ((O.back_x(136.0) - 0.2, 136.0), (86, 126), "0.40 mm off the\npanel's back face"),
               ((O.shell_x(ysh, 130) + 1.0, 130.0), (61, 145), "the shell, behind")])


# --------------------------------------------------------------------------------- 3-D views
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
            (straps[0] + np.array([14.0, 0.0, 26.0]), STRAP), (straps[1], STRAP)]
    R.draw(lift, "overalls-fitting", 14, 40, "fitting: the left strap lifted out along the way it drops in")
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
