#!/usr/bin/env python3
"""CrowPanel Advanced 7" ESP32-P4 enclosure that clamps onto Reachy Mini's front belly,
dressed as a pair of denim dungarees (the display is the bib).

    python shell.py                  # once: the Reachy shell proxy (out/cache)
    python enclosure.py [--check]    # parts -> out/step, out/stl, out/print; --check = fit checks
    python check_mesh.py             # watertightness of every exported STL
    python render.py                 # out/render/*.png

Three prints, no screws:
  BEZEL        the bib: glass window, stitched border, two bib buttons and a heart engraved in
               the face; full-depth top wall with the microSD slot; a snap lip (bumps) on the
               other three sides; bosses whose pegs go through the board's M3 holes. Face down.
  TRAY-CRADLE  the tray (USB-C windows, switch slot, BOOT/RESET flex tabs, LED and mic holes,
               an overalls strap + buckle + button on each end) and, behind it, ribs contoured
               to Reachy's belly and the front half of the waistband ending in a joint strip
               on each side. Upright.
  BACKSTRAP    the rest of the dungarees: waistband with belt loops, back pockets, crossed
               straps with buttons, a cable gutter that doubles as the rolled cuff, three spring
               tabs that preload the collar, and at each side a tongue with two flex tabs that
               hook into the strip. Upright.
Frames, printer fits and every number: geom.py. Board facts come from Elecrow's STEP.
"""
import os, sys, math
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geom import *          # noqa: F401,F403  (constants + helpers)

OUT = os.path.join(HERE, "out")
REPO = os.path.dirname(os.path.dirname(HERE))
BOARD_STEP = os.path.join(REPO, "cad", "crowpanel-advanced-7in-esp32-p4", "ESP32-P4-7_0-inch-20251229.stp")


# ------------------------------------------------------------------ snap features (B)
def bump(side, at):
    """Bump on the lip's outer face: flat catch toward the bezel, 45 deg lead-in toward the tray."""
    d, y0, y1 = BUMP_D, BUMP_Y0, BUMP_Y0 + BUMP_H
    if side in ("L", "R"):
        s = -1 if side == "L" else 1
        xf = (CX0 + LIP_CLR) if side == "L" else (CX1 - LIP_CLR)
        pts = [(xf - s * 0.05, y0), (xf - s * 0.05, y1), (xf + s * d, y1), (xf + s * d, y0 + d)]
        return cq.Workplane("XY", origin=(0, 0, at - BUMP_W / 2)).polyline(pts).close().extrude(BUMP_W)
    zf = CZ0 + LIP_CLR                                    # bottom side, outward = -z
    pts = [(y0, zf + 0.05), (y1, zf + 0.05), (y1, zf - d), (y0 + d, zf - d)]
    return cq.Workplane("YZ", origin=(at - BUMP_W / 2, 0, 0)).polyline(pts).close().extrude(BUMP_W)


def pocket(side, at):
    """Blind pocket in the tray's inner wall: the bump's reach past the wall face + clearance."""
    w, dep = BUMP_W + POCKET_W_EXTRA, BUMP_D - LIP_CLR + POCKET_DEPTH_EXTRA
    y0, y1 = BUMP_Y0 - POCKET_Y_EXTRA, BUMP_Y0 + BUMP_H + 0.6
    if side == "L":
        return box(CX0 - dep, CX0 + 0.05, y0, y1, at - w / 2, at + w / 2)
    if side == "R":
        return box(CX1 - 0.05, CX1 + dep, y0, y1, at - w / 2, at + w / 2)
    return box(at - w / 2, at + w / 2, y0, y1, CZ0 - dep, CZ0 + 0.05)


