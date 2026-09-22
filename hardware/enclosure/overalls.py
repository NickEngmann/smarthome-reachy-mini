#!/usr/bin/env python3
"""Bib straps: the two shoulder straps of the dungarees, as separate clip-on prints.

    python overalls.py                 # -> out/step, out/stl, out/print
    python overalls.py --plain         # no edge stitching (faster, for shape work)
    python render_overalls.py          # renders on the dressed robot

Nothing here changes the three existing parts. Each strap is one print that hangs over the
robot's own front rim, runs down the outside of the shell, and tucks into the gap BEHIND the
display, where it hooks over the top rear edge of the bezel. Nothing touches the bib's face:
from the front you see a strap coming over the robot's shoulder and disappearing behind the
panel, which is what a real pair of dungarees does.

  rim hook      a loose C over the shell's top edge. The slot is 4.5 mm over a ~2 mm rim, so it
                hangs rather than grips - the strap is held down by gravity and located by the
                bezel hook, and a tight slot on a CAD-proxy rim would be a reprint.
  shell run     the strap's inner face follows the body's front surface with SHELL_CLR (1.5 mm),
                sampled per slice across the strap's width, so it stays parallel to a shell that
                falls away 4 mm across those 14 mm.
  gap run       leaves the shell at z 152 and leans forward into the 10-13 mm gap behind the panel.
  bezel hook    straddles the bezel's top rear corner: a leg down the back face and a return along
                the top surface, both 0.4 mm clear. Hidden from the front by the panel's own depth.

It is held down by gravity in the rim hook and located by the bezel hook, and in between it is
trapped in a gap 10-13 mm wide, so neither hook has to grip anything.

WHERE IT CAN GO, and why (measured, robot frame R; see README "Bib straps"):
  * |Y| 29..43. The cradle's ribs stand behind the display at robot |Y| 0, 25 and 50 (RIB_BX,
    4.2 wide) and reach up to Z 137.9, so the bezel hook's leg has to miss them; 29..43 clears
    the 22.9..27.1 rib by 1.9 mm and the 47.9..52.1 rib by 4.9. The collar tops out at Z 124 and
    is not in the way at all.
  * The microSD slot is not a constraint here: it opens through the bezel's top wall at board
    x 62..76 (robot |Y| 62..76), well outboard of the strap.
  * HEAD CLEARANCE. Above the front rim the whole robot stays inside robot X 41.5..43.2 (full
    mesh, z 185..196) while the rim itself is at X 53..55 - about 12 mm of clear space just
    inside it. The rim hook's return reaches X (rim - 5.4) and tops out ~2 mm above the rim, so
    it keeps 4.6 mm of radial clearance to the head in the URDF zero pose and never rises to the
    head's underside. That is Pollen's CAD, not a measured head sweep: check it on the robot
    before printing the second one.

Rejected on the way, so it is not re-tried: straps clipped to the FRONT of the bib and rising
above the display. The display's top corners sit 43 mm in front of the body, so a strap from
there either spans that gap as a strut or stops in mid-air; both were rendered and neither
read as a strap from the side. Straps hanging below the display have nowhere to go either -
the enclosure's cuff ends at z 30 and the robot's turning foot starts at z 22, and the foot does
not yaw with the body.
"""
import os, sys, math, struct, functools
import cadquery as cq
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geom import *          # noqa: F401,F403
import enclosure as E

REPO = os.path.dirname(os.path.dirname(HERE))
BODY_STL = os.path.join(REPO, "cad", "reachy-mini", "reachy_mini_body.stl")
PRE = "reachy-crowpanel"
NAME = "bib-strap"

# ------------------------------------------------------------------------ the strap (robot R)
STRAP_Y = 36.0                 # |Y| of the strap's centre: clear of the ribs at 25 and 50
STRAP_W = 14.0                 # width, so the slice range is |Y| 29..43
STRAP_T = lines(5)             # 2.10 thick, flat section (not the rounded cord of the first try)
SLICE = 1.0                    # spacing of the lofted slices across the width

