#!/usr/bin/env python3
"""Bib straps: the two shoulder straps of the dungarees, as separate clip-on prints.

    python overalls.py                 # -> out/step, out/stl, out/print
    python overalls.py --plain         # no edge stitching (faster, for shape work)
    python render_overalls.py          # renders on the dressed robot

Nothing here changes the three existing parts. Each strap is one print that hangs over the
robot's own front rim, runs down the outside of the shell, and drops into the gap BEHIND the
display, where a foot sits in a pocket the cradle already has. Nothing touches the bib's face:
from the front you see a strap coming over the robot's shoulder and disappearing behind the
panel, which is what a real pair of dungarees does.

  rim hook      a loose C over the shell's top edge. The slot is 4.5 mm over a ~2 mm rim, so it
                hangs rather than grips - a tight slot on a CAD-proxy rim would be a reprint, and
                the foot is what actually holds the strap.
  shell run     the strap's inner face follows the body's front surface with SHELL_CLR (1.5 mm),
                sampled per slice across the strap's width, so it stays parallel to a shell that
                falls away 4 mm across those 14 mm.
  gap run       leaves the shell at z 152 and leans forward into the 10-13 mm gap behind the panel.
  foot (v3)     a tongue filling the slot between the cradle's ribs, down the panel's back to the
                collar band's top edge, and a spring finger on down into the band slot whose nub
                presses the band - clamping the strap against the panel's back. See FOOT_* below.
                v2 (shoulders on the rib tops, a short tongue) located the strap but did not hold
                it: the printed pair needed hot glue.

v1 hooked over the bezel's top rear corner instead: a leg down the back face and a return along
the top surface. It worked, but it hung on one edge and put a tab on the panel's top surface. The
pocket between the ribs is a better anchor because it is a pocket - it locates the strap in all
three directions at once, and it was already there.

WHERE IT CAN GO, and why (measured, robot frame R; see README "Bib straps"):
  * The part spans |Y| 27.5..47.5. The FOOT is centred on 37.5, the centre of the slot between
    the ribs at 25 and 50; the STRAP is 14 wide and flush with the foot's OUTBOARD edge, centred
    on 40.5, for the printing reason at STRAP_C below.
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
# |Y| 37.5 is the centre of the pocket between the cradle's ribs at Y 25 and Y 50 (RIB_T 4.2, so
# the pocket runs 27.10..47.90). The foot drops into it. STRAP_Y is the FOOT's centre; the visible
# strap sits at STRAP_C.
STRAP_Y = 37.5
STRAP_W = 14.0                 # the visible strap's width
STRAP_T = lines(5)             # 2.10 thick, flat section (not the rounded cord of the first try)
SLICE = 1.0                    # spacing of the lofted slices across the width

SHELL_G = SHELL_CLR            # 1.50 to the body: the shell is Pollen's CAD mesh, not a measurement
Z_LEAVE = 152.0                # the strap leaves the shell here and leans into the gap
Z_RUN0 = 150.0                 # the shell run starts here (it overlaps the gap run by 2 mm)

RIM_SLOT = 4.5                 # the C's slot over the rim: deliberately loose on a ~2 mm rim
RIM_DN = 3.0                   # how far the return hangs down inside the rim
# (the hook's clearance ABOVE the rim is SHELL_G, the same 1.5 the run uses - there is no separate
# constant for it. There was one, RIM_G = 0.8, and nothing ever read it.)
RIM_T = lines(4)               # 1.68: the return is thinner than the strap, to stay out of the way
RIM_LAP = 8.0                  # how far down the shell the hook's outer leg reaches

SEAM = 0.10                    # how far one lofted piece sits inside the next where they overlap

# The FOOT (v3). v2 printed, and it had to be hot-glued in (2026-09-30): shoulders on the rib tops
# and a 6 mm tongue locate the strap, but nothing HOLDS it - there is no downward-facing ledge in
# that pocket to hook under, and a 3 g strap on a turning robot walks out. The owner drew the foot
# running on down the panel's back. v3 does that, and adds the one thing depth alone cannot: a
# spring.
#
# The pocket, measured (behind the panel's back face, between the ribs at |Y| 25 and 50, which
# leave a slot 27.10..47.90 wide):
#   above Z 124   6.7 mm deep at the inboard rib, 15.7 outboard - the shell is what is behind it
#   below Z 124   the collar band comes in: 1.3 mm deep inboard, 8.8 outboard, and waisted, its
#                 narrowest at about Z 108. Our own part, so exact, not a CAD proxy.
#
#   TONGUE   the full 20 mm between the ribs, down the panel's back to just above the band's top
#            edge. Its inboard half rests ON that edge; outboard the band is behind it, clear.
#   FINGER   a spring, down the panel's back into the band slot to Z 92, on the outboard half only -
#            inboard the slot is too shallow for it. A nub on its back presses the band; the
#            reaction pushes the whole strap forward until the tongue bears on the panel's back.
#            So the strap is clamped between two faces of the SAME part (the tray-cradle's band
#            and its back wall), and holds by friction.
#
# v2's shoulders are gone. They are what forced its tongue into a 45 deg wedge in the print (see
# STRAP_C): with them, the part could not start flush on the plate without a cantilever somewhere.
FOOT_W = 20.0                  # the tongue: 0.40 a side in the 20.80 slot (the ribs are ours, exact)
FOOT_D = 5.5                   # radial depth, CLAMPED per slice so the back never nears the shell
FOOT_G = FIT_SLIDE             # 0.40 off the panel's back face - the gap the spring closes
FOOT_DZ_TOP = 1.5              # top, in board z above OZ1: still under the panel's front top edge
TONGUE_BOT = BAND_TOP + FIT_SLIDE   # 124.4: 0.4 over the collar band's top edge, which it rests on
FOOT_LEADIN = 1.5              # chamfer on the tongue's bottom-front corner: finds the panel's back
TONGUE_BREAK = 0.4             # only an edge break bottom-back - that corner is the bearing face
EDGE_LEADIN = 0.8              # 45 deg on the bottom's ends in Y: finds the slot between the ribs

# The spring finger. PETG, E ~2 GPa (an estimate - no datasheet figure was checked). Numbers below
# are for the finger as modelled; the check measures the real interference against the exported
# tray-cradle and reports it.
FINGER_Y = (37.5, 47.5)        # |Y|. Inboard of 37.5 the band slot's waist is under 3.95 mm and the
                               # finger (FINGER_G + FINGER_T = 3.28 off the panel) would not clear it
FINGER_T = lines(4)            # 1.68: flexes front-to-back, which in this print is ALONG the layers
FINGER_G = 1.6                 # its front face off the panel's back: the room it deflects into
FINGER_TIP = 92.0              # robot Z of its tip: the nub's 45 deg lead-in needs room below it
NUB_Z = 104.0                  # robot Z of the nub's contact on the band, ~20 mm below the tongue
NUB_H = 2.0                    # height of the nub's flat contact face
NUB_UPPER = 70.0               # deg from horizontal, the nub's upper face: steep, so the nub stiffens
                               # only a short length of the finger. The lower face is 45 deg - it is
                               # the lead-in that rides over the band's top edge going in
FINGER_PRELOAD = 0.8           # how far the nub presses into the band, AFTER the strap has moved
                               # forward FOOT_G onto the panel (modelled interference 1.2). 0.6 was
                               # the first pick; against the tray-cradle as PRINTED (its STL, whose
                               # chords sit up to 0.28 inside the true surface at the nub) that left
                               # only 0.34, so it went up. check() reports both.

# The part prints as a prism extruded along Y (robot Y is the print's vertical), so every outline
# must start on the plate and only ever shrink going up - an outline that begins partway up is a
# floating cantilever (v2 learnt that twice from the slicer, and islands.py called both CLEAN). The
# finger only fits outboard, so the strap and the tongue are made FLUSH with the OUTBOARD edge and
# that edge goes down on the plate: strap, tongue and finger all start there; going up the finger
# ends, then the strap, then the tongue. The strap is centred on |Y| 40.5 as a result - 9 mm further
# out than v2's 31.5.
STRAP_C = STRAP_Y + FOOT_W / 2 - STRAP_W / 2     # 40.5

STITCH_IN, STITCH_W, STITCH_D = 2.2, lines(2), 0.5      # edge stitching, as on the backstrap's straps

# The panel's top rear corner and the board axes, in the robot XZ plane (all uniform across board
# x). bp() builds the foot in these, because every surface it meets is one of the panel's.
C_X, C_Z = (lambda p: (p[0], p[2]))(pt_robot((0.0, Y_BACK, OZ1)))
U_TOP = (lambda v: (v[0], v[2]))(rot_b_to_r((0, 1, 0)))       # forward along the panel's top surface
N_TOP = (lambda v: (v[0], v[2]))(rot_b_to_r((0, 0, 1)))       # out of the top surface, i.e. board +z
D_BACK = (lambda v: (v[0], v[2]))(rot_b_to_r((0, 0, -1)))     # down the back face


def _p(o, *terms):
    """o + sum(k * v) over (k, v) pairs, in the XZ plane."""
    x, z = o
    for k, v in terms:
        x, z = x + k * v[0], z + k * v[1]
    return (x, z)


def back_x(z):
    """Robot X of the panel's back face at height z. The face is the plane board y = Y_BACK, so
    it leans back with the display's 6 deg tilt: 0.105 mm of X per mm of Z."""
    return C_X + (C_Z - z) * (-D_BACK[0] / D_BACK[1])


