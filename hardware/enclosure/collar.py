#!/usr/bin/env python3
"""The parts that meet Reachy (robot frame R): cradle ribs, the two halves of the waistband
collar, the side joints, the spring tabs, the cable gutter - plus export and checks for all
three prints. Run through enclosure.py.

Why it holds (see README "Load"):
  * The collar runs from z 30 to z 124, across the belly's widest ring (z ~60, r 77.4) and well
    above it (r 74.3 at z 120): it cannot slide down past the bulge, nor up past the lower taper.
  * Each side joint is full height: a tongue on the backstrap lies over a strip on the front half
    and two vertical flex tabs hook into windows in the strip (lift a tab by its lip to release).
    Every surface of the joint is extruded along x, so the backstrap slides on along x.
    Tab: 10 wide, 2.1 thick, 22 long, 0.6 deflection -> strain 0.39 %, ~2.6 N per tab (PETG).
  * Three spring tabs in the backstrap press nubs onto the shell: the backstrap is pushed back, the
    joint hooks pull the front half back, the ribs are pulled onto the belly. The nubs reach 1.2 mm
    plus the play the collar loses as it seats, so ~1.2 mm of preload remains and the collar's
    1.5 mm clearance never turns into rattle.
"""
import os, sys, math, functools
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geom import *          # noqa: F401,F403
import shell
import enclosure as E


@functools.lru_cache(maxsize=1)
def prof():
    return shell.profile()


@functools.lru_cache(maxsize=None)
def _proxy(key):
    return shell.build_proxy(key / 1000.0, prof())


def proxy(offset):
    """The shell grown by `offset` mm, cached per offset."""
    return cq.Workplane().add(_proxy(int(round(offset * 1000))))


def layer(tool, a, b):
    """The part of `tool` lying between shell offsets a and b (a thin skin following the shell)."""
    return tool.intersect(proxy(b)).cut(proxy(a))


def z_bed():
    return Z_BED_TARGET


def side_r(z):
    return shell.radius_at(prof(), z, 90.0)


def behind_plate(z_lo=None, z_hi=None, y_lim=Y_BACK + 1.0):
    """Half-space behind the tray (default B y <= Y_BACK + 1: 1 mm into the floor), in R."""
    b = box(-400, 400, -400, y_lim, OZ0 if z_lo is None else z_lo, (CZ1 - TOP_SEAM_CLR) if z_hi is None else z_hi)
    return to_robot(b)


def band(offset_in, offset_out, x0, x1, z0, z1):
    return layer(box(x0, x1, -300, 300, z0, z1), offset_in, offset_out)


def side_skin(a, b, x0, x1, z0=None, z1=None, step=2.0):
    """+Y side: the region side_r(z)+a <= y <= side_r(z)+b, extruded along x from x0 to x1."""
    z0 = z_bed() if z0 is None else z0
    z1 = BAND_TOP if z1 is None else z1
    n = max(2, int(math.ceil((z1 - z0) / step)))
    zs = [z0 + (z1 - z0) * i / n for i in range(n + 1)]
    pts = [(side_r(z) + b, z) for z in zs] + [(side_r(z) + a, z) for z in reversed(zs)]
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)


def both_sides(wp):
    return wp.union(wp.mirror("XZ"))


# ------------------------------------------------------------------- side joint (+Y)
# The rail-and-pin slide lock (geom.py, "side joint"). Everything below is +Y and mirrored.
A_STRIP = SHELL_CLR + STRIP_MARGIN                 # plate inner face offset from the shell side (1.9)
B_STRIP = A_STRIP + STRIP_T                        # plate outer face (4.0)
A_TONGUE = B_STRIP + JOINT_GAP                     # tongue inner face (4.4)
B_TONGUE = A_TONGUE + TONGUE_T                     # tongue outer face (7.34)


def _flank_prism(zc, u_lo, h, half_w, x0, x1, step=0.4):
    """A (radial, z) outline extruded along x: from shell offset u_lo out to B_STRIP + h(dz), for
    |dz| <= half_w, following side_r(z) - so it rides the plate's own curve, and a rail and its
    groove share it exactly."""
    n = max(4, int(math.ceil(2 * half_w / step)))
    zs = [zc - half_w + 2 * half_w * i / n for i in range(n + 1)]
    pts = [(side_r(z) + B_STRIP + h(z - zc), z) for z in zs] + [(side_r(z) + u_lo, z) for z in reversed(zs)]
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)


def _rail_h(dz):
    """Rail height (radial) at dz from its centre: RAIL_H on top, flanks 1 : RAIL_K to the root."""
    return max(0.0, min(RAIL_H, (RAIL_W / 2 - abs(dz)) * RAIL_K))


