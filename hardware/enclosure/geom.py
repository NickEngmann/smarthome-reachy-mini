"""Constants, frames and helpers shared by enclosure.py, collar.py, outfit.py and render.py.

Frames
  B (board): Elecrow's STEP frame. x = long axis, y = toward the viewer (glass +y),
             z = short axis (up in use), origin at the board centre. Every board fact
             below is in B, read from the STEP's named components (board_components.txt).
  R (robot): Reachy Mini. +X front, +Y robot's left, Z up, 0 = table.
             R = T(X0, 0, Z0) . Ry(-TILT) . Rz(-90) . B   ->  robot X = board y,
             robot Y = -board x, robot Z = board z (before the tilt).
The tray and bezel are modelled in B; the cradle, collar and joints in R.

Printer: Bambu X1C, 0.4 mm nozzle, 0.20 mm Standard profile, PETG. Every fit below is one
of the FIT_* classes, printed walls are whole line widths (lines()), and heights that stack
in the print's Z are whole layers (layers()).
"""
import math, functools
import cadquery as cq

# ------------------------------------------------------------- printer: Bambu X1C
NOZZLE, LINE, LAYER = 0.40, 0.42, 0.20       # Bambu's default line width for a 0.4 nozzle


def lines(n):
    """A wall n extrusion lines thick."""
    return round(n * LINE, 2)


def layers(h):
    """h rounded UP to whole layers."""
    return round(math.ceil(h / LAYER - 1e-6) * LAYER, 2)


FIT_SNAP = 0.40       # snap lip to wall, per side (reMixTape printed 0.2 on this X1C: +0.2 wiggle room)
FIT_SLIDE = 0.40      # faces that slide past each other (joint tongue over its strip)
FIT_Z = 0.40          # any gap that lies across layers: two layers, never one
FIT_CATCH = 0.30      # play at a snap's catch face (the springs take it up)
HOLE_H_EXTRA = 0.30   # holes whose axis lies flat in the print come out small and sag: +0.3 and a teardrop roof
PEG_UNDER = 0.20      # pegs and bosses print fat: a Ø3.2 board hole gets a Ø2.6 peg (0.3 a side)

# ---------------------------------------------------------------- board facts (B, mm)
BX0, BX1, BZ0, BZ1 = -88.45, 88.45, -52.0, 52.0          # PCB outline (176.9 x 104.0)
PCB_Y0, PCB_Y1 = -5.7, -4.0                               # PCB back / top faces
GLASS = (-82.45, 82.45, -50.0, 50.0, 2.0)                 # touch glass x0 x1 z0 z1, front y
ACTIVE = (-78.83, 75.38, -45.12, 40.80)                   # LCD active face (154.2 x 85.9)
HOLES = [(-85.45, -49.0), (85.45, -49.0), (-85.45, 49.0), (85.45, 49.0)]   # M3, Ø3.2
BACK_MIN_Y = -13.8                                        # deepest back component (U4 PH2.0 SMD pair)
USB_C = [dict(z=-10.47, y=-6.78), dict(z=10.47, y=-6.78)]  # USB-C-SMD_TYPE-C-6PIN-2MD: x -89.45..-81.87, 8.94 x 4.16
SWITCH = dict(z=-27.44, y=-8.13)                          # SW-SMD_MST22D18G2 slide, actuator 1.35 inside the edge
BUTTONS = [(84.2, 20.25), (84.2, 34.75)]                  # SW-SMD_4P 4.5x4.5 tact, plunger faces -y, top at y -10.2
BUTTON_TOP_Y = -10.2
SD = dict(x=69.08, y=-6.43)                               # TF-SMD x 61..77.15, y -7.75..-5.1, opens toward +z (top edge)
MICS = [(-85.09, -40.12), (85.09, -40.12)]                # PDM mics on the back; port side unknown -> holes both faces
LEDS = [(-86.05, 0.0), (-81.25, 0.0)]                     # status LEDs on the back