def bp(dy, dz):
    """Robot XZ of the point dy forward and dz up from the panel's top rear corner, in the PANEL's
    own axes. The foot is built in these because every surface it meets is one of the panel's: the
    back face is board y constant, the ribs' top is board z constant."""
    return _p((C_X, C_Z), (dy, U_TOP), (dz, N_TOP))


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


# ------------------------------------------------------- the collar band's outer face (exact)
def _cut_y(T, y):
    """Segments (n, 2, 2) of [(x0, z0), (x1, z1)] where the plane Y = y cuts triangles T (n, 3, 3).
    Vectorised: the band's surface is tens of thousands of triangles."""
    T = T[(T[:, :, 1].min(1) <= y) & (T[:, :, 1].max(1) >= y)]
    if not len(T):
        return np.zeros((0, 2, 2))
    ends = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        ya, yb = T[:, a, 1], T[:, b, 1]
        ok = (ya != yb) & ((ya - y) * (yb - y) <= 0)
        f = np.where(ok, (y - ya) / np.where(ya != yb, yb - ya, 1.0), 0.0)
        p = T[:, a, :] + f[:, None] * (T[:, b, :] - T[:, a, :])
        ends.append((ok, p[:, [0, 2]]))
    segs = []
    for i in range(len(T)):
        pts = [p[i] for ok, p in ends if ok[i]]
        if len(pts) >= 2:
            segs.append(pts[:2])
    return np.array(segs)