# Groove clearance: FIT_JOINT normal to every face. On a 1 : RAIL_K flank that is a z shift of
# FIT_JOINT * sqrt(1 + K^2) / K; on the rail's top, FIT_JOINT radially.
_GZ = FIT_JOINT * math.sqrt(1 + RAIL_K ** 2) / RAIL_K


def _groove_h(dz):
    return max(0.05, min(RAIL_H + FIT_JOINT, (RAIL_W / 2 + _GZ - abs(dz)) * RAIL_K))


def rail(zc):
    """A trapezoid rail on the plate's outer face, narrower at its tip. Both flanks lean in, so both
    print on what is below them: the lower flank grows out from the plate at 49.6 deg and the upper
    one is a top. (A dovetail would hook, but its groove's roof would then start at the tongue's
    face with nothing under it - a floating sliver along the whole groove.) Its rear end narrows at
    45 deg in x, so it enters the groove's mouth thin."""
    x0, x1 = STRIP_X
    r = _flank_prism(zc, B_STRIP - 0.3, _rail_h, RAIL_W / 2, x0, x1)
    L, top, bot = RAIL_LEADIN, zc + RAIL_W / 2 + 0.1, zc - RAIL_W / 2 - 0.1
    for tri in ([(x0 - 0.1, top), (x0 + L, top), (x0 - 0.1, top - L - 0.1)],
                [(x0 - 0.1, bot), (x0 + L, bot), (x0 - 0.1, bot + L + 0.1)]):
        r = r.cut(cq.Workplane("XZ", origin=(0, 200, 0)).polyline(tri).close().extrude(400))
    return r


def groove(zc):
    """The rail's groove in the tongue's inner face: the rail grown by FIT_JOINT on every face, from
    GROOVE_REAR out through the tongue's front edge. Its roof comes down toward the groove's depth,
    so the tongue above it grows out from the solid behind the groove. The mouth flares FUNNEL up
    and down at 45 deg (a 45 deg underside, supported from behind)."""
    x1 = TONGUE_X[1] + 1.0
    g = _flank_prism(zc, B_STRIP + 0.05, _groove_h, RAIL_W / 2 + _GZ - 0.06, GROOVE_REAR, x1)
    hw = RAIL_W / 2 + _GZ - (A_TONGUE - B_STRIP) / RAIL_K          # the groove's half-width at the tongue face
    u0, u1 = side_r(zc) + B_STRIP + 0.05, side_r(zc) + B_STRIP + RAIL_H + FIT_JOINT
    xm, F = TONGUE_X[1], FUNNEL
    for s in (1, -1):
        e = zc + s * hw
        tri = [(xm - F, e - s * 0.2), (x1, e - s * 0.2), (x1, e + s * (F + 1.0))]
        g = g.union(cq.Workplane("XZ", origin=(0, u1, 0)).polyline(tri).close().extrude(u1 - u0))
    return g


def _top_y():
    """Radial layout of the pin block, in robot y (constant up the block, which stands above the
    band where the tongue and plate no longer follow the shell):
      yp   the plate's outer face just above the band - the cap's underside starts there
      ypin the pin's axis: PIN_WALL + the hole's radius outside the tongue's inner face, everywhere
           the hole runs down the tongue
      ybo  the boss's and the cap's outer face
      ybi  the boss's inner edge: inside the tongue at every z of the boss (0.3 in from its inner
           face at the widest z)."""
    zt = BAND_TOP
    yp = side_r(zt + FIT_Z) + B_STRIP
    r = PIN_HOLE / 2
    span = [PIN_Z0 - 4.0 + i * 0.5 for i in range(int((zt - PIN_Z0 + 4.0) / 0.5) + 1)]
    ypin = max(side_r(z) for z in span) + A_TONGUE + PIN_WALL + r
    ybo = ypin + r + PIN_WALL
    ybi = max(side_r(z) for z in span) + A_TONGUE + 0.3
    assert ybi < min(side_r(z) for z in span) + B_TONGUE - 0.3, "the boss's inner edge leaves the tongue"
    return yp, ypin, ybo, ybi


def _pin_x():
    h = PIN_HOLE / 2 + PIN_WALL + 1.0
    return PIN_X - h, PIN_X + h


def _cap_top():
    yp, ypin, ybo, ybi = _top_y()
    return BAND_TOP + FIT_Z + (ybo - yp) + lines(6)                  # 2.5 of cap over its outer edge


