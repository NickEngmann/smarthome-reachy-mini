# Reachy Mini dungarees: a CrowPanel 7" P4 enclosure

This is a three-part, screwless, 3D-printed enclosure for the **Elecrow CrowPanel Advanced 7" ESP32-P4**. It clamps onto **Reachy Mini's front belly** and is dressed as **denim dungarees**: the display is the bib, and the collar is the waistband. It turns with the body and needs no changes to the robot. The display's software lives in the sibling repo `../smarthome-reachy-mini-display`.

The toolchain follows reMixTape (`reMixTape/re-MixedTape/hardware/enclosure`) and Luna (`luna/luna-hardware/hardware/enclosure_v2`): cadquery scripts, an interference check against the board STEP, mesh and layer checks, a Bambu Studio project writer, and headless slicing with the Bambu Studio CLI.

## Commands
Run these with `python`, the ESP-IDF 3.11 interpreter (cadquery 2.8, numpy, scipy).

```
python shell.py                  # once: Reachy shell proxy -> out/cache/
python enclosure.py              # build + export all parts (~12 min)  [--plain: no dungarees detail]
python collar.py --check-only    # fit checks on the exported STEPs (exit 1 on failure)
python check_mesh.py             # every exported STL watertight
python islands.py                # layer scan: floating islands (what the slicer calls "floating regions")
python islands.py --overhangs    # layer scan: cantilever/bridge regions with locations
python bambu.py --slice          # out/bambu/*.3mf + overhang audit + Bambu Studio CLI slice (time, grams, warnings)
python probe.py                  # diagnostic: re-slice with supports on critical regions, report where they touch
python render.py                 # out/render/*.png
```
After a build, everything below `enclosure.py` reads only its exports, so run those together rather than one after another. `python enclosure.py --check` builds and checks in one go (slower).

## Parts

| Part | Prints | Function | Dungarees detail |
|---|---|---|---|
| **bezel** | face down | Window over the active area. A full-depth top wall holds the **microSD slot**. A snap lip with bumps hangs from a shelf on the plate on three sides. Bosses hold the board down, with sockets for the tray's locating pegs. | Dashed stitch round the bib, two bib buttons above the screen, and a heart below it. All are engraved, because a face-down print can't have raised detail. |
| **tray-cradle** | upright | The tray has **2× USB-C windows** with 45°-roofed overmold recesses and a **switch slot** on one end. The floor has **BOOT/RESET flex tabs** (rooted below, 45° pointed tops) plus LED and mic holes. Four standoffs carry **locating pegs** through the board's M3 holes, and relief channels above the USB-C windows let the connectors slide down past the wall. Behind the tray, ribs bear on the belly and the front half of the waistband ends in a side-joint strip. | A strap, buckle and engraved button on each end of the bib, a stitched waistband, belt loops and a rolled cuff. |
| **backstrap** | upright | The rest of the collar. At each side, a tongue carries two flex tabs whose hooks click into windows in the strip. Three **spring tabs** preload the collar, and a **cable gutter** runs along the bottom. | Crossed back straps with edge stitching and teardrop buttons, two back pockets, a waistband with belt loops, and side buttons. The gutter doubles as the cuff. |

## Printing (Bambu Lab X1C)

The two projects are ready to open in Bambu Studio: `out/bambu/*.3mf`. Settings start from your saved X1C project (`bambu/project_settings.json`, taken from luna-hardware): 0.4 mm nozzle, textured PEI, 0.20 mm Standard. Filament is Bambu's own **PETG Basic @BBL X1C** preset.

| Project | Plate | Per-part settings |
|---|---|---|
| `reachy-dungarees-tray-cradle.3mf` | the tray-cradle upright, as it sits on the robot | 5 mm outer brim |
| `reachy-dungarees-bezel-backstrap.3mf` | the bezel face down (textured PEI gives the bib a fabric-like finish), with the backstrap upright and turned 90° beside it | backstrap: 5 mm outer brim |