# ------------------------------------------------------------ enclosure numbers (B)
CLR = 0.75            # board edge to wall (bottom, right)
CLR_L = 1.1           # left end: the USB-C shells stand 1.0 past the PCB edge
CLR_TOP = 2.0         # top edge: the LCD and touch flexes wrap round it, and the bezel's top wall slides past them (was 1.5)
WALL, FLOOR = lines(5), lines(5)                          # 2.1
TOP = layers(2.0)                                         # bezel plate, 10 layers (prints face down)
BACK_CLR = 1.0        # deepest component to the floor
CX0, CX1 = BX0 - CLR_L, BX1 + CLR                         # cavity
CZ0, CZ1 = BZ0 - CLR, BZ1 + CLR_TOP
OX0, OX1, OZ0, OZ1 = CX0 - WALL, CX1 + WALL, CZ0 - WALL, CZ1 + WALL   # outline (OZ1 = bezel top wall)
FLOOR_IN = BACK_MIN_Y - BACK_CLR                          # -14.8
Y_BACK = FLOOR_IN - FLOOR                                 # -16.9, tray back face
PLATE_IN = GLASS[4] + FIT_Z                               # bezel plate inner face, 2 layers off the glass
Y_FACE = PLATE_IN + TOP                                   # bezel face (the print bed for the bezel)
LIP_T, LIP_H, LIP_CLR = lines(3), layers(3.6), FIT_SNAP
PART_Y = PCB_Y1 + FIT_Z + LIP_H                           # parting plane: the lip ends 2 layers above the PCB
CORNER_R = 2.0
TOP_SEAM_CLR = FIT_Z  # tray walls stop this short of the bezel's top wall
# snap bumps on the bezel's lip, pockets in the tray: 0.45 mm engagement past the wall face
# Bumps are 45 deg on both faces: push-on and pull-off take about the same force, so the bezel can be
# removed without breaking anything (a flat catch can only be pried, which shears bumps).
BUMP_W, BUMP_H = 8.0, layers(1.8)
BUMP_D = LIP_CLR + 0.40      # 0.40 past the wall face: reMixTape's printed PETG engagement (was 0.45)
BUMP_Y0 = PART_Y - LIP_H + 0.6   # above the lip's 0.4 lead-in chamfer (a 45 deg face 0.05 off the bump's own)
POCKET_DEPTH_EXTRA, POCKET_Y_EXTRA, POCKET_W_EXTRA = 0.30, 0.40, 1.6
# Side walls only. The bottom wall is fused to the cradle's filler block and cannot flex, so a bump there
# would strain the lip ~15 %; the bottom lip only locates. z +-40 and 0 keep clear of the USB-C openings,
# the switch slot and the buckle frames on the end walls.
BUMPS = [("L", 40.0), ("L", -40.0), ("R", 40.0), ("R", 0.0), ("R", -40.0)]
# posts: the TRAY standoffs carry the locating pegs, so the board drops onto them and stays put while the
# bezel goes on (reMixTape's proven order). With the pegs on the bezel the board could float +-1.1 mm in
# its cavity while four hidden pegs had to find their holes, and a peg captures only ~0.7 mm.
STANDOFF_D = 6.8
PEG_D = 2.4            # teardrop pin (point down: it prints horizontal); 0.4 a side in the board's Ø3.2 hole
PEG_POINT_R = 1.45     # teardrop point clipped to this radius: 2.65 mm tall in the Ø3.2 hole
PEG_THROUGH = 1.4      # pin length past the PCB top face, into the bezel socket (was 2.4)
PEG_TIP = 0.6          # 45 deg cone at the tip
# Bezel sockets are slots, longer in z: the face-down bezel shrinks in its own plane (~0.2-0.3 % over the
# 98 mm hole pitch) while the upright tray's pitch lies in its print Z, so the bottom sockets would ride up
# onto the peg points. Bosses are ovals, longer in z too, because x is limited by the glass edge 0.5 mm away.
SOCKET_D, SOCKET_H = 3.4, 4.2
SOCKET_DEPTH = PEG_THROUGH + 1.0
BOSS_D, BOSS_H = 5.0, 5.8
BOSS_GAP = LAYER       # 0.2: boss end to the PCB top. The PCB's 1.7 mm is already in the stack-up; 0.4 only added rattle
# openings (all widened for the print; a plug's overmold gets a recess)
# USB-C: the plug-overmold opening runs through the whole wall (14 x 8.2 z x y), so an overmold reaches
# within ~0.1 mm of the receptacle mouth. A 1.4 mm blind recess stopped it 0.8 mm short and left a 0.1 mm
# web next to the relief channel.
USB_OPEN_W, USB_OPEN_H, USB_OPEN_R = 14.0, 8.2, 2.2
USB_RELIEF_D = 0.6    # channel in the wall's inner face above each opening: the shells stand 1.0 past the PCB edge, 0.1 from the wall
USB_RELIEF_W = 9.4    # the 8.94 shell + 0.23 a side; stays inside the opening's straight edge (14 - 2 x 2.2 = 9.6)
SWITCH_SLOT = (11.0, 5.6, 1.2)                            # z x y, radius: fingernail / pen slot
SD_SLOT = (12.0, 1.6)                                     # x x y: guides a 1 mm card into the socket (3.2 let it drop into the cavity)
SD_LEADIN = 0.8                                           # 45 deg chamfer outside
EDGE_CHAMFER = 0.6
# BOOT / RESET: pin holes (a paperclip or SIM tool), as on reMixTape. Flex tabs bent across the layer lines
# of the upright print at 4-6 % strain and would crack.
BUTTON_HOLE_D, BUTTON_HOLE_CSK = 3.0, 4.6
MIC_HOLE_D, LED_HOLE_D = 2.0, 2.2                         # Ø1.2 printed closed to ~0.9
LEADIN_LIP = 0.4                                          # 45 deg chamfer on the bezel lip's free edge