def cap():
    """On the tray-cradle: the plate carried up past the band, and a cap reaching out over the
    tongue's boss. Its underside rises outward at 45 deg from the plate's face (it prints from the
    plate); the boss's top follows it FIT_JOINT below, so the boss slides in under it along x."""
    yp, ypin, ybo, ybi = _top_y()
    x0, x1 = _pin_x()
    ztop = _cap_top()
    lo = BAND_TOP + FIT_Z
    # the inner edge runs down the middle of the plate, which leans in with the shell above the band
    # (side_r falls 2.2 mm from z 124 to 137, more than the plate is thick). A straight edge left a
    # 1.7 mm flat overhang inside the plate, 0.2 mm off the shell.
    n = 8
    inner = [(side_r(lo + (ztop - lo) * i / n) + (A_STRIP + B_STRIP) / 2, lo + (ztop - lo) * i / n) for i in range(n + 1)]
    pts = [(yp, lo), (ybo, lo + (ybo - yp)), (ybo, ztop)] + inner[::-1]
    c = cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)
    return c.union(side_skin(A_STRIP, B_STRIP, x0, x1, BAND_TOP - 1.0, ztop))


def boss():
    """On the backstrap's tongue: the block the pin goes down into. Its top is the cap's underside
    less FIT_JOINT (normal to the 45 deg face), its underside a 45 deg chamfer up from the tongue.
    The hole's floor is 1.5 below PIN_Z0 at its outer edge."""
    yp, ypin, ybo, ybi = _top_y()
    x0, x1 = _pin_x()
    top = lambda y: BAND_TOP + FIT_Z - FIT_JOINT * math.sqrt(2) + (y - yp)
    zb = PIN_Z0 - 1.5 - (ypin + PIN_HOLE / 2 - ybi)
    pts = [(ybi, zb), (ybo, zb + (ybo - ybi)), (ybo, top(ybo)), (ybi, top(ybi))]
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)


def pin_hole():
    yp, ypin, ybo, ybi = _top_y()
    ztop = _cap_top()
    h = cq.Workplane().add(cq.Solid.makeCylinder(PIN_HOLE / 2, ztop + 1.0 - PIN_Z0, cq.Vector(PIN_X, ypin, PIN_Z0), cq.Vector(0, 0, 1)))
    c = PIN_TIP
    csk = cq.Workplane().add(cq.Solid.makeCone(PIN_HOLE / 2, PIN_HOLE / 2 + c + 0.5, c + 0.5, cq.Vector(PIN_X, ypin, ztop - c), cq.Vector(0, 0, 1)))
    return h.union(csk)


def pin():
    """The lock, as it sits (+Y side): a head on the cap, a shaft down through the cap into the boss,
    stopping 0.6 short of the hole's floor, a 45 deg chamfer on its tip. Printed head-down."""
    yp, ypin, ybo, ybi = _top_y()
    ztop = _cap_top()
    z0 = PIN_Z0 + 0.6
    r, c = PIN_D / 2, PIN_TIP
    # the head sits 0.02 above the cap: resting exactly on it would be a tangent face for the checks
    shaft = cq.Workplane().add(cq.Solid.makeCylinder(r, ztop + 0.5 - z0 - c, cq.Vector(PIN_X, ypin, z0 + c), cq.Vector(0, 0, 1)))
    tip = cq.Workplane().add(cq.Solid.makeCone(r - c, r, c + 0.01, cq.Vector(PIN_X, ypin, z0), cq.Vector(0, 0, 1)))
    head = cq.Workplane().add(cq.Solid.makeCylinder(PIN_HEAD_D / 2, PIN_HEAD_H, cq.Vector(PIN_X, ypin, ztop + 0.02), cq.Vector(0, 0, 1)))
    return shaft.union(tip).union(head)


def stop():
    """On the tray-cradle, ahead of the tongue: the backstrap slides until the tongue's front edge
    meets it, and there the two halves of the pin hole line up (0.2 past: the hole's 0.25 play
    takes it)."""
    return side_skin(A_STRIP, B_TONGUE, STOP_X[0], STOP_X[1])


def strip():
    """The tray-cradle's side plate, its two rails, the stop and the cap."""
    s = side_skin(A_STRIP, B_STRIP, STRIP_X[0], STRIP_X[1])
    s = s.cut(side_corner_cut(STRIP_X[0], +1, B_STRIP, +1, LEADIN_JOINT))       # lead-in at the rear outer edge
    for zc in RAIL_Z:
        s = s.union(rail(zc))
    s = s.union(stop()).union(cap())
    return s.cut(pin_hole())


