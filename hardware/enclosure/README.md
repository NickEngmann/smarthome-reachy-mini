# Reachy Mini dungarees: a CrowPanel 7" P4 enclosure

This is a three-part (plus two small pins), screwless, 3D-printed enclosure for the **Elecrow CrowPanel Advanced 7" ESP32-P4**. It clamps onto **Reachy Mini's front belly** and is dressed as **denim dungarees**: the display is the bib, and the collar is the waistband. It turns with the body and needs no changes to the robot. The display's software lives in the sibling repo `../smarthome-reachy-mini-display`.

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
| **tray-cradle** | upright | The tray has **2× USB-C openings** sized for a plug's overmold and a **switch slot** on one end. The floor has **BOOT/RESET pin holes** plus LED and mic holes. Four standoffs carry **locating pegs** through the board's M3 holes, and relief channels above the USB-C windows let the connectors slide down past the wall. Behind the tray, ribs bear on the belly and the front half of the waistband ends, on each side, in a plate with two rails, a stop, and a cap with the pin hole. | A strap, buckle and engraved button on each end of the bib, a stitched waistband, belt loops and a rolled cuff. |
| **backstrap** | upright | The rest of the collar. At each side, a tongue slides onto the plate's two rails and is locked by a pin dropped through the cap into a boss on the tongue (v0.6). Three **spring tabs** preload the collar, and a **cable gutter** runs along the bottom. | Crossed back straps with edge stitching and teardrop buttons, two back pockets, a waistband with belt loops, and side buttons. The gutter doubles as the cuff. |
| **pins ×2** | head down | The side joints' locks (v0.6): Ø4 × 25 mm with an 8 mm head, dropped through the tray-cradle's cap into the backstrap's boss on each side. They print on the bezel-backstrap plate. | Copper-coloured in the renders, like jeans rivets; print them in any colour. |
| **bib-strap ×2** | on its side | **Optional, cosmetic.** Hangs over the robot's own front rim, runs down the outside of the shell, and drops into the gap behind the display, where a foot fills the pocket between two of the cradle's ribs and a spring finger clamps it in place. The other three parts are untouched. | The two shoulder straps of the dungarees, 14 × 2.1 mm with edge stitching, completing the crossed straps already moulded on the backstrap. |

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
stands off the body and the spring finger's nub pressed into the collar band are geometry rather
than a claim. A 3-D render of a 2 mm strap against a curved shell cannot show a 1 mm gap. There is no tight
3-D close-up of either hook for the same reason: `render.py` depth-sorts one collection by centroid,
which breaks down at close range on the shell's coarse triangles.

Each strap is five lofted pieces unioned, sliced every 1 mm so each slice follows the body at its
own Y.

| Piece | What it does |
|---|---|
| rim hook | A loose C over the shell's top edge: a 4.5 mm slot over a ~2 mm rim, reaching 3 mm down inside. Deliberately loose — a tight slot on a rim known only from CAD is a reprint, and the foot is what holds the strap. |
| shell run | Inner face at `SHELL_CLR` (1.5 mm) off the body's front, from z 150 up to the rim. |
| gap run | Leaves the shell at z 152 and leans forward into the gap behind the panel. |
| **tongue** | Fills the slot between two of the cradle's ribs (20.0 in 20.80), 0.40 off the tray's back wall, down to 0.4 mm above the collar band's top edge (Z 124.4). Locates the strap side to side and stops it dropping. |
| **spring finger** | Outboard half only (|Y| 37.5…47.5). A 1.68 mm blade on down the tray's back wall into the slot between the wall and the collar band, to Z 92, with a nub at Z 104 pressing the band. This is what **holds** the strap. |

**v3 (2026-09-30): why the finger.** v2 was printed, and the owner had to hot-glue it in. Its two
shoulders sat on the rib tops and a short tongue hung in the slot — that *located* the strap but
nothing *held* it: there is no downward-facing ledge in the pocket to hook under, and a 3 g strap
on a turning robot walks out. The owner's sketch ran the foot on down behind the panel; v3 does that
and adds a spring, because depth alone still would not hold anything. The nub is modelled 1.2 mm
into the band: the strap first moves 0.40 forward until the tongue bears on the tray's back wall,
and the other 0.8 bends the finger. So the strap is **clamped between two faces of the tray-cradle
itself** and holds by friction. In this print orientation the finger bends along its layers, not
across them — the strong way for a printed spring.