SHELL_G = SHELL_CLR            # 1.50 to the body: the shell is Pollen's CAD mesh, not a measurement
Z_LEAVE = 152.0                # the strap leaves the shell here and leans into the gap
Z_RUN0 = 150.0                 # the shell run starts here (it overlaps the gap run by 2 mm)

RIM_SLOT = 4.5                 # the C's slot over the rim: deliberately loose on a ~2 mm rim
RIM_G = 0.8                    # clearance above the rim's top edge
RIM_DN = 3.0                   # how far the return hangs down inside the rim
RIM_T = lines(4)               # 1.68: the return is thinner than the strap, to stay out of the way
RIM_LAP = 8.0                  # how far down the shell the hook's outer leg reaches

SEAM = 0.10                    # how far one lofted piece sits inside the next where they overlap
BEZ_G = FIT_SLIDE              # 0.40 to the bezel
BEZ_LEG = 9.0                  # down the bezel's back face
BEZ_RET = 8.0                  # along the bezel's top surface (its top is 21.3 mm deep)

STITCH_IN, STITCH_W, STITCH_D = 2.2, lines(2), 0.5      # edge stitching, as on the backstrap's straps

# The bezel's top rear corner and the board axes, in the robot XZ plane (all uniform across board x)
C_X, C_Z = (lambda p: (p[0], p[2]))(pt_robot((0.0, Y_BACK, OZ1)))
U_TOP = (lambda v: (v[0], v[2]))(rot_b_to_r((0, 1, 0)))       # forward along the bezel's top surface
N_TOP = (lambda v: (v[0], v[2]))(rot_b_to_r((0, 0, 1)))       # out of the top surface
N_BACK = (lambda v: (v[0], v[2]))(rot_b_to_r((0, -1, 0)))     # out of the back face
D_BACK = (lambda v: (v[0], v[2]))(rot_b_to_r((0, 0, -1)))     # down the back face


def _p(o, *terms):
    """o + sum(k * v) over (k, v) pairs, in the XZ plane."""
    x, z = o
    for k, v in terms:
        x, z = x + k * v[0], z + k * v[1]
    return (x, z)


