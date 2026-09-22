# CLAUDE.md: working conventions for smarthome-reachy-mini

**This repo is hardware.** The dungarees enclosure that carries an **Elecrow CrowPanel Advanced 7"
ESP32-P4** on the front belly of a **Reachy Mini**, plus the reference CAD it is fitted against.
Written 2026-09-20 as a handover: everything an agent needs to change the geometry safely and know
whether the change is good.

**The software is not here.** Firmware, the robot's voice loop, Home Assistant and every operational
runbook live in the sibling repo `../smarthome-reachy-mini-display`, which has its own CLAUDE.md.
Read that one for the system, the robot and the panel; read this one for the plastic.

## 0. Hard rules

1. **`python` is the CAD interpreter, and it is Python 3.11.** The scripts here need
   `cadquery 2.8` + `numpy` + `scipy`, which are installed in the ESP-IDF 3.11 interpreter that
   `python` resolves to on this machine (checked 2026-09-20: cadquery 2.8.0, Python 3.11.2). Do
   **not** run them with `py -3.12` - that interpreter is for the sibling repo's stdlib-only scripts
   and has no cadquery.
2. **No installs without the owner's explicit OK in chat.** That includes pip installs into the CAD
   interpreter, Bambu Studio versions, and anything that downloads a toolchain.
3. **Never hand-edit anything under `hardware/enclosure/out/`.** It is all generated. The scripts own
   it, `.gitignore` keeps the heavy parts out of git, and a hand-edited export makes every check a
   lie.
4. **Third-party files have licences, and they are not all the same.** `cad/reachy-mini/` meshes are
   Pollen Robotics, **CC BY-NC-SA 4.0** (non-commercial, share-alike). The CrowPanel STEP is
   Elecrow's, from a repo with **no licence file** - treat it exactly as the sibling repo's rule 3
   says: use it as a reference, never paste its content into source or docs. The ACOS community case
   is **CC BY-SA 4.0** and needs attribution. Keep the licence table in `README.md` true.
5. **Every fit number belongs to a class in `geom.py`**, not to the part that uses it. If a gap needs
   a number that is not one of those classes, add the class with the reason, and say what it was
   measured or reasoned from.
6. **Walls are whole line widths and heights are whole layers**, in the part's own print
   orientation - `lines(n)` (n x 0.42 mm) and `layers()`. A 2.0 mm wall on a 0.42 mm line is three
   passes and a gap.