**Where it can go, and why** (robot frame, all measured):

- **The mount is a pocket that was already there.** The ribs at |Y| 25 and 50 (4.2 thick) leave a
  slot **27.10…47.90**, 20.80 wide. Behind the tray's back wall, between those ribs, the free depth
  is 6.7 mm (inboard) to 15.7 mm (outboard) above Z 124, where the shell is what is behind it. Below
  Z 124 the collar band comes in: **1.3 mm** deep inboard, **8.8** outboard, and waisted, narrowest at
  about Z 108. Nothing was added to the cradle, and nothing about it changed.
- **Only the outboard half takes a spring.** Inboard of |Y| 37.5 the waist is under 3.95 mm, and the
  finger needs 3.28 (1.6 to bend into plus 1.68 of blade). There the tongue alone stops on the
  band's top edge.
- **The band is our own part, so it is exact.** `overalls.band_x` sections the same proxy
  `collar.band()` is made from; it agrees with an exact section of the exported STEP to 0.000 mm.
  The exported *STL* — which is what the slicer prints — sits up to **0.28 mm** inside it at the nub
  (collar.py's STL export uses cadquery's default relative tolerance, so its chords are coarse). The
  preload was raised from 0.6 to 0.8 for exactly that, and the check reports both.
- **The strap is flush with the foot's OUTBOARD edge**, centred on |Y| 40.5 (v2: inboard, 31.5).
  The finger only fits outboard, and in the print the outboard edge is the one on the plate — see
  "Print checks" below.
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
| `reachy-dungarees-bib-straps.3mf` | both bib straps on their sides, profile flat on the plate and the Y width as the print Z (each turned so **its own** flush edge is down) | 8 mm outer brim each; first layer 25 mm/s at 255 °C, textured plate 80 °C for the first layer and 75 °C after (adhesion — see below) |

`bambu.py --only <substring>` writes and slices just the projects whose name matches, so a change
to one plate does not re-time the others.

Common process settings:
- **Walls and infill:** 3 walls (the collar band is solid), 5 top and 4 bottom layers, 20 % gyroid.
- **Seam and ironing:** aligned seams, no ironing.
- **Supports:** none anywhere.
- **Elephant foot:** 0.15 mm compensation, so the engraving and the joint's sliding faces stay clean.
- **Bib straps, first-layer adhesion (2026-09-30).** The first v3 print would not stay on the plate
  and the PETG built up on the nozzle, with dry filament (6 % in the box), flow calibration and bed
  levelling all on. Each strap stands on a 284 mm² footprint of thin perimeters, so a line that
  does not bond gets dragged onto the nozzle. That plate alone now prints its first layer at
  25 mm/s (was 50, and 105 for its infill) and 255 °C (the preset's 245 was the coldest layer of the
  print), on a textured plate at 80 °C for the first layer and 75 °C after (preset 70), with an 8 mm
  brim (was 5). Before changing anything, wash the plate with dish soap and water and brush the
  nozzle clean while hot; if it still lifts, add a thin layer of glue stick. The straps have since been
  printed and work (owner, 2026-09-30).

Latest CLI slice:

| Project | Time | PETG | Supports | Slicer warning |
|---|---|---|---|---|
| tray-cradle (v0.6) | 5 h 14 | 162.5 g | none | none |
| bezel + backstrap + 2 joint pins (v0.6) | 4 h 00 | 124.1 g | none | none |
| bib straps (both, v3) | 41 min | 9.1 g | none | none |

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
- **The side joints are a rail-and-pin slide lock (v0.6).** v0.5's flex-tab hooks never clicked when printed and the joint had to be glued (owner, 2026-09-30); nothing in v0.6 has to flex.
  - Each side of the tray-cradle ends in a 2.1 mm plate with two rails (z 70 and 100) running along x. The backstrap's 2.94 mm tongue has matching grooves on its inner face, open at its front edge. A 2 mm funnel at each groove's mouth and a 45° taper on each rail's rear end let a rail find its groove from 2 mm out of line. The rails set the tongue's height and keep it on the plate.
  - The backstrap slides forward until the tongue's front edge meets a stop on the tray-cradle. There the two halves of a vertical hole line up: through a cap on the tray-cradle, above the band, and down into a boss on the tongue.
  - A Ø4 PETG pin dropped into that hole on each side is the lock. The collar's pull (the spring nubs push the backstrap back) goes through the pins, in shear. Pull the pins to take the backstrap off.
  - The rails are trapezoids, not dovetails, because of the upright print. A dovetail groove's roof would start at the tongue's face with nothing under it, a floating sliver the length of the groove. The tongue still can't leave its plate: the whole backstrap would have to move sideways, and its other tongue is up against the other plate.
  - Every joint surface is still extruded along x, so the backstrap slides straight on.
- **Spring preload.** Three U-slot spring tabs press their nubs into the shell. They reach 1.2 mm plus the play the collar loses as it seats, so about 1.2 mm of preload remains once seated. The nubs have 45° sides all round, so they ride up onto the shell as the backstrap slides on instead of catching on an edge. The ribs seat on the belly, and the collar's 1.5 mm clearance never becomes rattle.
- **Remaining limit:** at full body yaw, the display's front corners sweep a radius of about 135 mm, and the extra mass makes body turns slower.

## Tolerances: Bambu X1C, 0.4 mm nozzle, 0.20 mm layers, PETG
Every fit is one of these classes (`geom.py`). Walls are whole line widths (`lines(n)` × 0.42 mm), and heights stacked in a part's print Z are whole layers (`layers()`).

| Class | Value | Used for |
|---|---|---|
| `FIT_SNAP` | 0.40 / side | Bezel lip to tray wall (reMixTape printed 0.2 on this printer; +0.2 wiggle room). Bumps are 0.80 with 45° faces both ways, so they engage 0.40 past the wall face, as on reMixTape. Pockets are +0.3 deep and +1.6 wide. |
| `FIT_SLIDE` | 0.40 / side | Faces that slide past each other |
| `FIT_JOINT` | 0.50 / side | The side joint (v0.6): tongue over the side plate, each rail in its groove (normal to every face), the tongue's boss under the tray-cradle's cap. `FIT_SLIDE` + 0.1, because these are 94 mm tall, thin, curved walls printed upright, which warp more than the bezel lip `FIT_SLIDE` was proven on, and v0.5's 0.40 joint never went together. The pin locks the joint, so play in the rails costs nothing. |
| Joint pin | Ø4.0 pin in a Ø4.8 vertical hole | 0.4 a side, so a pin drops in even when the two parts sit 0.4 mm out of line sideways. The stop leaves the two halves of the hole 0.2 past alignment, well inside that. |
| `FIT_Z` | 0.40 (2 layers) | Any gap across layers: glass to bezel plate, lip to PCB, tray top to bezel top wall |
| `FIT_CATCH` | 0.30 | Play at the bezel's snap catch face |
| `HOLE_H_EXTRA` | +0.30 | Holes lying flat in an upright print get a teardrop roof; pins lying flat are teardrops, point down. |
| Locating pegs | Ø2.4 teardrop pins on the tray standoffs (point clipped to R1.45, 1.4 mm past the board, 45° tip); 3.4 × 4.2 slot sockets (long in z) in 5.0 × 5.8 oval bezel bosses | 0.4 / side in the board's Ø3.2 holes. The board sits on its pegs before the bezel goes on, so nothing has to find a hidden hole. The slots absorb the face-down bezel's in-plane shrink. |
| Boss to board | 0.2 (1 layer) | Holds the board down without rattle |
| Board to wall | 0.75 / 1.1 / 2.0 | Sides / USB-C end (plus 0.6 × 9.4 mm relief channels above the USB-C openings, so the connectors, which stand 1.0 mm past the board edge, slide past the wall) / top edge (the flex cables wrap it; was 1.5) |
| Flexure slits | 1.0, 45° pointed tops | Spring tabs: no bridged slit roof sits above a flexure where it could sag and fuse (was 0.84) |
| Shell | 1.5 collar, 0.4 ribs | The shell is Pollen's CAD mesh, not measured on the robot, and a tight collar would mean a reprint (was 1.0). The ribs set the position and the springs remove the play. |
| Openings | USB-C 14 × 8.2 through the wall (R2.2), switch 11 × 5.6, microSD 12 × 1.6 with a 0.8 lead-in, BOOT/RESET Ø3.0 (countersunk Ø4.6), mics Ø2.0 teardrop | |
| Lead-ins | 0.4 × 45° on the bezel lip's free edge; 0.8 × 45° on the side plate's rear outer edge and the tongue's front inner edge; 2.0 × 45° funnels at the groove mouths and 2.0 × 45° tapers on the rails' rear ends; 0.6 countersink on the pin holes and chamfer on the pin tips | |
| Walls | tray 2.1 (5 lines), collar 2.52 (6), tongue 2.94 (7), side plate 2.1 (5), ribs 4.2 (10); 1.68 (4) round each pin hole | |
| Detail, upright | proud 0.84 / 1.26 / 1.68; grooves 0.84 × 0.5 deep; stitch dashes 0.8 tall (4 layers); every underside at 45° or steeper | |
| Detail, bezel face | engraved 1.0 wide × 0.6 deep | |

