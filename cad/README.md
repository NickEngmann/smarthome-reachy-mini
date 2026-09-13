# CAD reference models

Reference geometry for the smarthome Reachy Mini display enclosure. All units are mm unless noted.

## `reachy-mini/` — Pollen Robotics Reachy Mini
Assembled from the per-part STLs and URDF in https://github.com/pollen-robotics/reachy_mini (`src/reachy_mini/descriptions/reachy_mini/urdf/`), at the URDF zero pose. Hardware licence CC BY-NC-SA. No official STEP has been released yet.

- `reachy_mini_body.stl` — body only: foot, turning ring, lower and upper shell
- `reachy_mini_full.stl` — whole robot
- `dimensions.txt` — per-part bounding boxes, plus body radius per 5 mm of height
- `reachy_mini_dimensions.png`, `back_interface.png` — Pollen's official drawings
- `preview.png` — render of the assembly

Frame: +X = front (camera side), +Y = robot's left, Z up, Z = 0 at the table.
Body envelope: 155 × 155 × 185. The shell is a rounded square in section: 155 across the flats, ~164 across the diagonals at z 50–100. The top edge is scalloped and highest at the front (z 184.8). The shell yaws ±180° on the foot (z 0–22, ~114 × 126).
The assembly script lives outside this repo, in `Projects/reachy-mini-cad/assemble.py`.

## `crowpanel-advanced-7in-esp32-p4/` — Elecrow CrowPanel Advanced 7" ESP32-P4 (Amazon B0H5K6W1C3)
- `ESP32-P4-7_0-inch-20251229.stp` — official Elecrow STEP, from https://github.com/Elecrow-RD/CrowPanel-Advanced-7inch-ESP32-P4-HMI-AI-Display-1024x600-IPS-Touch-Screen (`3D file/`)
- `CrowPanel-Advanced-7in-ESP32-P4.stl` — STL conversion (0.05 mm tolerance)
- `CrowPanel-Advanced-7in-ESP32-P4_no-flex-tails.stl` — same, with the flat-drawn LCD/touch flex tails clipped off above z = 53
- `dimensions.txt`, `preview.png`

Frame: X = long axis, Z = short axis, +Y = glass/viewing side, origin at board centre.
- PCB: 176.9 × 104.0 × 1.7
- LCD and touch glass: 164.9 × 100
- Active area: ~154 × 86
- Overall thickness: 17.5 (y −13.8 → +3.7)
- Mounting holes: 4 × Ø3.2 (M3) at x ±85.45, z ±49.0, i.e. **170.9 × 98.0** spacing
- Elecrow's spec lists the outline as 180 × 105, 450 g

## `community-cases/`
- `acos-crowpanel-advance-7-enclosure-s3/` — **Alley Cat "ACOS" enclosure** (Printables 1476807), CC BY-SA 4.0. It was designed for the **ESP32-S3** CrowPanel Advance 7", not the P4. Its board screw pattern (171 × 98) matches the P4's, but the port cutouts may not. Parts: front/center/rear in SMA, USB and insert variants, plus buttons and a `complete.step`; overall 197 × 111 × 25. `printables-1476807-description.pdf` has print settings and the BOM (4× M3×8, 4× M3×12, 8000 mAh LiPo).
- `crowpanel-p4-7in-case-3mf/elecrow-panel.3mf` — user-downloaded two-body case, probably Printables 1689586 ("Elecrow CrowPanel ESP32-P4 7" Case" by BIG_SUNDAR); unverified. Tray 182 × 124.5 × 20 plus a 7 mm lid.