def _cross_z(S, z):
    """X values where the cut S crosses the line Z = z."""
    if not len(S):
        return np.zeros(0)
    x0, z0, x1, z1 = S[:, 0, 0], S[:, 0, 1], S[:, 1, 0], S[:, 1, 1]
    m = (z0 - z) * (z1 - z) < 0
    return x0[m] + (z - z0[m]) / (z1[m] - z0[m]) * (x1[m] - x0[m])


@functools.lru_cache(maxsize=1)
def _band_solid():
    """The collar band's OUTER face: the shell proxy grown by SHELL_CLR + BAND_T. That is exactly
    how collar.band() makes it (proxy(outer) minus proxy(inner)), so this is the band's own surface,
    not a copy of an export - the build must not depend on a previous build's out/ files."""
    import collar
    return collar.proxy(SHELL_CLR + BAND_T).val()


@functools.lru_cache(maxsize=256)
def _band_cut(y_hundredths):
    """The band's outer face cut by the plane Y = y, as segments - by OCC section of the proxy
    solid, sampled along each edge. Tessellating the proxy instead gave 1,770 triangles over the
    whole region and put the face 0.27 mm off the export: a quarter of the entire preload."""
    y = y_hundredths / 100.0
    face = cq.Face.makePlane(600, 600, basePnt=cq.Vector(0, y, 90), dir=cq.Vector(0, 1, 0))
    sec = _band_solid().intersect(face)
    segs = []
    for e in sec.Edges():
        pts = [e.positionAt(t, mode="parameter") for t in np.linspace(0.0, 1.0, 600)]
        for p, q in zip(pts[:-1], pts[1:]):
            if max(p.x, q.x) > 30.0:
                segs.append([(p.x, p.z), (q.x, q.z)])
    return np.array(segs)