Common process settings:
- **Walls and infill:** 3 walls (the collar band is solid), 5 top and 4 bottom layers, 20 % gyroid.
- **Seam and ironing:** aligned seams, no ironing.
- **Supports:** none anywhere.
- **Elephant foot:** 0.15 mm compensation, so the engraving and the joint's sliding faces stay clean.

Latest CLI slice, before the final fixes below:

| Project | Time | PETG | Supports | Slicer warning |
|---|---|---|---|---|
| tray-cradle | 4 h 50 | 152 g | none | none |
| bezel + backstrap | 3 h 42 | 115 g | none | "floating cantilever" on the backstrap (being located with `probe.py`) |

**Colour:** a denim-blue PETG. With an AMS, add a height-range filament change on the upright parts for a brown cuff (z 0–4) and waistband (z 32–48 on the plate).

### Print checks and what they changed
Every geometry change is checked four ways: the fit check, `check_mesh.py`, `islands.py` (floating islands, then overhang regions), and a Bambu Studio CLI slice. `probe.py` turns support on for critical regions only and reports where the slicer puts it, which is how its warnings were traced to a part and a height. Fixes made for printing:

- **Bezel lip shelf.** The lip used to hang from the parting plane with a 2.4 mm gap to the plate, held only by the top wall and bosses. Face down, it would have printed as one long bridge in mid-air. It now hangs from a shelf on the plate.
- **BOOT/RESET flex tabs.** They are rooted below and grow upward. Rooted at the side, their lower edge was a 10 mm cantilever over the slit; that was the tray-cradle's slicer warning.
- **Spring tabs.** The slot and the tab close at the top in a 45° point instead of a flat top slit. The flat slit's roof was a 15 mm curved bridge, 2.5 mm thick with air on both faces, and Bambu Studio flagged it as a "floating cantilever" on the backstrap. `bisect_backstrap.py` found it in two rounds:
  - Round 1: of six variants with one feature group removed, only the one without springs sliced clean.
  - Round 2: flat springs without their nubs still warned, while gable-topped springs with nubs sliced clean.

  The back belt loops moved to 150° and 210° to clear the points.
- **Side buttons.** They are sunk 1 mm into the tongue and shaped as teardrops. At 0.3 mm deep their lowest layers floated; that was the backstrap's "floating regions" warning.
- **Other 45° undersides:** joint hooks (with windows 0.6 mm taller to clear them), teardrop strap buttons, pointed strap ends, a half step under the belt loops, pocket points, overmold recess roofs, and a wedge under the buckle frame. Buckle buttons are now engraved.
- **Mesh fixes:** the collar band stops 0.4 mm behind the tray back, and the tray-end straps no longer touch the button or the tray top. Each of these left faces that only touched, which meshed with non-manifold edges.
- **Fit review before the first print (v0.4).**
  - **Board location:** the locating pegs moved from the bezel to the tray standoffs. With the pegs on the bezel, the board could float ±1.1 mm while hidden pegs, which capture only about 0.7 mm, had to find its holes.
  - **USB-C:** relief channels added above the windows. The shells stood 0.1 mm from the wall while the board went in.
  - **Clearances:** boss-to-board gap 0.2 → 0.4, top-edge clearance 1.5 → 2.0 and collar-to-shell 1.5 (was 1.0).
  - **Snap engagement:** bump engagement 0.45 → 0.40.
  - **Flexures:** slits 0.84 → 1.0 with 45° pointed tops on every flexure; BOOT/RESET tabs thinned to 0.84 mm (about 12 N → 4 N).
  - **Spring nubs:** chamfered on all four sides.
  - **New checks:** `collar.py --check-only` now also checks the assembly paths, not only final positions: the board lifted out of the tray, the tray-cradle backed off the belly, and the backstrap pulled back off the robot and the tray-cradle.
- **Plate placement.** The print STLs are set on the plate by their tessellated vertices. OCC's bounding box of the lofted collar was loose, and the STLs floated.