def side_corner_cut(x_end, dx, a, da, size, step=2.0):
    """+Y side: a 45 deg chamfer along z on the edge where a side skin's end face (at x_end) meets its face at
    shell offset a. dx = +1 when the material lies at x > x_end (-1 otherwise); da = +1 for an outer face
    (material at smaller y), -1 for an inner face. Ruled through the same z samples as side_skin, so the
    cut follows the skin's facets exactly; it overshoots the faces by 0.2 and the skin's ends by 0.5."""
    z0, z1 = z_bed(), BAND_TOP
    n = max(2, int(math.ceil((z1 - z0) / step)))
    zs = [z0 + (z1 - z0) * i / n for i in range(n + 1)]
    secs = [(z0 - 0.5, z0)] + [(z, z) for z in zs] + [(z1 + 0.5, z1)]
    o = 0.2
    wires = []
    for z, zr in secs:
        yf = side_r(zr) + a
        pts = [(x_end - dx * o, yf + da * o), (x_end + dx * (size + o), yf + da * o), (x_end - dx * o, yf - da * (size + o))]
        wires.append(cq.Workplane("XY", origin=(0, 0, z)).polyline(pts).close().val())
    return cq.Workplane().add(cq.Solid.makeLoft(wires, True))


def tongue(tabs=True, buttons=True):
    """The backstrap's side tongue: two grooves for the plate's rails, and the boss the pin goes
    down into. `tabs` (kept for bisect_backstrap.py's variants) now switches the grooves and the
    boss - the joint's features - since v0.6 has no flex tabs."""
    t = side_skin(A_TONGUE, B_TONGUE, TONGUE_X[0], TONGUE_X[1])
    if tabs:
        for zc in RAIL_Z:
            t = t.cut(groove(zc))
        t = t.union(boss())
    for bx, bz in (SIDE_BUTTONS if buttons else []):  # dungaree side buttons on the fixed part of the tongue
        # sunk 1.0 into the 2.1 tongue from its innermost face over the disc's height: sunk 0.3 at the
        # centre only, the disc's lowest layers missed the tongue (which follows the shell inward
        # below the belly) and islands.py found them floating - the slicer's "floating regions"
        yo_in = min(side_r(bz + dz) for dz in (-5.0, -3.5, -1.75, 0.0, 1.75, 3.5)) + B_TONGUE
        yo = side_r(bz) + B_TONGUE
        # teardrop outline (45 deg point below): a round disc's underside overhangs in the upright print
        btn = teardrop_y(bx, bz, 7.0, yo_in - 1.0, yo + 1.26, up=False)
        for dx in (-1.2, 1.2):
            btn = btn.cut(cq.Workplane().add(cq.Solid.makeCylinder(0.6, 2.0, cq.Vector(bx + dx, yo + 0.5, bz), cq.Vector(0, 1, 0))))
        t = t.union(btn)
    t = t.cut(side_corner_cut(TONGUE_X[1], -1, A_TONGUE, -1, LEADIN_JOINT))   # lead-in at the front inner edge
    return t.cut(pin_hole()) if tabs else t


def wedge():
    """Joins the backstrap's curved band to its straight tongue (cut to the shell later)."""
    return side_skin(SHELL_CLR - 8.0, B_TONGUE, WEDGE_X[0], WEDGE_X[1])


# ------------------------------------------------------------------- spring tabs
def radial_box(theta, t0, t1, z0, z1, r0=45.0, r1=110.0):
    """A box from radius r0 to r1 and tangential offset t0..t1 at angle theta (deg), z0..z1."""
    return box(r0, r1, t0, t1, z0, z1).rotate((0, 0, 0), (0, 0, 1), theta)


def radial_prism(theta, pts, r0=45.0, r1=110.0):
    """A (tangential, z) outline extruded radially from r0 to r1 at angle theta (deg)."""
    return cq.Workplane("YZ", origin=(r0, 0, 0)).polyline(pts).close().extrude(r1 - r0).rotate((0, 0, 0), (0, 0, 1), theta)


def spring_cuts(gable=True):
    """U-slot flexures. gable=True: the slot and the tab close at the top in a 45 deg point instead of
    a flat top slit. The flat slit's roof, a 15 mm curved bridge only 2.5 mm thick with air on both
    faces, is what Bambu Studio flagged as a "floating cantilever" (bisect_backstrap.py: only the
    no-springs variant sliced without the warning)."""
    z0, z1 = SPRING_Z
    o = SHELL_CLR + BAND_T
    hw, S = SPRING_W / 2, SLIT
    k = S * math.sqrt(2)                                  # vertical offset of a slit S wide along a 45 deg line
    cuts = None
    for th in SPRINGS:
        if not gable:
            c = radial_box(th, -hw - S, -hw, z0, z1 + S).union(radial_box(th, hw, hw + S, z0, z1 + S))
            c = c.union(radial_box(th, -hw - S, hw + S, z1, z1 + S))
            c = c.union(layer(radial_box(th, -hw, hw, z0 + 1.0, z1), o - SPRING_THIN, o + 0.5))
        else:
            apex = z1 + hw + S
            outer = [(-(hw + S), z0), (hw + S, z0), (hw + S, z1), (0.0, apex), (-(hw + S), z1)]
            tab = [(-hw, z0 - 1.0), (hw, z0 - 1.0), (hw, z1 + S - k), (0.0, apex - k), (-hw, z1 + S - k)]
            c = radial_prism(th, outer).cut(radial_prism(th, tab, 40.0, 115.0))
            thin = [(-hw, z0 + 1.0), (hw, z0 + 1.0), (hw, z1 + S - k), (0.0, apex - k), (-hw, z1 + S - k)]
            c = c.union(layer(radial_prism(th, thin), o - SPRING_THIN, o + 0.5))                    # thin the tab
        cuts = c if cuts is None else cuts.union(c)
    return cuts