def band_x(y, z):
    """Robot X of the collar band's outer face at (y, z), on the front. Only meaningful at z up to
    BAND_TOP: the proxy carries on above it, the band does not."""
    xs = _cross_z(_band_cut(int(round(abs(y) * 100))), z)
    xs = xs[xs > 30.0]
    if not len(xs):
        raise ValueError("no band at y %.2f z %.2f" % (y, z))
    return float(xs.max())


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
    inset = 1.1                                               # ends strictly inside the foot
    return [(x_shell, Z_LEAVE),
            bp(-FOOT_G - inset - t, FOOT_DZ_TOP - inset),
            bp(-FOOT_G - inset, FOOT_DZ_TOP - inset),
            (x_out, Z_LEAVE)]


def _lift(y, lo, hi, inboard=True, outboard=True):
    """How far a bottom edge rises at |y| for a 45 deg lead-in over the last EDGE_LEADIN of [lo, hi].
    In the print this is a 45 deg growth, not an overhang: robot Y is the print's vertical."""
    a = abs(y)
    up = 0.0
    if inboard:
        up = max(up, (lo + EDGE_LEADIN) - a)
    if outboard:
        up = max(up, a - (hi - EDGE_LEADIN))
    return max(0.0, up)


def _tongue_depth(y, zb):
    """FOOT_D, clamped so the tongue's back face keeps SHELL_CLR from the body at every height it
    spans. Only the inboard end gets clamped (~4.8 mm there: the shell comes closest to the panel)."""
    zt = bp(-FOOT_G, FOOT_DZ_TOP)[1]
    room = min((back_x(z) - FOOT_G) - (shell_x(y, z) + SHELL_CLR)
               for z in (zb + (zt - zb) * i / 8.0 for i in range(9)))
    return max(2.5, min(FOOT_D, room))


def _tongue_profile(y):
    """The tongue: the full slot width between the ribs, down the panel's back face (FOOT_G off it,
    leaning with it) to TONGUE_BOT. Its bottom is horizontal so it beds flat on the band's top edge
    where the band lies under it (the inboard half); the bearing corner gets only an edge break."""
    zb = TONGUE_BOT + _lift(y, STRAP_Y - FOOT_W / 2, STRAP_Y + FOOT_W / 2)
    d = _tongue_depth(y, zb)
    xf = lambda z: back_x(z) - FOOT_G
    c, k = FOOT_LEADIN, TONGUE_BREAK
    return [bp(-FOOT_G, FOOT_DZ_TOP),                         # top, at the panel's back face
            (xf(zb + c), zb + c),                             # down the front face
            (xf(zb) - c, zb),                                 # chamfer onto the bottom
            (xf(zb) - d + k, zb),                             # across the bottom (bears on the band)
            (xf(zb + k) - d, zb + k),                         # edge break up the back
            bp(-FOOT_G - d, FOOT_DZ_TOP)]                     # up the back face


def _nub(y):
    """(face x, flat bottom z, flat top z, lower-ramp start z, upper-ramp end z) of the finger's nub.

    The nub's face is set into the band by FINGER_PRELOAD + FOOT_G: the spring's first job is to
    push the strap forward FOOT_G until the tongue bears on the panel, and what is left presses."""
    xfb = back_x(NUB_Z) - FINGER_G - FINGER_T
    xn = band_x(y, NUB_Z) - (FINGER_PRELOAD + FOOT_G)
    h = xfb - xn
    z0, z1 = NUB_Z - NUB_H / 2, NUB_Z + NUB_H / 2
    return xn, z0, z1, z0 - h, z1 + h / math.tan(math.radians(NUB_UPPER))


def _finger_profile(y):
    """The spring: a 4-line blade down the panel's back (FINGER_G off it, so it has room to bend),
    rooted 3 mm up inside the tongue, with a nub on its back pressing the band. The nub's height
    varies across the width because the band sweeps away from the panel as it follows the shell;
    the blade's does not, so every slice is the same spring with the same preload."""
    tip = FINGER_TIP + _lift(y, FINGER_Y[0], FINGER_Y[1], inboard=False)
    root = TONGUE_BOT + 3.0
    xff = lambda z: back_x(z) - FINGER_G
    xfb = lambda z: xff(z) - FINGER_T
    xn, z0, z1, zlo, zhi = _nub(y)
    c = 0.6
    if zlo < tip + c + 0.5 or zhi > root - 2.0:
        raise ValueError("nub at y %.2f runs from z %.2f to %.2f, outside the finger" % (y, zlo, zhi))
    return [(xff(root), root),                               # root, inside the tongue
            (xff(tip + c), tip + c),                          # down the front face
            (xff(tip) - c, tip),                              # tip
            (xfb(tip) + c, tip),
            (xfb(tip + c), tip + c),
            (xfb(zlo), zlo),                                  # up the back to the nub
            (xn, z0),                                         # 45 deg lead-in onto the band
            (xn, z1),                                         # the contact face
            (xfb(zhi), zhi),                                  # steep upper face back to the blade
            (xfb(root), root)]                                # up the back to the root