def chamfer_loft_x(xface, outward, cz, cy, w, h, e):
    """45 deg chamfer band around a (z-width w, y-height h) opening on a wall face normal to x."""
    x_in, x_out = xface - outward * e, xface + outward * 0.05
    wi = cq.Workplane("YZ", origin=(x_in, 0, 0)).center(cy, cz).rect(h - 0.2, w - 0.2).val()
    wo = cq.Workplane("YZ", origin=(x_out, 0, 0)).center(cy, cz).rect(h + 2 * e, w + 2 * e).val()
    return cq.Workplane().add(cq.Solid.makeLoft([wi, wo], True))


def xz_prism(pts, y0, y1):
    """An (x, z) outline extruded along y from y0 to y1."""
    return cq.Workplane("XZ", origin=(0, max(y0, y1), 0)).polyline(pts).close().extrude(abs(y1 - y0))


def gable_slot(xc, hw, z_root, z_tip, s, y0, y1):
    """U-slot of width s around a tab (half width hw) rooted at z_root, whose top closes in a 45 deg point:
    no slit roof is bridged right above the flexure, where it could sag onto the tab and fuse to it."""
    k = s * math.sqrt(2)
    apex = z_tip + hw + s
    outer = [(xc - hw - s, z_root), (xc + hw + s, z_root), (xc + hw + s, z_tip), (xc, apex), (xc - hw - s, z_tip)]
    tab = [(xc - hw, z_root - 1.0), (xc + hw, z_root - 1.0), (xc + hw, z_tip + s - k), (xc, apex - k), (xc - hw, z_tip + s - k)]
    lo, hi = min(y0, y1), max(y0, y1)
    return xz_prism(outer, lo, hi).cut(xz_prism(tab, lo - 1.0, hi + 1.0)), tab


def peg(hx, hz):
    """Locating pin on a tray standoff: a teardrop (point down; it prints horizontal) with its point
    clipped to PEG_POINT_R so it passes the board's Ø3.2 hole, and a 45 deg tip."""
    y0, y_tip = PCB_Y0 - 0.05, PCB_Y1 + PEG_THROUGH
    body = teardrop_y(hx, hz, PEG_D, y0, y_tip - PEG_TIP).intersect(cyl_y(hx, hz, 2 * PEG_POINT_R, y0 - 1, y_tip + 1))
    return body.union(cone_y(hx, hz, PEG_D, PEG_D - 2 * PEG_TIP, y_tip - PEG_TIP - 0.05, y_tip))


def end_window(cz, cy, w, h, r):
    """Through-window in the tray's left end wall, rounded, chamfered outside."""
    t = box(OX0 - 1, CX0 + 0.3, cy - h / 2, cy + h / 2, cz - w / 2, cz + w / 2).edges("|X").fillet(r)
    return t.union(chamfer_loft_x(OX0, -1, cz, cy, w, h, EDGE_CHAMFER))