# ------------------------------------------------------- the body's front surface (local, mm)
@functools.lru_cache(maxsize=1)
def _body():
    d = open(BODY_STL, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    v = np.frombuffer(d, np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)["v"]
    return v.astype(float).reshape(-1, 3)


Z_GRID = np.arange(120.0, 196.0, 1.0)


@functools.lru_cache(maxsize=1)
def _front_tris():
    """Body triangles in the upper front region, for slicing."""
    T = _body_tris()
    return T[(T[:, :, 0].max(1) > 20.0) & (T[:, :, 2].max(1) > 110.0) & (np.abs(T[:, :, 1]).min(1) < 70.0)]


@functools.lru_cache(maxsize=64)
def _front(y_tenths):
    """(X(z) samples on Z_GRID, rim X, rim Z) for the body's front surface in the plane robot Y = y.

    Cut from the TRIANGLES, not sampled from vertices in a window. The window version (shell.py's
    approach, which is right for its 10 mm rings) has nothing to sample where the mesh is coarse:
    between z 167 and 173 at Y 30 there is not one vertex in a +-2.5 mm band, so it interpolated
    across the gap and read the surface 1.4 mm too far in. The strap then had 8 of its 2306 points
    inside the shell wall - found by the exact point-to-triangle check, invisible to the window."""
    y = y_tenths / 10.0
    T = _front_tris()
    T = T[(T[:, :, 1].min(1) <= y) & (T[:, :, 1].max(1) >= y)]
    x = np.full(len(Z_GRID), np.nan)
    zr, xr = -1e9, 0.0
    for tri in T:
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            ya, yb = tri[a, 1], tri[b, 1]
            if ya != yb and (ya - y) * (yb - y) <= 0:
                f = (y - ya) / (yb - ya)
                pts.append((tri[a, 0] + f * (tri[b, 0] - tri[a, 0]), tri[a, 2] + f * (tri[b, 2] - tri[a, 2])))
        if len(pts) < 2:
            continue
        (x0, z0), (x1, z1) = pts[0], pts[1]
        for px, pz in pts:                                    # the rim is the highest point on the cut
            if px > 20.0 and pz > zr:
                zr, xr = pz, px
        if z0 == z1:
            continue
        for i in np.where((Z_GRID >= min(z0, z1)) & (Z_GRID <= max(z0, z1)))[0]:
            xx = x0 + (Z_GRID[i] - z0) / (z1 - z0) * (x1 - x0)
            if xx > 20.0 and (np.isnan(x[i]) or xx > x[i]):
                x[i] = xx
    ok = ~np.isnan(x)
    x = np.interp(Z_GRID, Z_GRID[ok], x[ok])
    for i in range(len(x) - 2, -1, -1):                       # non-increasing with height
        x[i] = max(x[i], x[i + 1])
    return x, float(xr), float(zr)


def shell_x(y, z):
    """The body's outer X at (y, z), on the front."""
    x, _, _ = _front(int(round(abs(y) * 10)))
    return float(np.interp(z, Z_GRID, x))


def rim(y):
    """(X, Z) of the body's top edge in the plane robot Y = y."""
    _, xr, zr = _front(int(round(abs(y) * 10)))
    return xr, zr


# ------------------------------------------------------------------- profiles (robot XZ plane)
def _run_profile(y, z0, z1, g, t, n=24):
    """The shell run: a strip whose inner face is the shell + g, t thick, from z0 to z1.

    n is a FIXED sample count, not a step: z1 follows the rim, which drops 4.6 mm across the
    strap's width, and a step would give neighbouring slices different vertex counts - which is
    a `BRep_API: command not done` out of makeLoft and nothing more helpful."""
    zs = [z0 + (z1 - z0) * i / n for i in range(n + 1)]
    return [(shell_x(y, z) + g, z) for z in zs] + [(shell_x(y, z) + g + t, z) for z in reversed(zs)]


def _rim_face(y, z, g):
    """The hook's shell-side face over its lap: a straight taper from the shell run up to the rim.

    Started SEAM inside the run's own face, not level with it. The taper is a chord of the shell's
    curve, so it already lies at or inside the run everywhere on the lap - but at z = zb the two
    were exactly equal, and a union of two solids whose faces meet tangentially leaves sliver faces:
    6 degenerate triangles and 6 non-manifold edges, at this seam and at the gap run's top."""
    xr, zr = rim(y)
    zb = zr - RIM_LAP
    xb = shell_x(y, zb) - SEAM
    f = (z - zb) / (zr - zb)
    return xb + (xr - xb) * f + g


def _rim_profile(y, g, t):
    """The C over the body's top edge, with its legs tapering into the shell run."""
    xr, zr = rim(y)
    zb = zr - RIM_LAP
    zs = [zb + (zr - zb) * i / 4 for i in range(5)]
    top_o, top_i = zr + g, zr + g + RIM_T
    x_in = xr + g - RIM_SLOT                                  # the slot's inner wall
    return ([(_rim_face(y, z, g), z) for z in zs]             # up the shell-side face
            + [(x_in, top_o),                                 # across the rim's top, inward
               (x_in, zr - RIM_DN),                           # down inside the rim
               (x_in - RIM_T, zr - RIM_DN),                   # the return's tip
               (x_in - RIM_T, top_i),                         # up the return's outside
               (xr + g + t, top_i)]                           # across the hook's top
            + [(_rim_face(y, z, g + t), z) for z in reversed(zs)])


def _gap_profile(y, g, t):
    """From the shell at Z_LEAVE, leaning forward into the gap, onto the bezel's back face.

    The strap turns through ~45 deg here, so the two long edges have to be matched by WHICH FACE
    they are, not by their X: the shell-side face (smaller X above) becomes the face AWAY from the
    bezel (smaller X below). Pairing them by X instead gives a bow-tie."""
    # SEAM inside the run's faces at the top, for the same reason as _rim_face: the two solids
    # overlap from z 150 to 152 and must not share a face there.
    x_shell = shell_x(y, Z_LEAVE) + g + SEAM
    x_out = shell_x(y, Z_LEAVE) + g + t - SEAM
    on_back = _p((C_X, C_Z), (BEZ_G, N_BACK), (2.0, D_BACK))  # against the back face, 2 mm below the corner
    return [(x_shell, Z_LEAVE), _p(on_back, (t, N_BACK)), on_back, (x_out, Z_LEAVE)]


def _bezel_profile(g, t):
    """Straddles the bezel's top rear corner: a leg down the back face and a return along the top
    surface, both g clear. U_TOP = -N_BACK and D_BACK = -N_TOP, so the two faces are orthogonal
    and the offset corners are just ci = C + g(N_BACK + N_TOP), co = ci + t(N_BACK + N_TOP)."""
    ci = _p((C_X, C_Z), (g, N_BACK), (g, N_TOP))
    co = _p(ci, (t, N_BACK), (t, N_TOP))
    return [_p(ci, (BEZ_LEG, D_BACK)),                        # leg tip, on the back face
            ci,                                               # up to the inner corner
            _p(ci, (BEZ_RET, U_TOP)),                         # forward along the top surface
            _p(ci, (BEZ_RET, U_TOP), (t, N_TOP)),             # across the return's tip
            co,                                               # back to the outer corner
            _p(co, (BEZ_LEG + t, D_BACK))]                    # down the leg's outer face


def _wire(pts, y):
    return cq.Workplane("XZ", origin=(0, y, 0)).polyline(pts).close().wires().val()


def _loft(profile, ys, ruled=True):
    """Ruled, always. A smooth (ruled=False) loft through the same slices builds without complaint
    and is valid, but every boolean against it returns a null shape - run.union(rim) came back with
    0 solids and 0 mm3. The faceting a ruled loft leaves is answered with more slices instead."""
    return cq.Workplane().add(cq.Solid.makeLoft([_wire(profile(y), y) for y in ys], ruled))


def _slices(sy):
    """Y stations across the strap. Every slice carries the same vertex count, so the ruled loft
    between them is clean; the long edges are left square (a 2D offset would round the corners of
    some profiles and not others, and the loft would not match up)."""
    a, b = sorted((sy * (STRAP_Y - STRAP_W / 2), sy * (STRAP_Y + STRAP_W / 2)))
    n = max(2, int(round((b - a) / SLICE)))
    return [a + (b - a) * i / n for i in range(n + 1)]


def build(sy=1, dressed=True):
    """One strap, robot frame. sy = +1 builds the robot's LEFT (+Y) side."""
    ys = _slices(sy)
    g, t = SHELL_G, STRAP_T
    part = _loft(lambda y: _run_profile(y, Z_RUN0, rim(y)[1] - RIM_LAP + 3.0, g, t), ys)
    part = part.union(_loft(lambda y: _rim_profile(y, g, t), ys))
    part = part.union(_loft(lambda y: _gap_profile(y, g, t), ys))
    part = part.union(_loft(lambda y: _bezel_profile(BEZ_G, t), ys))
    if dressed:
        part = part.cut(_stitch(sy, ys, g, t))
    return part


def _stitch(sy, ys, g, t):
    """Two grooves STITCH_IN in from each long edge, STITCH_D deep, on both faces of the run.

    The skins are lofted over the SAME Y stations as the part and then clipped to each groove's
    width with a plane. Lofting the tool over just the groove's own two stations instead left the
    tool's surface ruled differently from the part's (which has a crease at every station), and the
    boolean came back with four non-manifold edges on the outer groove's floor - valid to OCC,
    4 open edges to check_mesh.py."""
    top = lambda y: rim(y)[1] - 2.0
    outer = _loft(lambda y: _run_profile(y, Z_RUN0 - 6.0, top(y), g - STITCH_D, t + 2 * STITCH_D), ys)
    inner = _loft(lambda y: _run_profile(y, Z_RUN0 - 8.0, top(y) + 2.0, g + STITCH_D, t - 2 * STITCH_D), ys)
    skins = outer.cut(inner)
    tool = None
    for s in (-1, 1):
        yc = sy * (STRAP_Y + s * (STRAP_W / 2 - STITCH_IN))
        lo, hi = sorted((yc - STITCH_W / 2, yc + STITCH_W / 2))
        one = skins.intersect(box(-400, 400, lo, hi, 0, 400))
        tool = one if tool is None else tool.union(one)
    return tool


# --------------------------------------------------------------------------------- output
def to_bed(wp):
    """On the plate the profile lies flat and the strap's width is the print Z.

    That is nearly a prism, but not quite: the shell falls away 4 mm across the strap's 14 mm and
    the rim drops 5.3 mm, so the layers do shift. Measured on the export - 73-77 mm2 of face over
    45 deg, and short bridges of 4-7 mm where the hook bights lie. Bambu Studio slices it with no
    support and no warning (28 min, 5.5 g the pair), so the bridges are within what PETG spans."""
    p = wp.rotate((0, 0, 0), (1, 0, 0), 90)
    v, _ = p.val().tessellate(0.05, 0.2)
    xs, ys, zs = [q.x for q in v], [q.y for q in v], [q.z for q in v]
    return p.translate((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs)))


