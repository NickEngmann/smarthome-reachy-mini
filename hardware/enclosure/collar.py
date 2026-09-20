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
A_STRIP = SHELL_CLR + STRIP_MARGIN                 # strip inner face offset from the shell side
B_STRIP = A_STRIP + STRIP_T
A_TONGUE = B_STRIP + JOINT_GAP
B_TONGUE = A_TONGUE + TONGUE_T


def hook_z(tab):
    zr, zt = tab
    return zt - 0.6 - HOOK_H, zt - 0.6


def strip():
    s = side_skin(A_STRIP, B_STRIP, STRIP_X[0], STRIP_X[1])
    for tab in TABS:
        h0, h1 = hook_z(tab)
        # window; its bottom clears the hook's 45 deg underside, which enters the strip's plane at h0 - 0.6
        s = s.cut(box(HOOK_X[0] - FIT_CATCH, HOOK_X[1] + 0.8, 40, 120, h0 - 1.2, h1 + 0.6))
    return s.cut(side_corner_cut(STRIP_X[0], +1, B_STRIP, +1, LEADIN_JOINT))       # lead-in at the rear outer edge


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
    t = side_skin(A_TONGUE, B_TONGUE, TONGUE_X[0], TONGUE_X[1])
    for tab in (TABS if tabs else []):
        zr, zt = tab
        x0, x1 = TAB_X
        # U-slot whose top closes in a 45 deg point: a flat top slit is a bridge right above the tab, which
        # can sag onto it in the upright print and fuse the flexure
        slot, _ = E.gable_slot((x0 + x1) / 2, (x1 - x0) / 2, zr, zt, SLIT, 40.0, 120.0)
        t = t.cut(slot)
        # hook on the tab's inner face: catch face at HOOK_X[0] (the collar pulls the backstrap -x
        # onto it), a ramp toward +x that leads as the backstrap slides forward
        h0, h1 = hook_z(tab)
        yi = side_r((h0 + h1) / 2) + A_TONGUE
        pts = [(HOOK_X[0], yi + 0.3), (HOOK_X[0], yi - HOOK_D), (HOOK_X[0] + 1.0, yi - HOOK_D), (HOOK_X[1], yi + 0.3)]
        zb0 = h0 - HOOK_D - 0.3
        hook = cq.Workplane("XY", origin=(0, 0, zb0)).polyline(pts).close().extrude(h1 - zb0)
        # 45 deg underside: the hook's catch face and top are unchanged, its bottom slopes from the
        # tongue face (z zb0) to the tip (z h0) instead of hanging flat in the upright print
        py, pz = yi + 0.3, zb0
        tri = [(py + 20.0, pz - 20.0), (py - 20.0, pz + 20.0), (py - 20.0, pz - 20.0)]
        hook = hook.cut(cq.Workplane("YZ", origin=(HOOK_X[0] - 1.0, 0, 0)).polyline(tri).close().extrude(HOOK_X[1] - HOOK_X[0] + 2.0))
        t = t.union(hook)
        # pull lip at the tab's tip: lift it with a fingernail to release; 45 deg underside
        yo = side_r(zt) + B_TONGUE
        lip = [(yo - 0.3, zt - 2.0 - PULL_LIP), (yo + PULL_LIP, zt - 2.0), (yo + PULL_LIP, zt), (yo - 0.3, zt)]
        t = t.union(cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(lip).close().extrude(x1 - x0))
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
    return t.cut(side_corner_cut(TONGUE_X[1], -1, A_TONGUE, -1, LEADIN_JOINT))   # lead-in at the front inner edge


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
        reach = PRELOAD + (RIB_CLR + FIT_CATCH) * abs(math.cos(math.radians(th)))   # play lost when the collar seats
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
    zone = None
    for tab in TABS:
        h0, h1 = hook_z(tab)
        z = box(HOOK_X[0] - 1.0, HOOK_X[1] + 1.0, 60, 110, h0 - 2.0, h1 + 1.0)
        zone = z if zone is None else zone.union(z)
    zone = both_sides(zone)
    bs = backstrap.val().cut(nubs.val()).cut(zone.val())
    for d in (1.0, 3.0, 6.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 80.0, 100.0):
        m = bs.translate(cq.Vector(-d, 0, 0))
        v1, v2 = overlap(m, shell0), overlap(m, cr)
        bad = v1 > 0.05 or v2 > 0.05 or v1 < 0 or v2 < 0
        print("  backstrap %4.1f mm back: vs shell %.3f mm3, vs tray-cradle %.3f mm3 %s" % (d, v1, v2, "FAIL" if bad else "ok"))
        ok &= not bad
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
    parts = {"bezel": bezel_r, "tray-cradle": cradle, "backstrap": backstrap}
    for n, p in parts.items():
        report(n, p)
    pre = "reachy-crowpanel"
    for n, p in parts.items():
        cq.exporters.export(p, os.path.join(E.OUT, "step", "%s-%s.step" % (pre, n)))
        cq.exporters.export(p, os.path.join(E.OUT, "stl", "%s-%s.stl" % (pre, n)), tolerance=0.02, angularTolerance=0.1)
    prints = {"bezel": to_bed(bezel_b.rotate((0, 0, 0), (1, 0, 0), -90)),   # face (+y) down
              "tray-cradle": to_bed(cradle), "backstrap": to_bed(backstrap)}
    for n, p in prints.items():
        cq.exporters.export(p, os.path.join(E.OUT, "print", "%s-%s-print.stl" % (pre, n)), tolerance=0.02, angularTolerance=0.1)
    asm = cq.Assembly()
    asm.add(bezel_r, name="bezel", color=cq.Color(0.20, 0.33, 0.52))
    asm.add(cradle, name="tray-cradle", color=cq.Color(0.20, 0.33, 0.52))
    asm.add(backstrap, name="backstrap", color=cq.Color(0.20, 0.33, 0.52))
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