7. **Every underside is 45 degrees or steeper, and no bridged roof sits over a flexure.** Both rules
   came from real slicer warnings (see the README's "Print checks and what they changed"), and both
   are cheaper to keep than to rediscover.
8. **A geometry change is not done until the checks pass and the README's Status section says so**,
   with the numbers that run produced. See section 3.
9. **Never claim a fit, a print time or a mass that was not measured by a check or a slice.** The
   README is a record, not a hope.
10. **Git.** Commit and push are fine here (the owner asked for it; do not add `Co-Authored-By`
    trailers). Do not commit `out/step`, `out/stl`, `out/bambu/probe`, `out/bambu/sliced` or the
    build logs - they are hundreds of megabytes and regenerate. The printable results (`out/print`,
    `out/render`, `out/bambu/*.3mf`) **are** in git, because the README promises them.

## 1. The pipeline, and what each step proves

```
python shell.py                  # once: a smooth cadquery proxy of Reachy's body -> out/cache/
python enclosure.py              # build + export all three parts (~12 min)   [--plain: no detail]
python enclosure.py --check      # the same, with the fit checks in one go (slower)
python collar.py --check-only    # fit checks against the exported STEPs; exit 1 on failure
python check_mesh.py             # every exported STL watertight (0 open edges, normals 100%)
python islands.py                # layer scan: floating islands, with locations
python islands.py --overhangs    # layer scan: cantilever and bridge regions, with locations
python bambu.py                  # out/bambu/*.3mf, one project per plate
python bambu.py --slice          # + overhang audit + Bambu Studio CLI slice: time, grams, warnings
python bambu.py --only <name>    # ...just the matching projects, so the others are not re-timed
python overalls.py [--check]     # the two optional bib straps (~1 min); --check-only for the fits
python render_overalls.py        # out/render/overalls-*.png
python probe.py                  # diagnostic: where the slicer would put support, clustered
python render.py                 # out/render/*.png (matplotlib, no GPU)
python bisect_backstrap.py <v>   # diagnostic: which feature group causes a slicer warning
python step_names.py             # the CrowPanel STEP's named components and bounding boxes
```

Two things about running them:

- **Everything below `enclosure.py` reads only its exports**, so the checks can run side by side.
- **Run `bambu.py --slice` on its own.** With the other checks competing for the CPU, a tray-cradle
  slice ran past 25 minutes.

What each one is for, in one line each: `collar.py --check-only` is interference and *assembly
paths* (the board lifting out, the tray backing off the belly, the backstrap pulling off);
`check_mesh.py` catches the non-manifold edges that touching faces leave behind; `islands.py` is the
only thing that says *where* a slicer warning is, because the Bambu CLI says neither where nor what;
`probe.py` answers the same question from the slicer's side by turning support on for one region.

## 2. Where the numbers live

| Thing | Where |
|---|---|
| Frames B (board) and R (robot), the transform, `placement()` | `geom.py` docstring, and README "Frames" |
| Tolerance classes (`FIT_SNAP`, `FIT_SLIDE`, `FIT_Z`, `FIT_CATCH`, `HOLE_H_EXTRA`) | `geom.py`, tabulated in README "Tolerances" |
| Board facts (openings, hole pitch, connector stand-off) | read from Elecrow's STEP by name - `board_components.txt`, `step_names.py` |
| The robot's body profile | `shell.py` -> `out/cache/shell_profile.csv`, from Pollen's mesh. **A proxy, not a measurement of the robot**: the collar carries 1.5 mm clearance because of it |
| Cosmetic detail rules (upright proud vs face-down engraved) | `outfit.py` docstring |
| Print profile (X1C, PETG, 0.20 mm, no supports, brims, 0.15 elephant foot) | `bambu/project_settings.json` + README "Printing" |
| Load and retention reasoning | README "Load: why it stays put" |

## 3. Finishing a geometry change

1. `python enclosure.py` (or `--check`).
2. `python collar.py --check-only`, `python check_mesh.py`, `python islands.py`,
   `python islands.py --overhangs` - all four, every time.
3. `python bambu.py --slice`, alone. Record time, grams, supports and **any slicer warning**.
4. If a warning appears and it is not obvious, `python islands.py --overhangs` for the location and
   `python probe.py` for where support would land; `bisect_backstrap.py` if it is still unclear which
   feature group causes it.
5. `python render.py`, and look at the renders.
6. Update the README: the **Status** section (date, version, what ran, the table of volumes and
   extents), the tolerance table if a class changed, and "Print checks and what they changed" with
   what the change fixed and how it was found.

## 4. State at handover (2026-09-20)

- **v0.5 is print-ready and has never been printed.** The geometry, the README's v0.5 sections and
  the exports in `out/` are the independent fit review's result: everything passes, both plates slice
  with no warnings and no supports (tray-cradle 4 h 52 / 152 g, bezel+backstrap 3 h 42 / 114 g).
- **Re-checked 2026-09-20** on the exports as they stand: `check_mesh.py` passes all six STLs
  (backstrap 74.69 cm3, bezel 25.99, tray-cradle 135.34; 0 open edges each).
- **The first print is the next real step**, and it is the owner's to run. Until then every fit is
  reasoned or checked in CAD, never confirmed in plastic - say so in that order.
- The printable outputs are now committed (`out/print/*.stl`, `out/bambu/*.3mf`, `out/render/*.png`);
  `out/step`, `out/stl` and the slicer diagnostics stay out of git.

**2026-09-21: the bib straps (`overalls.py`), an optional fourth and fifth print.** Two clip-on
shoulder straps that hang over the robot's own front rim and hook behind the panel. They change
**nothing** about the three parts above - that was the owner's condition - so `enclosure.py` was
never re-run for them. Checked the same way and all passing: 0.000 mm3 against each existing part,
1.06 mm to the shell on the run, 0.57 mm at the rim hook, watertight, islands clean, and 28 min /
5.5 g with no slicer warning and no support. Three things this cost, worth not rediscovering:

- **Do not sample the body mesh in a window up here.** `shell.py`'s "max radius in a +-5 mm ring"
  is right for its 10 mm rings and wrong above z 150, where a +-2.5 mm band at Y 30 can contain no
  vertex at all between z 167 and 173: it interpolated across the gap and read the surface 1.4 mm
  too far in, putting 8 strap points inside the shell wall. `overalls._front()` cuts the TRIANGLES
  with the plane instead. The error was invisible to a vertex-window check and obvious to a
  point-to-triangle one, which is why `overalls.check()` uses the latter.
- **`makeLoft(..., ruled=False)` builds a valid solid that every boolean then refuses.**
  `run.union(rim)` came back with 0 solids and 0 mm3. Always ruled; answer the faceting with more
  slices.
- **Two lofted pieces must overlap, never meet tangentially.** Where the hook's taper met the run's
  face exactly, the union left sliver faces - 6 degenerate triangles and 6 non-manifold edges that
  `check_mesh.py` caught and OCC's `isValid()` did not. `SEAM = 0.10` sets one piece inside the next.

## 5. Style

- Python: 4-space indent, 110 columns, module docstring first and it explains *why*, not just what.
- Comments carry the measurement or the source that justifies a number. "0.40 / side (reMixTape
  printed 0.2 on this printer; +0.2 wiggle room)" is the house style; a bare `0.40` is not.
- Docs: facts with sources; when two sources disagree, record both and say which one is used and why.
- Never delete a "why it is like this" note to tidy up. They are the reason the second print is not
  needed.