## Load: why it stays put
- **The load is small.** The display (≤450 g) plus the enclosure (~260 g PETG) sits about 20 mm in front of where the ribs bear on the belly. Stopping it tipping forward takes only about 2 N at the collar top.
- **It can't slide.** The collar runs from z 30 to z 124, across the belly's widest ring (r 77.4 at z 60). It is 3 mm narrower above (r 74.3 at z 120) and 4 mm narrower below (r 73.4 at z 30), so it can't pass the bulge either way.
- **The joints are full height.** Each side has two flex tabs over 94 mm of height.
  - Each tab is 10 × 2.1 × 22 mm and deflects 0.6 mm to engage: 0.39 % strain and about 2.6 N per tab.
  - Every joint surface is extruded along x, so the backstrap slides straight on.
  - To release, lift each tab by its pull lip.
- **Spring preload.** Three U-slot spring tabs press their nubs 1.2 mm into the shell, about 3 N each. The nubs have 45° sides all round, so they ride up onto the shell as the backstrap slides on instead of catching on an edge. The ribs seat on the belly, and the collar's 1.5 mm clearance never becomes rattle.
- **Remaining limit:** at full body yaw, the display's front corners sweep a radius of about 135 mm, and the extra mass makes body turns slower.

## Tolerances: Bambu X1C, 0.4 mm nozzle, 0.20 mm layers, PETG
Every fit is one of these classes (`geom.py`). Walls are whole line widths (`lines(n)` × 0.42 mm), and heights stacked in a part's print Z are whole layers (`layers()`).

| Class | Value | Used for |
|---|---|---|
| `FIT_SNAP` | 0.40 / side | Bezel lip to tray wall (reMixTape printed 0.2 on this printer; +0.2 wiggle room). Bumps are 0.80, so they engage 0.40 past the wall face, as on reMixTape. Pockets are +0.3 deep and +1.6 wide. |
| `FIT_SLIDE` | 0.40 / side | Backstrap tongue over the front strip |
| `FIT_Z` | 0.40 (2 layers) | Any gap across layers: glass to bezel plate, lip to PCB, tray top to bezel top wall |
| `FIT_CATCH` | 0.30 | Play at a snap's catch face (the springs take it up); +0.8 on the free side of each window |
| `HOLE_H_EXTRA` | +0.30 | Holes lying flat in an upright print get a teardrop roof; pins lying flat are teardrops, point down. |
| Locating pegs | Ø2.4 teardrop pins on the tray standoffs (point clipped to R1.45, 2.4 mm past the board, 45° tip); Ø3.4 sockets with a lead-in in the bezel bosses | 0.4 / side in the board's Ø3.2 holes. The board sits on its pegs before the bezel goes on, so nothing has to find a hidden hole. |
| Boss to board | 0.4 (2 layers) | The bezel never binds on a thick board or a fat print (was 0.2) |
| Board to wall | 0.75 / 1.1 / 2.0 | Sides / USB-C end (plus 0.6 mm relief channels above the USB-C windows, so the connectors, which stand 1.0 mm past the board edge, slide past the wall) / top edge (the flex cables wrap it; was 1.5) |
| Flexure slits | 1.0, 45° pointed tops | Joint tabs, spring tabs and BOOT/RESET tabs: no bridged slit roof sits above a flexure where it could sag and fuse (was 0.84) |
| Shell | 1.5 collar, 0.4 ribs | The shell is Pollen's CAD mesh, not measured on the robot, and a tight collar would mean a reprint (was 1.0). The ribs set the position and the springs remove the play. |
| Openings | USB-C 10.2 × 5.6 (overmold recess 13.4 × 7.8), switch 11 × 5.6, microSD 13.4 × 3.2 | |
| Walls | tray 2.1 (5 lines), collar 2.52 (6), tongue 2.1 (5), strip 1.26 (3), ribs 4.2 (10) | |
| Detail, upright | proud 0.84 / 1.26 / 1.68; grooves 0.84 × 0.5 deep; stitch dashes 0.8 tall (4 layers); every underside at 45° or steeper | |
| Detail, bezel face | engraved 1.0 wide × 0.6 deep | |