# ---------------------------------------------------------------------------- checks
def _overlap(a, b):
    try:
        return a.intersect(b).Volume()
    except Exception:
        return -1.0


def check():
    """Solid booleans against the three existing parts and the shell, plus the two clearances that
    only the mesh can answer. Exit 1 on failure. Reads the STEP exports, so it runs beside
    check_mesh.py and islands.py without a rebuild."""
    import collar
    ok = True
    imp = cq.importers.importStep
    s = lambda n: imp(os.path.join(E.OUT, "step", "%s-%s.step" % (PRE, n)))
    straps = {side: s("%s-%s" % (NAME, side)) for side in ("left", "right")}
    others = {n: s(n) for n in ("bezel", "tray-cradle", "backstrap")}
    print("bib straps: interference with the parts that are already on the robot")
    for side, strap in straps.items():
        for n, o in others.items():
            v = _overlap(strap.val(), o.val())
            bad = v > 0.05 or v < 0
            print("  %-5s vs %-12s overlap %7.3f mm3 %s" % (side, n, v, "FAIL" if bad else "ok"))
            ok &= not bad
    # The shell proxy's rings stop at z 140 (shell.py) and are copied up to 150, so it is only
    # trustworthy below the display's top edge. Above that the mesh answers, further down.
    shell0 = collar.proxy(0.0).val()
    lo = box(-400, 400, -400, 400, 0, 139.0).val()
    for side, strap in straps.items():
        part = strap.val().intersect(lo)
        v = _overlap(part, shell0) if part.Volume() > 1e-6 else 0.0
        bad = v > 0.05 or v < 0
        print("  %-5s below z 139 vs the shell proxy: %7.3f mm3 %s" % (side, v, "FAIL" if bad else "ok"))
        ok &= not bad
    # Above the display the proxy does not reach, so measure against the mesh itself - point to
    # TRIANGLE, not point to vertex in an angular window. The window version read -1.13 mm on a
    # strap point at Y 30.0 by comparing it with a body vertex at Y 32.5: +-3 deg is 3.4 mm of arc
    # out here, which is wider than the strap's own curvature, and the body bulges across it.
    S = np.array([[p.x, p.y, p.z] for p in straps["left"].val().tessellate(0.1, 0.3)[0]])
    T = _body_tris()
    bb = (S.min(0) - 8.0, S.max(0) + 8.0)
    near = ((T.max(1) >= bb[0]).all(1) & (T.min(1) <= bb[1]).all(1))
    T = T[near]
    print("  measuring against %d body triangles around the strap" % len(T))
    # "inside" means inside the shell's WALL material: reachy_mini_body.stl is a shell about 2.7 mm
    # thick (checked at z 80: outer 77.2, inner 74.5), not a solid. That is the right test for a
    # collision, and it is also why the rim hook's return reads a positive distance - it hangs in
    # the cavity behind the rim, where there is no material, and its number is the gap to the rim's
    # inner face.
    for lab, z0, z1, floor, want in (
            ("run, z 139..172", 139.0, 172.0, 0.20, "gap to the shell's outer face"),
            ("rim hook, z 172..190", 172.0, 190.0, 0.10, "gap to the rim, inside and out")):
        P = S[(S[:, 2] >= z0) & (S[:, 2] < z1)]
        if not len(P):
            continue
        d = _dist_to_tris(P, T)
        inside = _inside(P, T)
        n_in = int(inside.sum())
        i = np.where(inside, -d, d).argmin()
        bad = n_in > 0 or d.min() < floor
        print("  %-22s min %5.2f mm at X %5.1f Y %5.1f Z %6.1f, %d of %d points in the wall  %s  (%s)"
              % (lab, d.min(), P[i, 0], P[i, 1], P[i, 2], n_in, len(P), "FAIL" if bad else "ok", want))
        ok &= not bad
    # head: everything in the full robot above the rim and inboard of the rim's own X
    F = _body_full()
    H = F[(F[:, 2] > 184.0) & (F[:, 0] < 46.0) & (F[:, 1] > 5) & (F[:, 1] < 65)][::4]
    Sh = S[S[:, 2] > 170.0]
    d = np.sqrt(((Sh[:, None, :] - H[None, :, :]) ** 2).sum(-1)).min() if len(H) and len(Sh) else float("nan")
    print("  rim hook vs the head region (full mesh above z 184, inboard of X 46): %.2f mm" % d)
    print("    URDF zero pose only - Pollen's CAD, not a head sweep. Check it on the robot.")
    print("BIB STRAP CHECK " + ("PASSED" if ok else "FAILED"))
    return ok