# ----------------------------------------------------------------------- tray (B)
def build_tray(dressed=True):
    top = CZ1 - TOP_SEAM_CLR
    t = box(OX0, OX1, Y_BACK, PART_Y, OZ0, top)
    t = t.edges("|Y").edges("<Z").fillet(CORNER_R)
    t = t.cut(box(CX0, CX1, FLOOR_IN, PART_Y + 1, CZ0, top + 1))
    # standoffs (teardrop: they print horizontal) carrying the locating pegs: the board drops onto the
    # pegs and stays put while the bezel goes on
    for hx, hz in HOLES:
        t = t.union(teardrop_y(hx, hz, STANDOFF_D, FLOOR_IN - 0.05, PCB_Y0))
    t = t.intersect(box(OX0 - 5, OX1 + 5, Y_BACK - 5, PART_Y, OZ0, top))      # teardrop tips stay inside the outline
    for hx, hz in HOLES:
        t = t.union(peg(hx, hz))
    # left end: two USB-C windows with overmold recesses, the slide-switch slot
    for u in USB_C:
        t = t.cut(end_window(u["z"], u["y"], USB_W, USB_H, USB_R))
        # relief channel in the wall's inner face from the window up past the rim: the USB-C shell slides
        # down past the wall as the board drops onto its pegs (0.1 mm from the wall without it)
        t = t.cut(box(CX0 - USB_RELIEF_D, CX0 + 0.05, u["y"] - USB_H / 2, PART_Y + 1.0, u["z"] - USB_W / 2, u["z"] + USB_W / 2))
        # overmold recess, its roof sloped 45 deg (a flat roof is a 1.4 mm cantilever in the upright print)
        rw, rh, rd = USB_RECESS
        zc = u["z"]
        prof = [(OX0 - 0.05, zc - rw / 2), (OX0 + rd, zc - rw / 2), (OX0 + rd, zc + rw / 2), (OX0 - 0.05, zc + rw / 2 + rd + 0.05)]
        t = t.cut(cq.Workplane("XZ", origin=(0, u["y"] + rh / 2, 0)).polyline(prof).close().extrude(rh))
    sw, sh, sr = SWITCH_SLOT
    t = t.cut(end_window(SWITCH["z"], SWITCH["y"], sw, sh, sr))
    # BOOT / RESET: flex tabs in the floor with a nub on the switch, back face thinned
    bt = BUTTON_TAB
    for bx, bz in BUTTONS:
        # each tab is rooted at its BOTTOM (board -z is down in the upright print) and grows up from it.
        # Rooted at its side, the tab's lower edge printed as a 10 mm cantilever over the slit - the
        # slicer's "floating cantilever" on this part
        # its top closes in a 45 deg point (gable_slot), so no bridged slit roof sits right above it
        z_root, z_tip = bz - bt["len"] * 0.62, bz + bt["len"] * 0.38
        slot, tab = gable_slot(bx, bt["w"] / 2, z_root, z_tip, bt["slit"], Y_BACK - 1, FLOOR_IN + 0.1)
        t = t.cut(slot)
        thin = [(x, max(z, z_root + 1.0)) for x, z in tab]                          # thin the tab from the back
        t = t.cut(xz_prism(thin, Y_BACK - 0.05, Y_BACK + bt["thin"]))
        # the nub is a 4 mm pin sticking out of a floor that prints upright: a teardrop, point down,
        # so its underside is a 45 deg slope instead of a cantilever (Bambu flagged one)
        t = t.union(teardrop_y(bx, bz, bt["nub_d"], FLOOR_IN - 0.05, BUTTON_TOP_Y - bt["gap"]))
    for mx, mz in MICS:
        t = t.cut(cyl_y(mx, mz, MIC_HOLE_D, Y_BACK - 1, FLOOR_IN + 0.1))
    for lx, lz in LEDS:
        t = t.cut(cyl_y(lx, lz, LED_HOLE_D, Y_BACK - 1, FLOOR_IN + 0.1))
    for side, at in BUMPS:
        t = t.cut(pocket(side, at))
    t = t.cut(box(-5.0, 5.0, PART_Y - 1.2, PART_Y + 1, OZ0 - 1, CZ0 + 0.3))              # pry notch, bottom centre
    if dressed:
        import outfit
        t = outfit.dress_tray(t)
    return t