def _nub_profile(y):
    """A tool that takes the nub off, for the checks - it is MEANT to be into the band. Everything
    behind the blade from 0.5 below the nub to 0.5 above it, and 0.3 into the blade. A tool traced
    along the nub's own ramps left slivers of both ramps behind (0.72 mm3 read as interference)."""
    xn, z0, z1, zlo, zhi = _nub(y)
    xfb = lambda z: back_x(z) - FINGER_G - FINGER_T + 0.3
    a, b = zlo - 0.5, zhi + 0.5
    return [(xfb(a), a), (xn - 0.5, a), (xn - 0.5, b), (xfb(b), b)]


def _span(sy, lo, hi, inboard=True, outboard=True):
    """Y stations every SLICE across |Y| lo..hi, plus one EDGE_LEADIN in from each lifted end."""
    ds = set(np.round(np.linspace(lo, hi, int(round((hi - lo) / SLICE)) + 1), 4))
    if inboard:
        ds.add(round(lo + EDGE_LEADIN, 4))
    if outboard:
        ds.add(round(hi - EDGE_LEADIN, 4))
    return sorted(sy * d for d in ds)


def _tongue_slices(sy):
    return _span(sy, STRAP_Y - FOOT_W / 2, STRAP_Y + FOOT_W / 2)


def _finger_slices(sy):
    return _span(sy, FINGER_Y[0], FINGER_Y[1], inboard=False)


def _wire(pts, y):
    return cq.Workplane("XZ", origin=(0, y, 0)).polyline(pts).close().wires().val()


def _loft(profile, ys, ruled=True):
    """Ruled, always. A smooth (ruled=False) loft through the same slices builds without complaint
    and is valid, but every boolean against it returns a null shape - run.union(rim) came back with
    0 solids and 0 mm3. The faceting a ruled loft leaves is answered with more slices instead."""
    return cq.Workplane().add(cq.Solid.makeLoft([_wire(profile(y), y) for y in ys], ruled))


def _slices(sy, w=STRAP_W):
    """Y stations across a piece of width w. Every slice carries the same vertex count, so the
    ruled loft between them is clean; the long edges are left square (a 2D offset would round the
    corners of some profiles and not others, and the loft would not match up)."""
    a, b = sorted((sy * (STRAP_C - w / 2), sy * (STRAP_C + w / 2)))
    n = max(2, int(round((b - a) / SLICE)))
    return [a + (b - a) * i / n for i in range(n + 1)]


def build(sy=1, dressed=True):
    """One strap, robot frame. sy = +1 builds the robot's LEFT (+Y) side."""
    ys = _slices(sy)
    g, t = SHELL_G, STRAP_T
    part = _loft(lambda y: _run_profile(y, Z_RUN0, rim(y)[1] - RIM_LAP + 3.0, g, t), ys)
    part = part.union(_loft(lambda y: _rim_profile(y, g, t), ys))
    part = part.union(_loft(lambda y: _gap_profile(y, g, t), ys))
    part = part.union(_loft(_tongue_profile, _tongue_slices(sy)))
    part = part.union(_loft(_finger_profile, _finger_slices(sy)))
    if dressed:
        part = part.cut(_stitch(sy, ys, g, t))
    return part


def nub(sy=1):
    """The finger's nub on its own (robot frame), for the checks."""
    return _loft(_nub_profile, _finger_slices(sy))


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
        yc = sy * (STRAP_C + s * (STRAP_W / 2 - STITCH_IN))   # the STRAP's centre, not the foot's
        lo, hi = sorted((yc - STITCH_W / 2, yc + STITCH_W / 2))
        one = skins.intersect(box(-400, 400, lo, hi, 0, 400))
        tool = one if tool is None else tool.union(one)
    return tool