@functools.lru_cache(maxsize=1)
def _body_tris():
    """The body mesh as (n, 3, 3) triangles."""
    return _body().reshape(-1, 3, 3)


def _dist_to_tris(P, T, chunk=192):
    """Min distance from each point in P to the triangle soup T.

    Written as: the perpendicular distance where the foot lands inside the triangle, and the
    distance to each of the three edges otherwise - two easy things instead of one seven-region
    case analysis. Chunked over P so the (points x triangles) array stays a sensible size."""
    A, B_, C = T[:, 0], T[:, 1], T[:, 2]
    e0, e1 = B_ - A, C - A
    n = np.cross(e0, e1)
    nn = np.maximum((n * n).sum(1), 1e-20)
    a, b, c = (e0 * e0).sum(1), (e0 * e1).sum(1), (e1 * e1).sum(1)
    det = np.maximum(a * c - b * b, 1e-20)
    seg = [(A, e0), (A, e1), (B_, C - B_)]
    seg = [(p0, v, np.maximum((v * v).sum(1), 1e-20)) for p0, v in seg]
    out = np.empty(len(P))
    for i in range(0, len(P), chunk):
        Q = P[i:i + chunk][:, None, :]                            # (q, 1, 3)
        w = Q - A[None]
        # foot of the perpendicular, in barycentric coordinates
        d0, d1 = (w * e0[None]).sum(2), (w * e1[None]).sum(2)
        s = (c * d0 - b * d1) / det
        t = (a * d1 - b * d0) / det
        face = (s >= 0) & (t >= 0) & ((s + t) <= 1)
        perp = np.abs((w * n[None]).sum(2)) / np.sqrt(nn)
        best = np.where(face, perp, np.inf)
        for p0, v, vv in seg:                                     # distance to each edge
            u = np.clip(((Q - p0[None]) * v[None]).sum(2) / vv, 0.0, 1.0)
            cl = p0[None] + u[:, :, None] * v[None]
            best = np.minimum(best, np.sqrt(((cl - Q) ** 2).sum(2)))
        out[i:i + chunk] = best.min(1)
    return out


