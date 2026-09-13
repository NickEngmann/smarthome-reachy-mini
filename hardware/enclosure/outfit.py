"""Denim dungarees for Reachy Mini: the cosmetic detail on all three prints.

The display is the bib. Everything is sized for an FDM print on the X1C:
  * on the UPRIGHT parts (tray-cradle, backstrap) detail stands on vertical faces: proud features
    are whole line widths (0.84 / 1.26 / 1.68), grooves 0.84 wide and 0.5 deep, and horizontal
    stitch dashes are 0.8 tall (4 layers);
  * on the FACE-DOWN bezel detail is engraved into the first layers (a face-down print cannot
    have anything proud): 1.0 wide (elephant foot eats ~0.15 a side), 0.6 deep (3 layers) -
    reMixTape's first prints showed 0.4 deep barely reads.
Collar features follow the shell through collar.layer(); flat patterns (pockets, straps) are
projected along x onto the back.
"""
import math
import cadquery as cq
from geom import *          # noqa: F401,F403

O = SHELL_CLR + BAND_T      # the collar's outer surface, as a shell offset

DASH, PITCH, STITCH_H, STITCH_D = 3.0, 5.0, layers(0.8), 0.5
WAIST = (62.0, 77.4)                                      # waistband: stitched top and bottom, belt loops across it
STITCH_Z = [(63.2, 63.2 + STITCH_H), (75.4, 75.4 + STITCH_H)]
LOOP_Z, LOOP_W = (61.6, 78.2), 5.0
FRONT_SECTORS = [(44.0, 70.0), (-70.0, -44.0)]            # collar visible beside the display (ribs end at 38 deg)
BACK_SECTORS = [(112.0, 248.0)]
FRONT_LOOPS = [57.0, -57.0]
BACK_LOOPS = [150.0, 210.0]                               # clear of the spring slots' 45 deg points (up to z 66.8 at 120/180/240)
CUFF_H = layers(4.2)
POCKET = dict(y=37.6, w=24.0, top=58.0, side=46.0, point=34.0, stitch_in=2.0)   # point at 45 deg: its edges print as walls
STRAPS = [((30.0, 124.0), (-26.0, 79.0)), ((-30.0, 124.0), (26.0, 79.0))]   # (top y, z), (bottom y, z) projected on the back
STRAP_W = 11.0
BUTTON_D = 8.0


def _c():
    import collar
    return collar