# --------------------------------------------------------------------------------- output
def to_bed(wp, sy=1):
    """On the plate the profile lies flat and robot Y is the print's vertical.

    sy turns each side so ITS OWN flush edge is down. Strap, tongue and finger are all flush with
    the OUTBOARD edge (see STRAP_C), which is max Y on the left and min Y on the right. rotate(+90)
    about X makes print z = robot Y, so the left turns -90 and the right +90; the other way round
    stands each on the tongue's inboard end, and the strap and the finger both start in mid-air."""
    p = wp.rotate((0, 0, 0), (1, 0, 0), -sy * 90)     # each side turned so ITS flush edge is down
    v, _ = p.val().tessellate(0.05, 0.2)
    xs, ys, zs = [q.x for q in v], [q.y for q in v], [q.z for q in v]
    return p.translate((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs)))


# ---------------------------------------------------------------------------- checks
def _overlap(a, b):
    try:
        return a.intersect(b).Volume()
    except Exception:
        return -1.0


def _section(solid, y):
    """The plane Y = y's exact OCC section of `solid`, as segments - the same method as _band_cut,
    on an export instead of the proxy. Cut once per Y and read at many Z: sectioning per point
    cost a whole-cradle boolean each time, and the check crawled."""
    face = cq.Face.makePlane(600, 600, basePnt=cq.Vector(0, y, 90), dir=cq.Vector(0, 1, 0))
    segs = []
    for e in solid.intersect(face).Edges():
        pts = [e.positionAt(t, mode="parameter") for t in np.linspace(0.0, 1.0, 800)]
        segs += [[(p.x, p.z), (q.x, q.z)] for p, q in zip(pts[:-1], pts[1:])]
    return np.array(segs)


def _stl_x(S, z):
    xs = _cross_z(S, z)
    xs = xs[(xs > 30.0) & (xs < back_x(z) - 0.05)]
    return float(xs.max()) if len(xs) else float("nan")