def spring_nubs():
    """Inward nubs near each spring tab's tip, PRELOAD into the shell: square frustums with 45 deg sides
    all round, so the backstrap's sideways slide rides them up onto the shell instead of catching (and
    scratching) on a square edge. The base starts 1.0 mm inside the tab."""
    z0, z1 = SPRING_Z
    zc = z1 - 7.0                                          # the frustum base stays inside the tab's pointed top
    top_w, top_h = 2.0, 2.2
    nubs = None
    for th in SPRINGS:
        rs = shell.radius_at(prof(), zc, th)
        reach = PRELOAD + (RIB_CLR + PIN_HOLE - PIN_D) * abs(math.cos(math.radians(th)))   # play lost when the collar seats
        ri, rt = rs + SHELL_CLR + SPRING_THIN / 2, rs - reach     # base mid-way through the thinned tab
        d = ri - rt
        base = cq.Workplane("YZ", origin=(ri, 0, 0)).rect(top_w + 2 * d, top_h + 2 * d).val()
        tip = cq.Workplane("YZ", origin=(rt, 0, 0)).rect(top_w, top_h).val()
        n = cq.Workplane().add(cq.Solid.makeLoft([base, tip], True)).translate((0, 0, zc))
        n = n.rotate((0, 0, 0), (0, 0, 1), th)
        nubs = n if nubs is None else nubs.union(n)
    return nubs


# ---------------------------------------------------------------------------- parts
def build_cradle(tray_b, dressed=True):
    zb = z_bed()
    filler = box(OX0 + CORNER_R, OX1 - CORNER_R, Y_BACK, PART_Y - 1.3, OZ0 - 4.0, OZ0 + 1.0)   # tilted underside to the bed
    tr = to_robot(tray_b.union(filler))
    ribs = None
    for bx in RIB_BX:
        r = box(20, 140, -bx - RIB_T / 2, -bx + RIB_T / 2, zb, 200)
        ribs = r if ribs is None else ribs.union(r)
    ribs = ribs.intersect(behind_plate(z_lo=OZ0 - 10)).cut(proxy(RIB_CLR))
    # front half of the waistband: stops 0.4 behind the tray back (a grazing union there meshed
    # badly); the ribs join band and tray square-on
    fb = band(SHELL_CLR, SHELL_CLR + BAND_T, SPLIT_F_X, 200, zb, BAND_TOP).intersect(
        behind_plate(z_lo=-200, z_hi=400, y_lim=Y_BACK - 0.4))
    c = tr.union(ribs).union(fb).union(both_sides(strip()))
    if dressed:
        import outfit
        adds, cuts = outfit.front()
        for a in adds:
            c = c.union(a)
        for k in cuts:
            c = c.cut(k)
    c = c.cut(box(-300, 300, -300, 300, zb - 50, zb))          # flat on the bed
    return c


def build_backstrap(nubs=True, dressed=True, springs=True, tabs=True, buttons=True, gutter=True, gable=True):
    """The flags (all on for the real part) let bisect_backstrap.py slice variants to find which
    feature group a slicer warning comes from."""
    zb = z_bed()
    s = band(SHELL_CLR, SHELL_CLR + BAND_T, -200, SPLIT_B_X, zb, BAND_TOP)
    s = s.union(both_sides(wedge().cut(proxy(SHELL_CLR))))
    s = s.union(both_sides(tongue(tabs=tabs, buttons=buttons)))
    g = GUTTER
    o = SHELL_CLR + BAND_T
    if gutter:
        s = s.union(band(o - 0.5, o + g["w"] + g["t"], -200, g["x_max"], zb, zb + g["t"]))
        s = s.union(band(o + g["w"], o + g["w"] + g["t"], -200, g["x_max"], zb, zb + g["h"]))
    if dressed:
        import outfit
        adds, cuts = outfit.back()
        for a in adds:
            s = s.union(a)
        for k in cuts:
            s = s.cut(k)
    if springs:
        s = s.cut(spring_cuts(gable))
    if nubs and springs:
        s = s.union(spring_nubs())
    s = s.cut(box(-300, 300, -300, 300, zb - 50, zb))
    return s