def sector(a0, a1, z0, z1, r=115.0, n=24):
    pts = [(0.0, 0.0)] + [(r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(pts).close().extrude(z1 - z0)


def spokes(angles, half_w, z0, z1, r0=50.0, r1=115.0):
    """Many radial strips in one extrude (they never overlap)."""
    wp = cq.Workplane("XY", origin=(0, 0, z0))
    for a in angles:
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        corners = [(r0, -half_w), (r1, -half_w), (r1, half_w), (r0, half_w)]
        wp = wp.polyline([(x * c - y * s, x * s + y * c) for x, y in corners]).close()
    return wp.extrude(z1 - z0)


def dash_angles(sectors, avoid=(), r=80.0, avoid_deg=4.0):
    step = math.degrees(PITCH / r)
    out = []
    for a0, a1 in sectors:
        n = int((a1 - a0) / step)
        for i in range(n + 1):
            a = a0 + i * step
            if all(abs((a - v + 180) % 360 - 180) > avoid_deg for v in avoid):
                out.append(a)
    return out


def waistband(sectors, loops):
    c = _c()
    adds, cuts = [], []
    ang = dash_angles(sectors, avoid=loops)
    for z0, z1 in STITCH_Z:
        cuts.append(c.layer(spokes(ang, DASH / 2, z0, z1), O - STITCH_D, O + 0.5))
    adds.append(c.layer(spokes(loops, LOOP_W / 2, *LOOP_Z), O - 0.3, O + lines(3)))
    # a half-height step under each loop: two 0.63 mm ledges at 45 deg instead of one 1.26 mm cantilever
    step = LOOP_Z[0] - lines(3) / 2
    adds.append(c.layer(spokes(loops, LOOP_W / 2, step, LOOP_Z[0] + 0.05), O - 0.3, O + lines(3) / 2))
    return adds, cuts


# ------------------------------------------------------------------ front half (R)
def front():
    c = _c()
    adds, cuts = waistband(FRONT_SECTORS, FRONT_LOOPS)
    zb = c.z_bed()
    cuff = None
    for a0, a1 in FRONT_SECTORS:
        s = sector(a0, a1, zb, zb + CUFF_H)
        cuff = s if cuff is None else cuff.union(s)
    adds.append(c.layer(cuff, O - 0.3, O + lines(2)))                       # rolled cuff ridge, on the bed
    return adds, cuts


# ------------------------------------------------------------------ backstrap (R)
def yz_prism(pts, x0=-125.0, x1=-10.0):
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)


def pentagon(yc):
    p = POCKET
    hw = p["w"] / 2
    return [(yc - hw, p["top"]), (yc + hw, p["top"]), (yc + hw, p["side"]), (yc, p["point"]), (yc - hw, p["side"])]


def back():
    c = _c()
    adds, cuts = waistband(BACK_SECTORS, BACK_LOOPS)
    # back pockets: a raised patch with a stitched seam inset from its edge
    for yc in (POCKET["y"], -POCKET["y"]):
        pts = pentagon(yc)
        adds.append(c.layer(yz_prism(pts), O - 0.3, O + lines(2)))
        outer = cq.Workplane("YZ", origin=(-125.0, 0, 0)).polyline(pts).close().offset2D(-POCKET["stitch_in"]).extrude(115.0)
        inner = cq.Workplane("YZ", origin=(-126.0, 0, 0)).polyline(pts).close().offset2D(-POCKET["stitch_in"] - lines(2)).extrude(117.0)
        cuts.append(c.layer(outer.cut(inner), O + lines(2) - STITCH_D, O + lines(2) + 0.5))
    # crossed straps with a button at each lower end
    for (yt, zt), (ybt, zbt) in STRAPS:
        hw = STRAP_W / 2
        # the strap's lower end is a 45 deg point (a flat end is a cantilever in the upright print)
        adds.append(c.layer(yz_prism([(yt - hw, zt + 1.0), (yt + hw, zt + 1.0), (ybt + hw, zbt + hw), (ybt, zbt), (ybt - hw, zbt + hw)]),
                            O - 0.3, O + lines(3)))
        # edge stitching: a groove 1.6 in from each long edge of the strap (to its top face depth)
        for s in (-1, 1):
            e0, e1 = s * (hw - 1.6 - lines(2)), s * (hw - 1.6)
            lo, hi = min(e0, e1), max(e0, e1)
            g = yz_prism([(yt + lo, zt + 1.0), (yt + hi, zt + 1.0), (ybt + hi, zbt + 5.0), (ybt + lo, zbt + 5.0)])
            cuts.append(c.layer(g, O + lines(3) - STITCH_D, O + lines(3) + 0.5))
        # teardrop button (a circle with a 45 deg point below): every side face prints at 45 deg or steeper
        r, zc = BUTTON_D / 2, zbt + 2.0 + 1.0
        btn = cq.Workplane("YZ", origin=(-125.0, 0, 0)).center(ybt, zc).circle(r).extrude(115.0)
        tip = [(ybt - r / math.sqrt(2), zc - r / math.sqrt(2)), (ybt + r / math.sqrt(2), zc - r / math.sqrt(2)), (ybt, zc - r * math.sqrt(2))]
        btn = btn.union(cq.Workplane("YZ", origin=(-125.0, 0, 0)).polyline(tip).close().extrude(115.0))
        adds.append(c.layer(btn, O - 0.3, O + lines(4)))
        zbt = zbt + 1.0                                     # the holes below follow the button's centre
        holes = cq.Workplane("YZ", origin=(-125.0, 0, 0)).pushPoints([(ybt - 1.4, zbt + 2.0), (ybt + 1.4, zbt + 2.0)]).circle(0.65).extrude(115.0)
        cuts.append(c.layer(holes, O + lines(4) - 0.8, O + lines(4) + 0.5))
    return adds, cuts


# ------------------------------------------------------------------ tray ends (B)
BUCKLE = dict(y=(Y_BACK + PART_Y) / 2, strap_w=10.0, w=13.0, z0=25.0, z1=34.0, bar=lines(3), button_d=5.0)


def dress_tray(t):
    """An overalls strap coming down each end of the bib into a buckle with a button in it."""
    b = BUCKLE
    top = CZ1 - TOP_SEAM_CLR
    for xo, s in ((OX0, -1), (OX1, 1)):
        def slab(d0, d1, y0, y1, z0, z1):
            return box(xo + s * d0, xo + s * d1, y0, y1, z0, z1)
        yc = b["y"]
        # the strap starts 1 mm above the button (z1 - 1.0) and stops 1 mm below the tray's top: at
        # z1 - 2.0 its underside was exactly tangent to the button's top (z 32.0), which meshed with
        # 2 non-manifold edges
        t = t.union(slab(-0.05, lines(2), yc - b["strap_w"] / 2, yc + b["strap_w"] / 2, b["z1"] - 1.0, top - 1.0))
        frame = slab(-0.05, lines(3), yc - b["w"] / 2, yc + b["w"] / 2, b["z0"], b["z1"])
        frame = frame.cut(slab(0.02, 3.0, yc - b["w"] / 2 + b["bar"], yc + b["w"] / 2 - b["bar"], b["z0"] + b["bar"], b["z1"] - b["bar"]))
        # 45 deg wedge under the frame's bottom bar: in the upright print a flat underside is a 1.26 mm cantilever
        wedge = [(xo - s * 0.05, b["z0"] + 0.05), (xo + s * lines(3), b["z0"] + 0.05), (xo - s * 0.05, b["z0"] - lines(3) - 0.05)]
        frame = frame.union(cq.Workplane("XZ", origin=(0, yc + b["w"] / 2, 0)).polyline(wedge).close().extrude(b["w"]))
        t = t.union(frame)
        # the button inside the buckle is engraved into the wall (a proud disc's underside would overhang)
        zc = (b["z0"] + b["z1"]) / 2
        ring = cq.Workplane("YZ", origin=(xo + s * 0.05, 0, 0)).center(yc, zc).circle(b["button_d"] / 2).circle(b["button_d"] / 2 - lines(2))
        t = t.cut(ring.extrude(-s * 0.55))
        holes = cq.Workplane("YZ", origin=(xo + s * 0.05, 0, 0)).pushPoints([(yc - 1.0, zc), (yc + 1.0, zc)]).circle(0.5)
        t = t.cut(holes.extrude(-s * 0.85))
    return t


# ------------------------------------------------------------------ bezel face (B)
BEZEL_STITCH_IN, BEZEL_LINE, BEZEL_DEPTH = 3.0, 1.0, layers(0.6)


def dress_bezel(b):
    """Engraved: a dashed stitch round the bib, two bib buttons above the window, a heart below it."""
    y_top = Y_FACE + 0.05
    depth = BEZEL_DEPTH + 0.05
    wp = lambda: cq.Workplane("XZ", origin=(0, y_top, 0))              # extrudes toward -y, into the face
    xl, xr = OX0 + BEZEL_STITCH_IN, OX1 - BEZEL_STITCH_IN
    zl, zt = OZ0 + BEZEL_STITCH_IN, OZ1 - BEZEL_STITCH_IN
    heart_gap = 6.0
    hor = []
    x = xl + 2.0
    while x + DASH < xr - 1.0:
        xc = x + DASH / 2
        hor.append((xc, zt))
        if abs(xc) > heart_gap:
            hor.append((xc, zl))
        x += PITCH
    ver = []
    z = zl + 2.0
    while z + DASH < zt - 1.0:
        ver += [(xl, z + DASH / 2), (xr, z + DASH / 2)]
        z += PITCH
    b = b.cut(wp().pushPoints(hor).rect(DASH, BEZEL_LINE).extrude(depth))
    b = b.cut(wp().pushPoints(ver).rect(BEZEL_LINE, DASH).extrude(depth))
    # bib buttons: an engraved ring with two holes, in the top border
    ax0, ax1, az0, az1 = ACTIVE
    zc = ((az1 + 0.5 + 1.2) + (OZ1 - EDGE_CHAMFER)) / 2 - 1.0
    for xc in (OX0 + 24.0, OX1 - 24.0):
        b = b.cut(wp().center(xc, zc).circle(4.0).circle(4.0 - BEZEL_LINE).extrude(depth))
        b = b.cut(wp().pushPoints([(xc - 1.3, zc), (xc + 1.3, zc)]).circle(0.75).extrude(layers(1.0) + 0.05))
    # a heart centred in the bottom border
    zh = ((az0 - 0.5 - 1.2) + (OZ0 + EDGE_CHAMFER)) / 2
    heart = wp().pushPoints([(-1.45, zh + 0.9), (1.45, zh + 0.9)]).circle(1.7).extrude(depth)
    heart = heart.union(wp().polyline([(-3.1, zh + 0.6), (3.1, zh + 0.6), (0.0, zh - 2.9)]).close().extrude(depth))
    b = b.cut(heart)
    return b