def _inside(P, T, chunk=256):
    """Odd-crossing test against the triangle soup (the body mesh is closed).

    The ray is deliberately NOT axis-aligned: straight +X from a point inside a box leaves along
    the diagonal that two triangles share, counts two hits and calls the point outside. A skewed
    direction cannot land on an edge of this mesh."""
    A, B_, C = T[:, 0], T[:, 1], T[:, 2]
    e1, e2 = B_ - A, C - A
    d = np.array([1.0, 0.0173, 0.0131])
    d = d / np.sqrt((d * d).sum())
    h = np.cross(d, e2); det = (e1 * h).sum(1)
    par = np.abs(det) < 1e-12
    inv = 1.0 / np.where(par, 1.0, det)
    out = np.zeros(len(P), dtype=bool)
    for i in range(0, len(P), chunk):
        Q = P[i:i + chunk]
        s = Q[:, None] - A[None]
        u = (s * h[None]).sum(2) * inv
        q = np.cross(s, e1[None])
        v = (q * d).sum(2) * inv
        tt = (e2[None] * q).sum(2) * inv
        hit = (~par[None]) & (u >= 0) & (u <= 1) & (v >= 0) & ((u + v) <= 1) & (tt > 1e-9)
        out[i:i + chunk] = (hit.sum(1) % 2) == 1
    return out