def _stl_tris(p):
    d = open(p, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    v = np.frombuffer(d, np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)["v"]
    return v.astype(float)


def check():
    """Solid booleans against the three existing parts and the shell, plus the two clearances that
    only the mesh can answer. Exit 1 on failure. Reads the STEP exports, so it runs beside
    check_mesh.py and islands.py without a rebuild."""
    import collar
    ok = True
    imp = cq.importers.importStep
    s = lambda n: imp(os.path.join(E.OUT, "step", "%s-%s.step" % (PRE, n)))
    straps = {side: s("%s-%s" % (NAME, side)) for side in ("left", "right")}
    signs = {"left": 1, "right": -1}
    # the existing parts, clipped to the region the straps ever occupy (fitted or on the way in):
    # every boolean below is then against a small piece rather than a 135 cm3 cradle
    # The bounds are deliberately off-grid. With whole numbers (Y -60..-18, Z 80..240) OCC returned
    # the right side's cradle clip EMPTY - 0.0 mm3 against 13,953 on the left - with no error, and
    # the right strap then "passed" every test against nothing. The guard below stops that recurring.
    region = lambda sy: box(21.3, 109.1, sy * 18.7, sy * 59.3, 85.1, 235.3).val()
    others = {side: {n: s(n).val().intersect(region(signs[side])) for n in ("bezel", "tray-cradle", "backstrap")}
              for side in straps}
    for side in straps:
        vs = {n: others[side][n].Volume() for n in ("bezel", "tray-cradle")}
        bad = min(vs.values()) < 1000.0
        print("  %-5s clipped for the checks: bezel %.0f mm3, tray-cradle %.0f mm3 %s"
              % (side, vs["bezel"], vs["tray-cradle"], "FAIL (a boolean came back empty)" if bad else "ok"))
        ok &= not bad
    # The nub is MEANT to be into the band - that is the spring's preload - so it comes off before
    # looking for interference, and is measured on its own below.
    bare = {side: straps[side].val().cut(nub(signs[side]).val()) for side in straps}
    print("bib straps: interference with the parts that are already on the robot (nub removed)")
    for side in straps:
        for n, o in others[side].items():
            v = _overlap(bare[side], o)
            bad = v > 0.05 or v < 0
            print("  %-5s vs %-12s overlap %7.3f mm3 %s" % (side, n, v, "FAIL" if bad else "ok"))
            ok &= not bad
    # ...and WITH the nub, which must be into the band on both sides. This is also what proves the
    # clipped parts above are not empty.
    for side in straps:
        v = _overlap(straps[side].val(), others[side]["tray-cradle"])
        bad = v < 5.0
        print("  %-5s nub into the collar band %7.3f mm3 (the preload) %s" % (side, v, "FAIL" if bad else "ok"))
        ok &= not bad

    # The spring, against the band twice: as DESIGNED (exact section of the exported STEP) and as
    # PRINTED (a cut of the exported STL - the slicer only ever sees the mesh, and its chords sit up
    # to 0.28 mm inside the true surface here: collar.py exports with cadquery's default RELATIVE
    # tolerance). interference = how far the nub's face sits inside the band's outer face; the strap
    # then moves forward FOOT_G onto the panel, so what presses is that minus FOOT_G.
    # bend = the most the finger has to bend on the way in, strap not yet moved forward: the nub
    # rides from the band's top edge down past the slot's waist (~Z 108) to where it sits.
    cradle = others["left"]["tray-cradle"]
    mesh =_stl_tris(os.path.join(E.OUT, "stl", "%s-tray-cradle.stl" % PRE))
    slope = -D_BACK[0] / D_BACK[1]            # the nub's X gains this per mm it moves down
    print("the spring, nub on the collar band - design (STEP) / as printed (STL):")
    worst_bend = 0.0
    zs = np.arange(NUB_Z, BAND_TOP - 0.2, 0.5)
    for y in _finger_slices(1):
        xn = _nub(y)[0]
        exact, cut = _section(cradle, y), _cut_y(mesh, y)
        at = {"step": lambda z: _stl_x(exact, z),
              "stl": lambda z: _stl_x(cut, z)}
        inter = {k: f(NUB_Z) - xn for k, f in at.items()}
        bend = max(f(z) - (xn - (z - NUB_Z) * slope) for f in at.values() for z in zs)
        worst_bend = max(worst_bend, bend)
        press = {k: v - FOOT_G for k, v in inter.items()}
        bad = min(press.values()) < 0.25 or bend > FINGER_G - 0.2
        print("  |Y| %4.1f  presses %4.2f / %4.2f mm once seated, bends %4.2f going in  %s"
              % (y, press["step"], press["stl"], bend, "FAIL" if bad else "ok"))
        ok &= not bad
    lever = TONGUE_BOT + 3.0 - NUB_Z
    print("  worst bend going in %.2f mm, of the %.2f in front of the finger: ~%.2f %% strain at the root"
          " (%.1f mm lever, %.2f thick)  %s"
          % (worst_bend, FINGER_G, 150.0 * FINGER_T * worst_bend / lever ** 2, lever, FINGER_T,
             "FAIL" if worst_bend > FINGER_G - 0.2 else "ok"))

    # Assembly path. The strap goes in, and comes out, along the panel's back face (it leans 6 deg,
    # so straight up would drive the tongue into it after ~4 mm). Everything but the nub, which is
    # meant to bend the finger, must clear everything at every step - the rim hook included.
    up = (-D_BACK[0], 0.0, -D_BACK[1])
    T = _body_tris()
    print("assembly path, out along the panel's back face (nub removed):")
    for side in straps:
        P0 = np.array([[p.x, p.y, p.z] for p in bare[side].tessellate(0.2, 0.3)[0]])
        Tn = T[((T.max(1) >= P0.min(0) - 60).all(1) & (T.min(1) <= P0.max(0) + 60).all(1))]
        for d in (1.0, 2.0, 4.0, 8.0, 14.0, 20.0, 28.0, 38.0, 50.0):
            m = bare[side].translate(cq.Vector(up[0] * d, 0, up[2] * d))
            vs = [_overlap(m, o) for o in others[side].values()]
            n_in = int(_inside(P0 + np.array(up) * d, Tn).sum())
            bad = any(v > 0.05 or v < 0 for v in vs) or n_in > 0
            print("  %-5s %4.0f mm: bezel %.3f  cradle %.3f  backstrap %.3f mm3, %d points in the shell wall  %s"
                  % (side, d, vs[0], vs[1], vs[2], n_in, "FAIL" if bad else "ok"))
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
        cq.exporters.export(to_bed(p, 1 if side == "left" else -1),
                            os.path.join(E.OUT, "print", "%s-%s-print.stl" % (PRE, n)),
                            tolerance=0.02, angularTolerance=0.1)
    print("written to", E.OUT)
    if args.check and not check():
        sys.exit(1)


if __name__ == "__main__":
    main()