## Assembly
1. Lower the board, glass up, onto the tray's four locating pegs. Start at the USB-C end, so the connectors slide down the relief channels into their windows. The board then sits on its standoffs without moving.
2. Press the bezel on at the bench, before the tray-cradle goes on the robot, until the bumps click. Its boss sockets drop over the peg tips. To open it, pull it straight off: the bumps are 45° both ways. The notch at the bottom centre gives a fingernail a start.
3. Put the tray-cradle against Reachy's belly. The front half of the waistband slides on from the front.
4. Slide the backstrap on from behind, level, so the tongues pass outside the tray-cradle's side plates. The grooves' funnels catch the rails; push it forward until the tongues stop (the spring nubs drag on the shell on the way). Holding it there, drop a pin into the hole on top of each side, head up.
5. To take it off, pull the two pins and slide the backstrap back.
6. **Bib straps, if you printed them.** Last, and by hand. Slide each one down the back of the
   tray, finger first, into the slot between the ribs — the chamfers find the slot — and keep
   pushing down along the tray's back wall. The nub rides over the collar band's top edge (the finger
   bends about 1.3 mm) and the strap stops when the tongue reaches the band. The rim hook drops over
   the shell's front rim on the way down. To remove, pull it straight up along the tray's back wall.
   They come off before the bezel does.

Cable:
- **Outside power:** plug either USB-C port directly.
- **From Reachy:** lay the cable in the back gutter and down to the foot port, with slack for the body's ±180° yaw.

## Frames
- **Board frame B** is Elecrow's STEP frame: x long, +y is the glass side, z is up.
- **Robot frame R**: +X front, +Y robot's left, Z up, 0 at the table.
- The transform is R = T(X0,0,Z0)·Ry(−6°)·Rz(−90°)·B. `placement()` puts the tray's lowest back edge at z 30, with the tray back 2.5 mm from the shell at the closest point. Board centre: robot X 97.4, Z 86.3.

## Status (2026-09-30, v0.6: rail-and-pin side joints, not yet printed)
v0.5 was printed. Its bezel, tray and collar fit, but its side joints never clicked: the hooks on
the tongues' hidden inner faces never caught in the strip's windows, and the joint had to be glued
(owner). v0.6 replaces the joint with rails, a stop and a drop-in pin on each side. Everything else
is unchanged. The run was `enclosure.py --check`, then `collar.py --check-only` (after fixing one
check), `check_mesh.py`, `islands.py` (both modes) and `render.py`, then `bambu.py --only … --slice`
on each plate on its own. **Everything passes, and both plates slice with no warnings and no supports.**