@functools.lru_cache(maxsize=1)
def _body_full():
    p = os.path.join(REPO, "cad", "reachy-mini", "reachy_mini_full.stl")
    d = open(p, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    v = np.frombuffer(d, np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)["v"]
    return v.astype(float).reshape(-1, 3)


def report(name, wp):
    val = wp.val()
    bb = val.BoundingBox()
    print("%-22s valid=%s solids=%d vol %5.2f cm3  x %6.1f..%6.1f  y %6.1f..%6.1f  z %6.1f..%6.1f" % (
        name, val.isValid(), len(wp.solids().vals()), val.Volume() / 1000,
        bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--plain", action="store_true", help="no edge stitching (faster, for shape work)")
    ap.add_argument("--check", action="store_true", help="build, export, then run the fit checks")
    ap.add_argument("--check-only", action="store_true", help="fit checks on the last build's STEP exports")
    args = ap.parse_args(argv)
    if args.check_only:
        sys.exit(0 if check() else 1)
    for d in ("step", "stl", "print"):
        os.makedirs(os.path.join(E.OUT, d), exist_ok=True)
    # The right strap is the left one mirrored, not a second build. Every profile here reads the
    # shell through abs(y), so the two sides are identical by construction - and building the -Y
    # side directly lofts its slices in the opposite order, which OCC's union().clean() rejected
    # with "Courbes non jointives" while the +Y side built cleanly.
    left = build(1, not args.plain)
    for side, p in (("left", left), ("right", left.mirror("XZ"))):
        n = "%s-%s" % (NAME, side)
        report(n, p)
        cq.exporters.export(p, os.path.join(E.OUT, "step", "%s-%s.step" % (PRE, n)))
        cq.exporters.export(p, os.path.join(E.OUT, "stl", "%s-%s.stl" % (PRE, n)), tolerance=0.02, angularTolerance=0.1)
        cq.exporters.export(to_bed(p), os.path.join(E.OUT, "print", "%s-%s-print.stl" % (PRE, n)),
                            tolerance=0.02, angularTolerance=0.1)
    print("written to", E.OUT)
    if args.check and not check():
        sys.exit(1)


if __name__ == "__main__":
    main()