# ------------------------------------------------------------------ placement (R)
TILT = 6.0            # deg, top leans back: follows the shell, screen faces slightly up
GAP = 2.5             # closest tray back to shell (measured rings): the spline proxy bulges ~0.7 between rings
Z_BED_TARGET = 30.0   # lowest point of the tray-cradle print (tray bottom, collar bottom)

# ------------------------------------------------------------------ collar (R)
SHELL_CLR = 1.5       # collar to shell: the real shell is unmeasured (Pollen CAD mesh) and a tight collar is a reprint; the springs take up the slack (was 1.0)
RIB_CLR = 0.4         # ribs bear on the shell and set where the display sits
BAND_T = lines(6)     # 2.52
BAND_TOP = Z_BED_TARGET + layers(94.0)                    # 124: well above the belly's widest ring -> taper-locked
RIB_BX = [-50.0, -25.0, 0.0, 25.0, 50.0]                  # rib positions along the board's x (robot -Y)
RIB_T = lines(10)
# side joint, +Y side (mirrored for -Y). The collar splits near +/-90 deg. The front half ends in a
# thin STRIP extruded along x (so the backstrap can slide along x over it); the backstrap ends in a
# TONGUE plate outside the strip, with two vertical flex tabs whose hooks drop into windows in the strip.
SPLIT_F_X = 12.0      # front band exists for x >= this
SPLIT_B_X = -18.0     # backstrap band for x <= this
STRIP_X, STRIP_T, STRIP_MARGIN = (-16.0, 14.0), lines(3), 0.4
TONGUE_X, TONGUE_T = (-26.0, 11.2), lines(5)
WEDGE_X = (-26.0, -17.0)
JOINT_GAP = FIT_SLIDE
TABS = [(40.0, 62.0), (88.0, 110.0)]                      # (root z, tip z) of each flex tab
TAB_X, SLIT = (-10.0, 0.0), 1.0     # flexure slits 1.0 (was 0.84: PETG ooze and fat perimeters can close a 2-line gap)
HOOK_X, HOOK_H, HOOK_D = (-9.0, -3.0), layers(4.8), 1.0
PULL_LIP = lines(2)   # 0.84: only 0.6 mm of lift releases a hook; a bigger lip invites lifting 2-3 mm (1.3-2 % strain across layers)
LEADIN_JOINT = 0.8    # 45 deg chamfers where the tongue's front edge meets the strip's rear edge
SIDE_BUTTONS = [(6.0, 50.0), (6.0, 98.0)]
# spring tabs in the backstrap: U-slot flexures with an inward nub, preloading the collar
SPRINGS = [180.0, 120.0, 240.0]                           # deg
# Spring tabs 1.26 thick (band 2.52 thinned by 1.26) and longer (z 37-62). The nub reach adds the play the
# collar loses when it seats (ribs RIB_CLR onto the belly + hook FIT_CATCH), projected on each nub's
# direction: 1.9 mm at 180 deg, 1.55 at 120/240, so ~1.2 mm remains once seated (~0.6 % strain).
SPRING_Z, SPRING_W, SPRING_THIN, PRELOAD, NUB_W = (37.0, 62.0), 12.0, lines(3), 1.2, 5.0
GUTTER = dict(w=6.0, t=lines(4), h=6.0, x_max=-28.0)      # cable gutter along the backstrap's bottom