| Part | Volume | Robot-frame extent (mm) | Checks |
|---|---|---|---|
| bezel | 26.0 cm³ | x 74.7…107.4, y −91.3…91.6, z 31.8…142.5 | unchanged; clear of all 55 board solids; watertight |
| tray-cradle | 144.6 cm³ | x −16.0…103.1, y −92.6…92.9, z 30.0…139.6 | clear of board; watertight; no floating islands |
| backstrap | 82.8 cm³ | x −86.5…11.2, y ±88.2, z 30.0…134.3 | watertight; no floating islands |
| pins (2) | 0.8 cm³ | x −6.0…2.0, y ±88.1, z 112.6…139.6 (as fitted) | watertight; no islands, no overhang regions |

- **Fit check: passed.** 0.000 mm³ for bezel/tray, tray-cradle/backstrap, bezel/backstrap, each part against the shell, and the pins against both parts. The spring nubs overlap the shell by 119.7 mm³ (was 82.6), because they now also reach across the pin's 0.8 mm of play.
- **Assembly paths: passed.** Board and bezel as before, and the tray-cradle backs 1–60 mm off the belly. The backstrap pulls 0.5–100 mm back along the rails, past the shell and the tray-cradle, with 0.000 mm³ at every step.
- **Positive controls.** These prove the zero readings above can see contact at all:
  - Pushed 0.4 mm forward of seated, the backstrap meets the stop (80.7 mm³).
  - A rod 0.3 mm wider than the pin hole hits both parts (59.2 mm³ tray-cradle, 169.6 mm³ backstrap), so the pin really passes through both.
  - The pins lift 2–30 mm straight out without touching anything.
- **Mesh check: passed.** All twelve STLs (as modelled and as printed, the pins and bib straps included) have 0 open edges and 100 % normals.
- **Island scan: clean** on every part. In the overhang scan, the tray-cradle's regions are the same nine ≤1.8 mm ledges as v0.5. The backstrap has one 0.8 mm-reach, 1.2 mm² region at each lower groove's mouth, and the slicer did not flag it.
- **One check fixed on the way.** The "pin passes through the part" control first grew the *pin* by 0.3 mm. That still fits a Ø4.8 hole, so it read 0 and failed. It now grows the *hole* by 0.3 mm.

| Project | Time | PETG | Supports | Slicer warnings |
|---|---|---|---|---|
| `reachy-dungarees-tray-cradle.3mf` | 5 h 14 | 162.5 g | none | none |
| `reachy-dungarees-bezel-backstrap.3mf` (with the two pins) | 4 h 00 | 124.1 g | none | none |

Total: about 9 h 14 and 287 g of PETG (v0.5: 8 h 34, 266 g). Both plates must be reprinted: both halves of the joint changed.

## Previous status (2026-09-13, v0.5, printed; side joints did not work)
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

### Bib straps (2026-09-30, v3 — PRINTED and working, no glue (owner, 2026-09-30); v2 needed hot glue)
Added without touching the three parts above: `overalls.py`, then `overalls.py --check-only`,
`check_mesh.py`, `islands.py`, `islands.py --overhangs`, `bambu.py --only bib-straps --slice`.
**Everything passes and the plate slices with no warnings and no supports.**

| Part | Volume | Robot-frame extent (mm) | Checks |
|---|---|---|---|
| bib-strap-left | 4.01 cm³ | x 44.2…78.1, y 27.5…47.5, z 92.0…183.7 | watertight; no floating islands |
| bib-strap-right | 4.01 cm³ | mirrored in y | identical — it is the left one mirrored, not a second build |

- **Fit check: passed**, with the nub (the intended preload) taken off first: 0.000 mm³ against
  the bezel, the tray-cradle and the backstrap on both sides, and 0.000 mm³ against the shell proxy
  below z 139. The nub itself is **33.92 mm³** into the collar band on each side.