# ---------------------------------------------------------------------- board model
def board_solids():
    """Elecrow's STEP solids for fit checks: the flat-drawn flex tails clipped at z 53, the
    optional camera module (drawn hanging below the board, AS-AG638) left out."""
    a = cq.importers.importStep(E.BOARD_STEP)
    keep = cq.Solid.makeBox(400, 100, 300, cq.Vector(-200, -50, -247))
    out = []
    for s in a.solids().vals():
        if s.BoundingBox().zmax < -43.0 and s.BoundingBox().zmin < -60.0:
            continue
        c = s.intersect(keep)
        if c.Volume() > 1e-6:
            out.append(c)
    return out


# --------------------------------------------------------------------------- checks
def overlap(a, b):
    try:
        return a.intersect(b).Volume()
    except Exception:
        return -1.0


CHECK_DIR = os.path.join(E.OUT, "step", "check")
PARTS_PRE = "reachy-crowpanel"


def save_check_inputs(tray_b, bezel_b):
    """Board-frame tray and bezel for --check-only (the robot-frame parts are the out/step exports)."""
    os.makedirs(CHECK_DIR, exist_ok=True)
    cq.exporters.export(tray_b, os.path.join(CHECK_DIR, "tray-board-frame.step"))
    cq.exporters.export(bezel_b, os.path.join(CHECK_DIR, "bezel-board-frame.step"))


def load_check_inputs():
    imp = cq.importers.importStep
    s = lambda n: imp(os.path.join(E.OUT, "step", "%s-%s.step" % (PARTS_PRE, n)))
    return (imp(os.path.join(CHECK_DIR, "tray-board-frame.step")), imp(os.path.join(CHECK_DIR, "bezel-board-frame.step")),
            s("tray-cradle"), s("backstrap"))