def rot_b_to_r(v):
    """Rotate a B-frame vector into R (no translation)."""
    x, y, z = v
    x, y = y, -x                                          # Rz(-90)
    t = math.radians(-TILT)
    return (x * math.cos(t) + z * math.sin(t), y, -x * math.sin(t) + z * math.cos(t))


@functools.lru_cache(maxsize=1)
def placement():
    """(X0, Z0): Z0 puts the tray's lowest back edge at Z_BED_TARGET, X0 puts the tray back
    GAP in front of the shell at its closest point."""
    import shell
    prof = shell.profile()
    lo = rot_b_to_r((0.0, Y_BACK, OZ0))
    Z0 = Z_BED_TARGET - lo[2]
    X0 = -1e9
    for bz in [OZ0 + i * (OZ1 - OZ0) / 40 for i in range(41)]:
        for bx in [OX0 + i * (OX1 - OX0) / 60 for i in range(61)]:
            p = rot_b_to_r((bx, Y_BACK, bz))
            zr, yr = Z0 + p[2], p[1]
            if zr < 12 or zr > 150:
                continue
            best = None
            for k in range(-85, 86):
                th = math.radians(k)
                r = shell.radius_at(prof, zr, k)
                if abs(r * math.sin(th) - yr) < 1.2 and math.cos(th) > 0:
                    xs = r * math.cos(th)
                    best = xs if best is None else max(best, xs)
            if best is not None:
                X0 = max(X0, best + GAP - p[0])
    return X0, Z0


def to_robot(wp):
    X0, Z0 = placement()
    return (wp.rotate((0, 0, 0), (0, 0, 1), -90).rotate((0, 0, 0), (0, 1, 0), -TILT).translate((X0, 0, Z0)))


def pt_robot(b):
    X0, Z0 = placement()
    p = rot_b_to_r(b)
    return (p[0] + X0, p[1], p[2] + Z0)


# ------------------------------------------------------------------------ helpers
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().add(cq.Solid.makeBox(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0),
                                               cq.Vector(min(x0, x1), min(y0, y1), min(z0, z1))))


def cyl_y(cx, cz, d, y0, y1):
    """Cylinder along y from y0 to y1."""
    return cq.Workplane().add(cq.Solid.makeCylinder(d / 2, abs(y1 - y0), cq.Vector(cx, min(y0, y1), cz), cq.Vector(0, 1, 0)))


def cyl_x(cy, cz, d, x0, x1):
    return cq.Workplane().add(cq.Solid.makeCylinder(d / 2, abs(x1 - x0), cq.Vector(min(x0, x1), cy, cz), cq.Vector(1, 0, 0)))


def cone_y(cx, cz, d0, d1, y0, y1):
    return cq.Workplane().add(cq.Solid.makeCone(d0 / 2, d1 / 2, abs(y1 - y0), cq.Vector(cx, y0, cz),
                                                cq.Vector(0, 1 if y1 > y0 else -1, 0)))


def teardrop_y(cx, cz, d, y0, y1, up=False):
    """Cylinder along y with a 45 deg point: down (-z) for a solid boss whose underside would
    sag, up (+z) for a hole whose roof would. Board z is up in the upright print."""
    c = cyl_y(cx, cz, d, y0, y1)
    r, s = d / 2, (1 if up else -1)
    k = r * math.sqrt(2)
    tri = (cq.Workplane("XZ", origin=(0, max(y0, y1), 0))
           .polyline([(cx - r / math.sqrt(2), cz + s * r / math.sqrt(2)), (cx + r / math.sqrt(2), cz + s * r / math.sqrt(2)), (cx, cz + s * k)]).close()
           .extrude(abs(y1 - y0)))
    return c.union(tri)