# ---------------------------------------------------------------------- bezel (B)
def build_bezel(dressed=True):
    b = box(OX0, OX1, PART_Y, Y_FACE, OZ0, OZ1).edges("|Y").fillet(CORNER_R)
    try:
        b = b.faces(">Y").edges().chamfer(EDGE_CHAMFER)
    except Exception as e:
        print("bezel face chamfer skipped:", e)
    b = b.cut(box(CX0, CX1, PART_Y - 1, PLATE_IN, CZ0, CZ1))
    # the top wall runs the tray's full depth; cut from the rounded outline so its corners match
    topw = (box(OX0, OX1, Y_BACK, Y_FACE, OZ0, OZ1).edges("|Y").fillet(CORNER_R)
            .intersect(box(OX0 - 1, OX1 + 1, Y_BACK, PART_Y + 0.05, CZ1, OZ1 + 1)))
    b = b.union(topw)
    # window over the active area, 45 deg chamfer at the face
    ax0, ax1, az0, az1 = ACTIVE
    m = 0.5
    cx, cz, w, h = (ax0 + ax1) / 2, (az0 + az1) / 2, ax1 - ax0 + 2 * m, az1 - az0 + 2 * m
    b = b.cut(box(cx - w / 2, cx + w / 2, PLATE_IN - 1, Y_FACE + 1, cz - h / 2, cz + h / 2).edges("|Y").fillet(1.0))
    e = 1.2
    wi = cq.Workplane("XZ", origin=(0, Y_FACE - e, 0)).center(cx, cz).rect(w - 0.2, h - 0.2).val()
    wo = cq.Workplane("XZ", origin=(0, Y_FACE + 0.05, 0)).center(cx, cz).rect(w + 2 * e, h + 2 * e).val()
    b = b.cut(cq.Workplane().add(cq.Solid.makeLoft([wi, wo], True)))
    # microSD slot through the top wall, rounded, and a fingertip dish outside
    sx, sy = SD["x"], SD["y"]
    lw, lh = SD_SLOT
    b = b.cut(box(sx - lw / 2, sx + lw / 2, sy - lh / 2, sy + lh / 2, CZ1 - 1, OZ1 + 1).edges("|Z").fillet(1.0))
    b = b.cut(cq.Workplane().add(cq.Solid.makeSphere(9.0, cq.Vector(sx, sy, OZ1 + 9.0 - 1.2))))
    # snap lip on L, R, B (the top is the bezel's own wall), bumps
    lip = box(CX0 + LIP_CLR, CX1 - LIP_CLR, PART_Y - LIP_H, PART_Y + 0.05, CZ0 + LIP_CLR, CZ1 + 0.05)
    lip = lip.cut(box(CX0 + LIP_CLR + LIP_T, CX1 - LIP_CLR - LIP_T, PART_Y - LIP_H - 1, PART_Y + 1, CZ0 + LIP_CLR + LIP_T, CZ1 + 1))
    b = b.union(lip)
    # the lip hangs from the plate: a shelf from the walls to the lip's inner face, parting plane to plate.
    # Without it the plate's inner face (y PLATE_IN) sat 2.4 above the lip, which was held only by the top
    # wall and the bosses - face down, the whole U of the lip printed as one bridge in mid-air
    # starts exactly at the parting plane: 0.05 below it the shelf ran into the tray walls' top edge (0.95 mm3)
    shelf = box(CX0 - 0.05, CX1 + 0.05, PART_Y, PLATE_IN + 0.05, CZ0 - 0.05, CZ1 + 0.05)
    shelf = shelf.cut(box(CX0 + LIP_CLR + LIP_T, CX1 - LIP_CLR - LIP_T, PART_Y - 1, PLATE_IN + 1, CZ0 + LIP_CLR + LIP_T, CZ1 + 1))
    b = b.union(shelf)
    for side, at in BUMPS:
        b = b.union(bump(side, at))
    # bosses holding the board down on its standoffs, with sockets for the tray's locating pegs
    for hx, hz in HOLES:
        y_end = PCB_Y1 + BOSS_GAP
        b = b.union(cyl_y(hx, hz, BOSS_D, y_end, PLATE_IN + 0.05))
        b = b.cut(cyl_y(hx, hz, SOCKET_D, y_end - 0.1, y_end + SOCKET_DEPTH))
        b = b.cut(cone_y(hx, hz, SOCKET_D + 2 * SOCKET_MOUTH, SOCKET_D, y_end - 0.05, y_end + SOCKET_MOUTH))
    for mx, mz in MICS:
        b = b.cut(cyl_y(mx, mz, MIC_HOLE_D, PLATE_IN - 0.5, Y_FACE + 1))
    if dressed:
        import outfit
        b = outfit.dress_bezel(b)
    return b


if __name__ == "__main__":
    import collar
    collar.main()