def check(tray_b, bezel_b, cradle, backstrap_free, nubs):
    ok = True
    solids = board_solids()
    print("interference check: %d board solids" % len(solids))
    for name, part in (("tray", tray_b.val()), ("bezel", bezel_b.val())):
        pbb = part.BoundingBox()
        hits = []
        for s in solids:
            b = s.BoundingBox()
            if b.xmax < pbb.xmin or b.xmin > pbb.xmax or b.ymax < pbb.ymin or b.ymin > pbb.ymax or b.zmax < pbb.zmin or b.zmin > pbb.zmax:
                continue
            v = overlap(part, s)
            if v > 0.05 or v < 0:
                hits.append((v, b))
        for v, b in hits:
            print("  %s: HIT %.2f mm3 at x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (name, v, b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax))
        print("  %s vs board: %s" % (name, "clear" if not hits else "%d hits" % len(hits)))
        ok &= not hits
    shell0 = proxy(0.0).val()
    bez_r = to_robot(bezel_b).val()
    v_nub = overlap(nubs.val(), shell0)
    pairs = [("bezel/tray", bezel_b.val(), tray_b.val()), ("cradle/backstrap", cradle.val(), backstrap_free.val()),
             ("cradle/shell", cradle.val(), shell0), ("bezel/shell", bez_r, shell0), ("bezel/backstrap", bez_r, backstrap_free.val())]
    for name, a, b in pairs:
        v = overlap(a, b)
        bad = v > 0.05 or v < 0
        print("  %-18s overlap %.3f mm3 %s" % (name, v, "FAIL" if bad else "ok"))
        ok &= not bad
    # the backstrap may be passed with its nubs: then its overlap with the shell must be the nubs' alone
    v_bs = overlap(backstrap_free.val(), shell0)
    extra = v_bs - (v_nub if v_bs > 0.05 else 0.0)
    bad = abs(extra) > 0.05 or v_bs < 0
    print("  %-18s overlap %.3f mm3 beyond the spring nubs %s" % ("backstrap/shell", extra, "FAIL" if bad else "ok"))
    ok &= not bad
    print("  spring nubs/shell  %.1f mm3 (intended: %.1f mm preload each plus the seating play)" % (v_nub, PRELOAD))
    ok &= v_nub > 0
    ok &= check_paths(solids, tray_b, bezel_b, cradle, backstrap_free, nubs, shell0)
    print("CHECK " + ("PASSED" if ok else "FAILED"))
    return ok


def board_overlap(part, solids, dy=0.0):
    pbb = part.BoundingBox()
    v = 0.0
    for s in solids:
        m = s.translate(cq.Vector(0, dy, 0)) if dy else s
        b = m.BoundingBox()
        if b.xmax < pbb.xmin or b.xmin > pbb.xmax or b.ymax < pbb.ymin or b.ymin > pbb.ymax or b.zmax < pbb.zmin or b.zmin > pbb.zmax:
            continue
        v += max(overlap(part, m), 0.0)
    return v


def check_paths(solids, tray_b, bezel_b, cradle, backstrap, nubs, shell0):
    """Assembly paths, not just final positions. The board drops into the tray along -y (checked by lifting
    it back out along +y); the bezel then presses on along -y (lifted back, its snap bumps left out); the
    tray-cradle slides onto the belly along -x (backed off along +x); the backstrap slides on along +x
    (pulled back along -x) past the robot and the tray-cradle. The backstrap's spring nubs and joint hooks
    are left out: they are meant to deflect on the way."""
    import enclosure as EN
    ok = True
    print("assembly paths (overlap must stay 0 at every step):")
    tray = tray_b.val()
    for d in (0.5, 1.0, 2.0, 3.0, 4.5, 6.0, 8.0, 10.0, 13.0, 16.0):
        v = board_overlap(tray, solids, d)
        bad = v > 0.05
        print("  board lifted %4.1f mm out of the tray: %.3f mm3 %s" % (d, v, "FAIL" if bad else "ok"))
        ok &= not bad
    bez = bezel_b.val()
    for side, at in BUMPS:
        bez = bez.cut(EN.bump(side, at).val())
    for d in (0.5, 1.0, 2.0, 3.0, 5.0, 8.0):
        m = bez.translate(cq.Vector(0, d, 0))
        v1, v2 = overlap(m, tray), board_overlap(m, solids)
        bad = v1 > 0.05 or v2 > 0.05 or v1 < 0
        print("  bezel (no bumps) %4.1f mm up: vs tray %.3f mm3, vs board %.3f mm3 %s" % (d, v1, v2, "FAIL" if bad else "ok"))
        ok &= not bad
    cr = cradle.val()
    for d in (1.0, 3.0, 6.0, 10.0, 20.0, 40.0, 60.0):
        v = overlap(cr.translate(cq.Vector(d, 0, 0)), shell0)
        bad = v > 0.05 or v < 0
        print("  tray-cradle %4.1f mm off the belly vs shell: %.3f mm3 %s" % (d, v, "FAIL" if bad else "ok"))
        ok &= not bad
    # v0.6: nothing on the joint flexes, so only the spring nubs come off. The path is the rails'
    # whole run and past the rear of the plate: the pins must be out, so they are not in `backstrap`.
    bs = backstrap.val().cut(nubs.val())
    for d in (0.5, 1.0, 3.0, 6.0, 10.0, 15.0, 20.0, 25.0, 30.0, 38.0, 45.0, 60.0, 80.0, 100.0):
        m = bs.translate(cq.Vector(-d, 0, 0))
        v1, v2 = overlap(m, shell0), overlap(m, cr)
        bad = v1 > 0.05 or v2 > 0.05 or v1 < 0 or v2 < 0
        print("  backstrap %5.1f mm back: vs shell %.3f mm3, vs tray-cradle %.3f mm3 %s" % (d, v1, v2, "FAIL" if bad else "ok"))
        ok &= not bad
    # The stop is real: 0.4 further forward than seated, the tongues run into it (0.2 of travel left).
    v = overlap(bs.translate(cq.Vector(0.4, 0, 0)), cr)
    print("  backstrap 0.4 mm FORWARD of seated vs tray-cradle: %.3f mm3 (the stop; must be > 0) %s" % (v, "ok" if v > 0.05 else "FAIL"))
    ok &= v > 0.05
    # The pins: clear of both parts where they sit, in both halves' holes (so they lock), and they
    # lift straight out.
    pins = both_sides(pin()).val()
    for name, part in (("tray-cradle", cr), ("backstrap", backstrap.val())):
        v = overlap(pins, part)
        bad = v > 0.05 or v < 0
        print("  pins vs %-11s %.3f mm3 %s" % (name, v, "FAIL" if bad else "ok"))
        ok &= not bad
    # positive control: a rod 0.3 wider than the HOLE (not the pin - the hole has 0.4 of play) must
    # hit both parts, or the pin is not actually passing through both of them
    for name, part in (("tray-cradle", cr), ("backstrap", bs)):
        grown = both_sides(cq.Workplane().add(cq.Solid.makeCylinder(PIN_HOLE / 2 + 0.3, 60.0, cq.Vector(PIN_X, _top_y()[1], PIN_Z0 + 0.6), cq.Vector(0, 0, 1)))).val()
        v = overlap(grown, part)
        print("  rod 0.3 over the hole vs %-11s %.2f mm3 (> 0: the pin passes through this part) %s" % (name, v, "ok" if v > 0.05 else "FAIL"))
        ok &= v > 0.05
    for d in (2.0, 10.0, 30.0):
        v = overlap(pins.translate(cq.Vector(0, 0, d)), cr) + overlap(pins.translate(cq.Vector(0, 0, d)), backstrap.val())
        print("  pins lifted %4.1f mm: %.3f mm3 %s" % (d, v, "FAIL" if v > 0.05 else "ok"))
        ok &= v <= 0.05
    return ok


# --------------------------------------------------------------------------- output
def report(name, wp):
    v = wp.val()
    bb = v.BoundingBox()
    print("%-11s valid=%s solids=%d vol %6.1f cm3  x %7.1f..%6.1f  y %7.1f..%6.1f  z %6.1f..%6.1f" % (
        name, v.isValid(), len(wp.solids().vals()), v.Volume() / 1000, bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))


def to_bed(wp):
    """Centre on the plate and set down at z 0 by the tessellated vertices: OCC's bounding box of the
    lofted collar surfaces is loose by a millimetre or more, and the print STLs floated that much."""
    v, _ = wp.val().tessellate(0.05, 0.2)
    xs, ys, zs = [p.x for p in v], [p.y for p in v], [p.z for p in v]
    return wp.translate((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs)))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="build, export, then run the fit checks")
    ap.add_argument("--check-only", action="store_true",
                    help="fit checks on the last build's STEP exports, no rebuild (run it beside check_mesh/islands/bambu)")
    ap.add_argument("--plain", action="store_true", help="no dungarees detail (faster, for fit work)")
    args = ap.parse_args(argv)
    dressed = not args.plain
    if args.check_only:
        tray_b, bezel_b, cradle, backstrap = load_check_inputs()
        sys.exit(0 if check(tray_b, bezel_b, cradle, backstrap, spring_nubs()) else 1)
    for d in ("step", "stl", "print"):
        os.makedirs(os.path.join(E.OUT, d), exist_ok=True)
    X0, Z0 = placement()
    print("placement: board centre at robot X %.2f Z %.2f, tilt %.1f deg" % (X0, Z0, TILT))
    tray_b, bezel_b = E.build_tray(dressed), E.build_bezel(dressed)
    cradle = build_cradle(tray_b, dressed)
    backstrap = build_backstrap(True, dressed)
    bezel_r = to_robot(bezel_b)
    pins = both_sides(pin())
    parts = {"bezel": bezel_r, "tray-cradle": cradle, "backstrap": backstrap, "pins": pins}
    for n, p in parts.items():
        report(n, p)
    pre = "reachy-crowpanel"
    for n, p in parts.items():
        cq.exporters.export(p, os.path.join(E.OUT, "step", "%s-%s.step" % (pre, n)))
        cq.exporters.export(p, os.path.join(E.OUT, "stl", "%s-%s.stl" % (pre, n)), tolerance=0.02, angularTolerance=0.1)
    # the two pins head-down, side by side (in the robot they are 170 mm apart)
    one = pin().translate((-PIN_X, -_top_y()[1], 0)).rotate((0, 0, 0), (1, 0, 0), 180)
    prints = {"bezel": to_bed(bezel_b.rotate((0, 0, 0), (1, 0, 0), -90)),   # face (+y) down
              "tray-cradle": to_bed(cradle), "backstrap": to_bed(backstrap),
              "pins": to_bed(one.union(one.translate((PIN_HEAD_D + 6.0, 0, 0))))}
    for n, p in prints.items():
        cq.exporters.export(p, os.path.join(E.OUT, "print", "%s-%s-print.stl" % (pre, n)), tolerance=0.02, angularTolerance=0.1)
    asm = cq.Assembly()
    asm.add(bezel_r, name="bezel", color=cq.Color(0.20, 0.33, 0.52))
    asm.add(cradle, name="tray-cradle", color=cq.Color(0.20, 0.33, 0.52))
    asm.add(backstrap, name="backstrap", color=cq.Color(0.20, 0.33, 0.52))
    asm.add(pins, name="pins", color=cq.Color(0.72, 0.45, 0.20))
    try:
        board = cq.Workplane().add(cq.Compound.makeCompound(board_solids()))
        asm.add(to_robot(board), name="crowpanel", color=cq.Color(0.15, 0.15, 0.17))
    except Exception as e:
        print("board not added to the assembly:", e)
    asm.save(os.path.join(E.OUT, "%s-assembly.step" % pre))
    save_check_inputs(tray_b, bezel_b)
    print("written to", E.OUT)
    if args.check:
        if not check(tray_b, bezel_b, cradle, backstrap, spring_nubs()):
            sys.exit(1)


if __name__ == "__main__":
    main()