- **The spring**, per 1 mm slice across the finger: presses **0.80 mm** once seated against the
  band as designed, **0.54–0.73 mm** against the band as printed (its STL). Going in, the finger bends
  at most **1.27 mm** of the 1.60 it has, ~0.58 % strain at the root (1.68 thick, 23.4 mm lever;
  PETG's stiffness is an estimate).
- **Assembly path: passed.** The strap, nub off, moved 1–50 mm out along the tray's back wall:
  0.000 mm³ against every part and 0 points inside the shell wall at every step, both sides.
- **Against the body above the display**, measured point-to-triangle on Pollen's mesh: the run's
  closest approach is **0.81 mm** (0 of 3,616 points inside the shell wall) and the rim hook's is
  **0.64 mm** (0 of 924). The rim hook to anything above z 184 and inboard of X 46 is **7.52 mm**.
  (The run is closer than v2's 1.23 because the strap moved 9 mm outboard; its floor is 0.20.)
- **Mesh check: passed.** All four strap STLs, 0 open edges, 100 % normals.
- **Island scan: clean.** 57 mm² over 45° and 284 mm² on the plate per strap. `islands.py
  --overhangs` lists one 21.7 mm² "bridge" per strap at print z 9.7, and it is the checker's own
  artefact: layer 9.5 lies exactly on a loft station (|Y| 38.0), where the section drops part of
  the gap run (6,011 raster cells there, ~6,585 at 9.49 and 9.51), so the next layer looks unsupported.
  Bambu's slice has no warning.
- **Sections**: `overalls-section.png` (rim hook to finger tip, one closed loop),
  `overalls-section-foot.png` (the finger and its nub in the band), `overalls-section-tongue.png`
  (inboard, the tongue over the band's top edge), and `overalls-cutaway*.png` in 3-D.

**Two check bugs found on the way, worth not repeating.** The right side's cradle clip came back
from OCC *empty* for whole-number bounds (0.0 mm³ against 13,953 on the left), with no error, so the
right strap "passed" against nothing; the clip is off-grid now and the check fails if a clip is
empty. And a nub-removal tool traced along the nub's own ramps left slivers of both ramps behind,
read as 0.72 mm³ of interference; the tool is now a generous block behind the blade.

**Print checks and what they changed (bib straps).** The part prints as a prism extruded along
robot Y, so **robot Y is the print's vertical** — which inverts the intuition about overhangs. v2
cost two rounds, and v3 kept the lesson (strap, tongue and finger are all flush with the OUTBOARD
edge, which goes on the plate, and the part only loses material going up):

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
| `reachy-dungarees-bib-straps.3mf` (v3) | 41 min | 9.1 g | none | none |

**2026-09-20, handover check.** `check_mesh.py` re-run against the exports exactly as they stand:
all six STLs pass, 0 open edges, normals 100 % (backstrap 74.69 cm³, bezel 25.99, tray-cradle
135.34). The printable results are now **committed** - `out/print/*.stl`, `out/bambu/*.3mf` and
`out/render/*.png` - so the repo can be printed from without a 12-minute rebuild; `out/step`,
`out/stl` and the slicer diagnostics stay out of git, as `.gitignore` says. Nothing was reprinted or
re-sliced, and v0.5 still has never been printed.

## Open risks — check on the first print
- **Collar and spring feel.** If the backstrap is too hard to slide on, reduce `PRELOAD`; if the collar is loose, raise it.
- **Side joint (v0.6), not yet printed.** Every sliding face has 0.5 mm of clearance (`FIT_JOINT`) and the pin 0.4 a side, chosen for warp in the tall upright walls, not measured. If the tongues bind on the rails, raise `FIT_JOINT` by 0.1. If the pin holes don't line up when the tongue is at its stop, the stop is `STOP_X`. The pins hold by gravity; if one ever works up, a drop of glue on its head is fine, because the pin is the only part you take out.
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
- **Bib strap retention (v3).** Printed and holding without glue (owner, 2026-09-30). v3 is held by the spring finger's friction, and
  how much it presses is the one number printing can move: 0.80 mm as designed, 0.54–0.73 against
  the tray-cradle's printed mesh, before any print tolerance. If a strap still lifts out,
  raise `FINGER_PRELOAD` by 0.2. The check fails once the bend going in passes 1.4 of the finger's
  1.6 mm of room. If a strap is too hard to push home, lower it by 0.2. If a foot will not
  enter the slot, `FOOT_W` (20.0 in a 20.80 slot) is the number to shave. PETG's stiffness here
  (~2 GPa) is an estimate, not a datasheet figure.
- **The straps assume the shell's real rim matches Pollen's mesh.** The slot is 4.5 mm over a rim
  measured at ~2 mm for exactly that reason, but a much thicker rim would stop the hook seating.
