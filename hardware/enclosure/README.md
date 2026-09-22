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
python overalls.py [--check]     # the two optional bib straps (~1 min); --check-only for the fits
python render_overalls.py        # out/render/overalls-*.png
```
After a build, everything below `enclosure.py` reads only its exports, so the checks can run side by side. Run `bambu.py --slice` on its own, though: with the other checks competing for the CPU, a slice of the tray-cradle ran past 25 minutes. `python enclosure.py --check` builds and checks in one go (slower).

## Parts

| Part | Prints | Function | Dungarees detail |
|---|---|---|---|
| **bezel** | face down | Window over the active area. A full-depth top wall holds the **microSD slot**. A snap lip hangs from a shelf on the plate on three sides, with 45° bumps on the two ends. Oval bosses hold the board down, with slot sockets for the tray's locating pegs. | Dashed stitch round the bib, two bib buttons above the screen, and a heart below it. All are engraved, because a face-down print can't have raised detail. |
| **tray-cradle** | upright | The tray has **2× USB-C openings** sized for a plug's overmold and a **switch slot** on one end. The floor has **BOOT/RESET pin holes** plus LED and mic holes. Four standoffs carry **locating pegs** through the board's M3 holes, and relief channels above the USB-C windows let the connectors slide down past the wall. Behind the tray, ribs bear on the belly and the front half of the waistband ends in a side-joint strip. | A strap, buckle and engraved button on each end of the bib, a stitched waistband, belt loops and a rolled cuff. |
| **backstrap** | upright | The rest of the collar. At each side, a tongue carries two flex tabs whose hooks click into windows in the strip. Three **spring tabs** preload the collar, and a **cable gutter** runs along the bottom. | Crossed back straps with edge stitching and teardrop buttons, two back pockets, a waistband with belt loops, and side buttons. The gutter doubles as the cuff. |
| **bib-strap ×2** | on its side | **Optional, cosmetic.** Hangs over the robot's own front rim, runs down the outside of the shell, and drops into the gap behind the display, where a foot sits in the pocket between two of the cradle's ribs. The other three parts are untouched. | The two shoulder straps of the dungarees, 14 × 2.1 mm with edge stitching, completing the crossed straps already moulded on the backstrap. |

## Bib straps

Two small clip-on prints (`overalls.py`), added after the first three were done. They are what makes
the robot read as *wearing* the dungarees rather than carrying a bib: from the front a strap comes
over each shoulder and disappears behind the panel. Nothing touches the bib's face, and nothing
about the bezel, tray-cradle or backstrap changes — lift the straps off and the enclosure is exactly
as it was.

```
python overalls.py [--plain]         # build and export the pair (~1 min)  [--plain: no stitching]
python overalls.py --check-only      # fit checks against the exported STEPs
python render_overalls.py            # 3-D views + sections -> out/render/overalls-*.png
python render_overalls.py --section  # just the sections (seconds: no 3-D painting)
```

`overalls-section*.png` are the pictures that actually show the fit: every part cut by a plane just
off the strap's centre and drawn filled, so the rim hook on the shell's top edge, the 1.5 mm the run
stands off the body and the foot in its pocket are geometry rather than a claim. A 3-D render of a 2 mm strap against a curved shell cannot show a 1 mm gap. There is no tight
3-D close-up of either hook for the same reason: `render.py` depth-sorts one collection by centroid,
which breaks down at close range on the shell's coarse triangles.

Each strap is four lofted pieces unioned, sliced every 1 mm so each slice follows the body at its
own Y. Its weight goes into the cradle's two rib tops through the foot's shoulders; the rim hook
only keeps the top against the shell, and nothing has to grip anything.

| Piece | What it does |
|---|---|
| rim hook | A loose C over the shell's top edge: a 4.5 mm slot over a ~2 mm rim, reaching 3 mm down inside. Deliberately loose — a tight slot on a rim known only from CAD is a reprint, and the foot is what holds the strap. |
| shell run | Inner face at `SHELL_CLR` (1.5 mm) off the body's front, from z 150 up to the rim. |
| gap run | Leaves the shell at z 152 and leans forward into the gap behind the panel. |
| **foot** | Two **shoulders** resting on the cradle's own **rib tops**, and a **tongue** hanging into the slot between those ribs. This is the mount — see below. |

**Where it can go, and why** (robot frame, all measured):

- **The mount is a pocket that was already there.** The ribs at |Y| 25 and 50 (4.2 thick) leave a
  slot **27.10…47.90**, 20.80 wide, and their tops are a flat plane at board z 53.6 — robot Z 137.86
  at the panel's back face, sloping to 137.0 eight mm behind it. The gap between the shell and the
  panel's back there is **9.6–10.9 mm** over Z 118…140. So: the shoulders bed on the rib tops, the
  tongue drops into the slot, and the panel's back and the shell take it fore-and-aft. Nothing was
  added to the cradle, and nothing about it changed.
- **The tongue stops 6 mm down, clear of the collar.** Resting on the collar band was the first
  idea and it is wrong: the band's top edge sweeps 6.6 mm in X across the pocket as it follows the
  shell (X 72.05…75.11 at Y 28.5, but 65.21…68.46 at Y 46.5), so a flat-bottomed foot would have
  borne on about a millimetre of it at one end and missed it entirely at the other.
- **The strap is flush with the foot's inboard edge**, centred on |Y| 31.5 rather than 37.5. That is
  a printing constraint, not a styling one — see "Printing" below.
- **The microSD is not a constraint here.** It opens through the bezel's top wall at |Y| 62…76, well
  outboard of the strap. It *was* the constraint for the rejected front-clip version.
- **Head clearance.** Above the front rim the whole robot stays inside X 41.5…43.2 (full mesh,
  z 185…196) while the rim itself is at X 51…55 — about 12 mm of clear space just inside it. The
  measured distance from the rim hook to anything above z 184 and inboard of X 46 is **7.52 mm**.
  That is Pollen's CAD in the URDF zero pose, **not a measured head sweep**: check it on the robot.

**Rejected on the way**, so it is not tried again: straps clipped to the *front* of the bib and
rising above the display. The display's top corners sit 43 mm in front of the body, so such a strap
either spans that gap as a strut or stops in mid-air — three variants were built and rendered, and
none read as a strap from the side. Straps hanging *below* the display have nowhere to go either:
the enclosure's cuff ends at z 30 and the robot's turning foot starts at z 22, and the foot does not
yaw with the body.

## Printing (Bambu Lab X1C)

The three projects are ready to open in Bambu Studio: `out/bambu/*.3mf`. Settings start from your saved X1C project (`bambu/project_settings.json`, taken from luna-hardware): 0.4 mm nozzle, textured PEI, 0.20 mm Standard. Filament is Bambu's own **PETG Basic @BBL X1C** preset.

| Project | Plate | Per-part settings |
|---|---|---|
| `reachy-dungarees-tray-cradle.3mf` | the tray-cradle upright, as it sits on the robot | 5 mm outer brim |
| `reachy-dungarees-bezel-backstrap.3mf` | the bezel face down (textured PEI gives the bib a fabric-like finish), with the backstrap upright and turned 90° beside it | backstrap: 5 mm outer brim |
| `reachy-dungarees-bib-straps.3mf` | both bib straps on their sides, profile flat on the plate and the Y width as the print Z (each turned so **its own** flush edge is down) | 5 mm outer brim each |

`bambu.py --only <substring>` writes and slices just the projects whose name matches, so a change
to one plate does not re-time the others.

Common process settings:
- **Walls and infill:** 3 walls (the collar band is solid), 5 top and 4 bottom layers, 20 % gyroid.
- **Seam and ironing:** aligned seams, no ironing.
- **Supports:** none anywhere.
- **Elephant foot:** 0.15 mm compensation, so the engraving and the joint's sliding faces stay clean.

Latest CLI slice (v0.5):

| Project | Time | PETG | Supports | Slicer warning |
|---|---|---|---|---|
| tray-cradle | 4 h 52 | 152 g | none | none |
| bezel + backstrap | 3 h 42 | 114 g | none | none |
| bib straps (both) | 39 min | 6.0 g | none | none |

**Colour:** a denim-blue PETG. With an AMS, add a height-range filament change on the upright parts for a brown cuff (z 0–4) and waistband (z 32–48 on the plate).

### Print checks and what they changed
Every geometry change is checked four ways: the fit check, `check_mesh.py`, `islands.py` (floating islands, then overhang regions), and a Bambu Studio CLI slice. `probe.py` turns support on for critical regions only and reports where the slicer puts it, which is how its warnings were traced to a part and a height. Fixes made for printing:

- **Bezel lip shelf.** The lip used to hang from the parting plane with a 2.4 mm gap to the plate, held only by the top wall and bosses. Face down, it would have printed as one long bridge in mid-air. It now hangs from a shelf on the plate.
- **BOOT/RESET flex tabs** (since replaced by pin holes, see v0.5). Rooted at the side, their lower edge was a 10 mm cantilever over the slit; that was the tray-cradle's slicer warning.
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
- **Independent fit review (v0.5).** A second reviewer went over v0.4 for anything that would force a reprint. Changes:
  - **Snap bumps:** the bottom bumps are gone. The tray's bottom wall is fused to the cradle filler and can't flex, so a bump there would have strained the lip about 15 %; the bottom lip now only locates. There are five bumps on the two end walls instead (z ±40 and 0 on the right, clear of the USB-C openings and the switch). Both faces are 45°, so the bezel pulls off without prying. The pockets let the bezel lift 0.3 mm (was 0.6).
  - **BOOT/RESET:** Ø3 pin holes with a countersink, pressed with a paperclip. The flex tabs bent across the layer lines at 4–6 % strain, and a pointed slot top left a 0.7 mm web between the two tabs.
  - **USB-C:** the overmold opening (14 × 8.2) runs through the whole wall, so a plug seats fully. The blind recess stopped the overmold 0.8 mm short and left a 0.1 mm web.
  - **Pegs and sockets:** pegs go 1.4 mm past the board (was 2.4). The bezel sockets are 3.4 × 4.2 slots in 5.0 × 5.8 oval bosses. Face down, the bezel shrinks in its own plane while the upright tray's hole pitch doesn't, so round sockets could have ridden up onto the peg points. The boss-to-board gap is back to 0.2: the board thickness was already in the stack-up.
  - **Spring preload:** the nubs reach 1.2 mm plus the play the collar loses as it seats (1.9 mm at the back, 1.55 mm at 120°/240°). Tabs are 1.26 thick and 25 mm long, so the remaining 1.2 mm is about 0.6 % strain.
  - **microSD:** the slot is 12 × 1.6 with a 45° lead-in, so a card can't drop into the case (was 13.4 × 3.2).
  - **Mics:** Ø2.0 teardrop holes (Ø1.2 prints closed).
  - **Lead-ins:** a 0.4 mm chamfer on the bezel lip's free edge, and 0.8 mm chamfers where the tongue meets the strip. The joint pull lips are 0.84 mm proud (was 1.68): only 0.6 mm of lift releases a hook.
  - **Mesh:** the right back strap's edge stitches ended 0.1 mm inside its button and tore the mesh (794 open edges). They now stop 1.5 mm above it. Waistband stitch dashes keep clear of the spring slots.
  - **Checks:** the path sweeps now run the backstrap 100 mm back and the tray-cradle 60 mm off the belly in finer steps, and add the bezel lifted off the tray and board.
- **Plate placement.** The print STLs are set on the plate by their tessellated vertices. OCC's bounding box of the lofted collar was loose, and the STLs floated.

## Load: why it stays put
- **The load is small.** The display (≤450 g) plus the enclosure (~260 g PETG) sits about 20 mm in front of where the ribs bear on the belly. Stopping it tipping forward takes only about 2 N at the collar top.
- **It can't slide.** The collar runs from z 30 to z 124, across the belly's widest ring (r 77.4 at z 60). It is 3 mm narrower above (r 74.3 at z 120) and 4 mm narrower below (r 73.4 at z 30), so it can't pass the bulge either way.
- **The joints are full height.** Each side has two flex tabs over 94 mm of height.
  - Each tab is 10 × 2.1 × 22 mm and deflects 0.6 mm to engage: 0.39 % strain and about 2.6 N per tab.
  - Every joint surface is extruded along x, so the backstrap slides straight on.
  - To release, lift each tab by its pull lip.
- **Spring preload.** Three U-slot spring tabs press their nubs into the shell. They reach 1.2 mm plus the play the collar loses as it seats, so about 1.2 mm of preload remains once seated. The nubs have 45° sides all round, so they ride up onto the shell as the backstrap slides on instead of catching on an edge. The ribs seat on the belly, and the collar's 1.5 mm clearance never becomes rattle.
- **Remaining limit:** at full body yaw, the display's front corners sweep a radius of about 135 mm, and the extra mass makes body turns slower.

## Tolerances: Bambu X1C, 0.4 mm nozzle, 0.20 mm layers, PETG
Every fit is one of these classes (`geom.py`). Walls are whole line widths (`lines(n)` × 0.42 mm), and heights stacked in a part's print Z are whole layers (`layers()`).

| Class | Value | Used for |
|---|---|---|
| `FIT_SNAP` | 0.40 / side | Bezel lip to tray wall (reMixTape printed 0.2 on this printer; +0.2 wiggle room). Bumps are 0.80 with 45° faces both ways, so they engage 0.40 past the wall face, as on reMixTape. Pockets are +0.3 deep and +1.6 wide. |
| `FIT_SLIDE` | 0.40 / side | Backstrap tongue over the front strip |
| `FIT_Z` | 0.40 (2 layers) | Any gap across layers: glass to bezel plate, lip to PCB, tray top to bezel top wall |
| `FIT_CATCH` | 0.30 | Play at a snap's catch face (the springs take it up); +0.8 on the free side of each window |
| `HOLE_H_EXTRA` | +0.30 | Holes lying flat in an upright print get a teardrop roof; pins lying flat are teardrops, point down. |
| Locating pegs | Ø2.4 teardrop pins on the tray standoffs (point clipped to R1.45, 1.4 mm past the board, 45° tip); 3.4 × 4.2 slot sockets (long in z) in 5.0 × 5.8 oval bezel bosses | 0.4 / side in the board's Ø3.2 holes. The board sits on its pegs before the bezel goes on, so nothing has to find a hidden hole. The slots absorb the face-down bezel's in-plane shrink. |
| Boss to board | 0.2 (1 layer) | Holds the board down without rattle |
| Board to wall | 0.75 / 1.1 / 2.0 | Sides / USB-C end (plus 0.6 × 9.4 mm relief channels above the USB-C openings, so the connectors, which stand 1.0 mm past the board edge, slide past the wall) / top edge (the flex cables wrap it; was 1.5) |
| Flexure slits | 1.0, 45° pointed tops | Joint tabs and spring tabs: no bridged slit roof sits above a flexure where it could sag and fuse (was 0.84) |
| Shell | 1.5 collar, 0.4 ribs | The shell is Pollen's CAD mesh, not measured on the robot, and a tight collar would mean a reprint (was 1.0). The ribs set the position and the springs remove the play. |
| Openings | USB-C 14 × 8.2 through the wall (R2.2), switch 11 × 5.6, microSD 12 × 1.6 with a 0.8 lead-in, BOOT/RESET Ø3.0 (countersunk Ø4.6), mics Ø2.0 teardrop | |
| Lead-ins | 0.4 × 45° on the bezel lip's free edge; 0.8 × 45° on the strip's rear outer edge and the tongue's front inner edge | |
| Walls | tray 2.1 (5 lines), collar 2.52 (6), tongue 2.1 (5), strip 1.26 (3), ribs 4.2 (10) | |
| Detail, upright | proud 0.84 / 1.26 / 1.68; grooves 0.84 × 0.5 deep; stitch dashes 0.8 tall (4 layers); every underside at 45° or steeper | |
| Detail, bezel face | engraved 1.0 wide × 0.6 deep | |

## Assembly
1. Lower the board, glass up, onto the tray's four locating pegs. Start at the USB-C end, so the connectors slide down the relief channels into their windows. The board then sits on its standoffs without moving.
2. Press the bezel on at the bench, before the tray-cradle goes on the robot, until the bumps click. Its boss sockets drop over the peg tips. To open it, pull it straight off: the bumps are 45° both ways. The notch at the bottom centre gives a fingernail a start.
3. Put the tray-cradle against Reachy's belly. The front half of the waistband slides on from the front.
4. Slide the backstrap on from behind. The spring nubs drag on the shell, and the four joint tabs click into their windows.
5. To take it off, lift the four tabs by their pull lips (1 mm is enough) and slide the backstrap back.
6. **Bib straps, if you printed them.** Last, and by hand. Lower each one into the gap behind the
   display so its foot drops into the slot between the ribs — the wedge finds the slot on its own —
   until the two shoulders bed on the rib tops. Then lay the top of the strap over the shell's front
   rim until the C seats on it. There is nothing to click; lift it straight out to remove. They come
   off before the bezel does.

Cable:
- **Outside power:** plug either USB-C port directly.
- **From Reachy:** lay the cable in the back gutter and down to the foot port, with slack for the body's ±180° yaw.

## Frames
- **Board frame B** is Elecrow's STEP frame: x long, +y is the glass side, z is up.
- **Robot frame R**: +X front, +Y robot's left, Z up, 0 at the table.
- The transform is R = T(X0,0,Z0)·Ry(−6°)·Rz(−90°)·B. `placement()` puts the tray's lowest back edge at z 30, with the tray back 2.5 mm from the shell at the closest point. Board centre: robot X 97.4, Z 86.3.

## Status (2026-09-13, v0.5 print-ready candidate — not yet printed)
Final run after the independent fit review (`enclosure.py`, then `collar.py --check-only`, `check_mesh.py`, `islands.py`, `bambu.py` and `render.py`, then `bambu.py --slice` on its own): **everything passes, and both plates slice with no warnings and no supports.**

| Part | Volume | Robot-frame extent (mm) | Checks |
|---|---|---|---|
| bezel | 26.0 cm³ | x 74.7…107.4, y −91.3…91.6, z 31.8…142.5 | clear of all 55 board solids; watertight; no floating islands |
| tray-cradle | 134.9 cm³ | x −16.0…103.1, y −92.6…92.9, z 30.0…139.6 | clear of board; watertight; no floating islands |
| backstrap | 73.5 cm³ | x −86.5…11.2, y ±84.2, z 30.0…125.0 | watertight; no floating islands, no cantilever or bridge regions |

- **Fit check: passed.** Overlaps are 0.000 mm³ for bezel/tray, tray-cradle/backstrap (the hooks sit in their windows), bezel/backstrap, and each part against the shell. The spring nubs' 82.6 mm³ overlap with the shell is the intended preload plus the seating play.
- **Assembly paths: passed** at every step: the board lifted 0.5–16 mm out of the tray, the bezel (bumps removed) lifted 0.5–8 mm off the tray and board, the tray-cradle backed 1–60 mm off the belly, and the backstrap pulled 1–100 mm back past the shell and the tray-cradle.
- **Mesh check: passed.** All six STLs (as modelled and as printed) have 0 open edges and 100 % consistent normals.
- **Island scan: clean** on all three parts. The overhang scan's remaining regions are short bridges (1–6 mm: the microSD slot roof, the pry notch, loop steps), which PETG prints unsupported.

| Project | Time | PETG | Supports | Slicer warnings |
|---|---|---|---|---|
| `reachy-dungarees-tray-cradle.3mf` | 4 h 52 | 152 g | none | none |
| `reachy-dungarees-bezel-backstrap.3mf` | 3 h 42 | 114 g | none | none |

Total: about 8 h 34 and 266 g of PETG.

### Bib straps (2026-09-21, v2 — not yet printed)
Added without touching the three parts above: `overalls.py`, then `overalls.py --check-only`,
`check_mesh.py`, `islands.py`, `islands.py --overhangs`, `bambu.py --only bib-straps --slice`.
**Everything passes and the plate slices with no warnings and no supports.**

| Part | Volume | Robot-frame extent (mm) | Checks |
|---|---|---|---|
| bib-strap-left | 2.49 cm³ | x 47.9…75.0, y 24.5…50.5, z 131.4…186.0 | watertight; no floating islands |
| bib-strap-right | 2.49 cm³ | mirrored in y | identical — it is the left one mirrored, not a second build |

- **Fit check: passed.** 0.000 mm³ against the bezel, the tray-cradle and the backstrap on both
  sides, and 0.000 mm³ against the shell proxy below z 139.
- **Against the body above the display**, measured point-to-triangle on Pollen's mesh: the run's
  closest approach is **1.23 mm** (0 of 3,141 points inside the shell wall) and the rim hook's is
  **0.66 mm** (0 of 1,395). The rim hook to anything above z 184 and inboard of X 46 is **7.52 mm**.
- **Mesh check: passed.** All four STLs, 0 open edges, 100 % normals.
- **Island scan: clean**, and 91 mm² over 45° with 135 mm² on the plate. Getting there took two
  fixes the slicer found and CAD did not — see "Print checks" below.
- **Section through the strap: one closed loop**, so it is continuous from the rim hook to the foot
  — `out/render/overalls-section.png`, with the rim hook and the foot enlarged beside it.

**Print checks and what they changed (bib straps).** The part prints as a prism extruded along
robot Y, so **robot Y is the print's vertical** — which inverts the intuition about overhangs, and
cost two rounds:

- **The foot is 26 mm wide and the strap 14.** Centred, the strap's whole outline — the run and
  the rim hook, 50 mm of it — began 6 mm above the plate with nothing under it: "floating
  cantilever", 214 mm² of overhang and **20 mm² on the plate**. The strap is now flush with the
  foot's inboard edge, so every outline starts at the plate and the part only loses material going
  up: 44 mm² of overhang, 135 mm² on the plate. Each side is turned so its own flush edge is down.
- **The tongue's side taper was 81° in the part and 8° in the print.** A side that drops 10 mm over
  1.5 mm of Y looks nearly vertical in CAD; in the print it crosses 10 mm of plate while the nozzle
  rises 1.5. Still a cantilever, 8.4 mm of reach. The tongue is now a 45° wedge — 1 mm of drop per
  1 mm of width, 6 mm deep, the full 20 mm across at the rib plane and 8 mm at the bottom.

Neither showed up in `islands.py`, which reported CLEAN both times: it finds regions with nothing
at all beneath them, and these had a sliver of contact. The slicer's own warning found both.

| Project | Time | PETG | Supports | Slicer warnings |
|---|---|---|---|---|
| `reachy-dungarees-bib-straps.3mf` | 39 min | 6.0 g | none | none |

**2026-09-20, handover check.** `check_mesh.py` re-run against the exports exactly as they stand:
all six STLs pass, 0 open edges, normals 100 % (backstrap 74.69 cm³, bezel 25.99, tray-cradle
135.34). The printable results are now **committed** - `out/print/*.stl`, `out/bambu/*.3mf` and
`out/render/*.png` - so the repo can be printed from without a 12-minute rebuild; `out/step`,
`out/stl` and the slicer diagnostics stay out of git, as `.gitignore` says. Nothing was reprinted or
re-sliced, and v0.5 still has never been printed.

## Open risks — check on the first print
- **Collar and spring feel.** If the backstrap is too hard to slide on, reduce `PRELOAD`; if the collar is loose, raise it.
- **Slide switch (MST22D18G2):** the actuator sits 1.35 mm inside the board edge, so it needs a fingernail or pen tip. A captive slider cap would be a v2.
- **microSD** is push-push, about 4 mm inside the wall, so a pen tip may be needed.
- **BOOT/RESET** are pressed through Ø3 pin holes with a paperclip or SIM tool.
- **Bezel retention.** Five 45° bumps hold the bezel by friction and flex, not by a hard catch. If it comes off too easily, raise `BUMP_D` by 0.1.
- **Mics:** their port side isn't known, so there are holes front and back.
- **The optional camera module** isn't accommodated.
- **Antennas:** by Pollen's sleep-pose drawing, the antennas pass about 14 mm outside the collar top. Check this on the robot.
- **Reachy's USB-C output:** check it supplies enough current for the display before relying on it.
- **Bib straps and the head.** The rim hook sits 7.52 mm from anything above the rim *in the URDF
  zero pose*. The head moves on its Stewart platform and this has not been checked against a real
  sweep. Watch it once with the straps on before leaving them there; if the head does come near,
  `RIM_DN` and `RIM_SLOT` set how far the hook reaches inside the rim. The front rim is the highest
  point of the body (z 184.8, against 139 at the sides), which is the reason to expect it is fine.
- **Bib strap retention.** Nothing clicks: the foot's shoulders sit on the rib tops and its tongue
  fills the slot between them, with the rim hook keeping the top against the shell. If one rattles,
  raise `FOOT_D` (the tongue is currently 5.5 mm deep, auto-clamped against the shell) or narrow
  `RIM_SLOT`. If a foot will not drop in, `FOOT_W` (20.0 in a 20.80 slot) is the number to shave.
- **The straps assume the shell's real rim matches Pollen's mesh.** The slot is 4.5 mm over a rim
  measured at ~2 mm for exactly that reason, but a much thicker rim would stop the hook seating.