## Assembly
1. Lower the board, glass up, onto the tray's four locating pegs. Start at the USB-C end, so the connectors slide down the relief channels into their windows. The board then sits on its standoffs without moving.
2. Press the bezel on until the bumps click; its boss sockets drop over the peg tips. To open it, pry at the notch at the bottom centre.
3. Put the tray-cradle against Reachy's belly. The front half of the waistband slides on from the front.
4. Slide the backstrap on from behind. The spring nubs drag on the shell, and the four joint tabs click into their windows.
5. To take it off, lift the four tabs by their pull lips and slide the backstrap back.

Cable:
- **Outside power:** plug either USB-C port directly.
- **From Reachy:** lay the cable in the back gutter and down to the foot port, with slack for the body's ±180° yaw.

## Frames
- **Board frame B** is Elecrow's STEP frame: x long, +y is the glass side, z is up.
- **Robot frame R**: +X front, +Y robot's left, Z up, 0 at the table.
- The transform is R = T(X0,0,Z0)·Ry(−6°)·Rz(−90°)·B. `placement()` puts the tray's lowest back edge at z 30, with the tray back 2.5 mm from the shell at the closest point. Board centre: robot X 97.4, Z 86.3.

## Status (2026-09-12, v0.3 print-ready candidate — not yet printed)
Final run (`enclosure.py`, then `collar.py --check-only`, `check_mesh.py`, `islands.py`, `bambu.py --slice` and `render.py` side by side): **everything passes, and both plates slice with no warnings and no supports.**

| Part | Volume | Robot-frame extent (mm) | Checks |
|---|---|---|---|
| bezel | 26.0 cm³ | x 74.8…107.4, y −91.3…91.6, z 31.8…142.0 | clear of all 55 board solids; watertight; no floating islands |
| tray-cradle | 135.4 cm³ | x −16.0…103.1, y −92.6…92.9, z 30.0…139.1 | clear of board; watertight; no floating islands |
| backstrap | 75.2 cm³ | x −86.0…11.2, y ±84.3, z 30.0…125.0 | watertight; no floating islands |

- **Fit check: passed.** Overlaps are 0.000 mm³ for bezel/tray, tray-cradle/backstrap (the hooks sit in their windows), bezel/backstrap, and each part against the shell. The spring nubs' 65 mm³ overlap with the shell is the intended 1.2 mm preload.
- **Mesh check: passed.** All six STLs (as modelled and as printed) have 0 open edges and 100 % consistent normals.
- **Island scan: clean** on all three parts. The overhang scan's remaining "cantilever" regions are ledges of 1.0–1.8 mm (window corners, buckle bars, loop steps), which PETG prints unsupported.

| Project | Time | PETG | Supports | Slicer warnings |
|---|---|---|---|---|
| `reachy-dungarees-tray-cradle.3mf` | 4 h 50 | 152 g | none | none |
| `reachy-dungarees-bezel-backstrap.3mf` | 3 h 42 | 115 g | none | none |

Total: about 8 h 32 and 267 g of PETG.

## Open risks — check on the first print
- **Collar and spring feel.** If the backstrap is too hard to slide on, reduce `PRELOAD`; if the collar is loose, raise it.
- **Slide switch (MST22D18G2):** the actuator sits 1.35 mm inside the board edge, so it needs a fingernail or pen tip. A captive slider cap would be a v2.
- **microSD** is push-push, about 4 mm inside the wall, so a pen tip may be needed.
- **BOOT/RESET tabs** are 0.84 mm flexures with a 0.6 mm gap to the switch (about 4 N at the tip).
- **Mics:** their port side isn't known, so there are holes front and back.
- **The optional camera module** isn't accommodated.
- **Antennas:** by Pollen's sleep-pose drawing, the antennas pass about 14 mm outside the collar top. Check this on the robot.
- **Reachy's USB-C output:** check it supplies enough current for the display before relying on it.
