# smarthome-reachy-mini

Hardware for putting a smart-home display on a **Pollen Robotics / Hugging Face Reachy Mini**. The display is an **Elecrow CrowPanel Advanced 7" ESP32-P4** (1024×600 IPS touch, ESP32-C6 Wi-Fi 6). It rides on the robot's front belly in a 3D-printed enclosure dressed as denim dungarees.

The display's firmware and software live in the sibling repo **`../smarthome-reachy-mini-display`**.

## System architecture
The display is one part of a local, private assistant that replaces an Echo Show:
- **Reachy Mini** handles listening, speaking, reflexes and gestures.
- A **Jetson AGX Thor** runs speech recognition, a local LLM and speech synthesis.
- **Home Assistant** on a Raspberry Pi 5 keeps timers, weather, music and alerts.
- The **CrowPanel** is an Echo-Show-style dashboard that reads only Home Assistant.

This is the current direction, not final software decisions. It is written up in [`../smarthome-reachy-mini-display/docs/system-architecture.md`](../smarthome-reachy-mini-display/docs/system-architecture.md); the latency design is in [`docs/latency.md`](../smarthome-reachy-mini-display/docs/latency.md) in the same repo.

## Repo map

| Path | What |
|---|---|
| [`hardware/enclosure/`](hardware/enclosure/README.md) | The dungarees enclosure: cadquery source, fit, mesh and printability checks, renders, and **Bambu Studio projects ready to print** (`out/bambu/*.3mf`) |
| [`cad/`](cad/README.md) | Reference models: Reachy Mini body and robot (assembled from Pollen's URDF), Elecrow's official CrowPanel P4 STEP and STL conversions, and two community cases (the ACOS enclosure for the S3 Advance 7", and a two-part case 3MF) |
| `elecrow-crowpanel-advance-7-enclosure-model_files.zip`, `elecrow-panel.3mf` | The original community-case downloads, also unpacked under `cad/community-cases/` |
| [`docs/TODO.md`](docs/TODO.md) | Hardware ideas not built yet, with whatever has already been measured for them. First up: **a hat**, and what the antennas and the head's microphones will and will not allow |

## Print the enclosure
1. Open `hardware/enclosure/out/bambu/reachy-dungarees-tray-cradle.3mf` and `reachy-dungarees-bezel-backstrap.3mf` in Bambu Studio.
2. Load PETG and print. Both projects are set for an X1C with a textured PEI plate, 0.20 mm layers, and no supports.
3. Assemble: board into the tray, bezel snapped on, tray-cradle against the belly, backstrap slid on from behind until the four tabs click.
4. Optional: `reachy-dungarees-bib-straps.3mf` (39 min, 6.0 g) adds the two shoulder straps. They hang over the robot's own front rim and drop into the pocket the cradle already has behind the panel, and they change nothing about the three parts above — see the enclosure README's "Bib straps".

Check the enclosure README's Status section before printing: it records the last verified build. It also lists the tolerances, load reasoning and open risks.

## Rebuild from source
The enclosure scripts use cadquery on the ESP-IDF 3.11 interpreter (`python`), with numpy and scipy. Bambu Studio's CLI is used for slicing. See [`hardware/enclosure/README.md`](hardware/enclosure/README.md) for the full command list.

## Licences of included third-party files
- **Reachy Mini meshes:** Pollen Robotics, CC BY-NC-SA 4.0.
- **CrowPanel STEP:** Elecrow, from their GitHub repo, which has no licence file.
- **ACOS enclosure:** Alley Cat / Majestic AV, CC BY-SA 4.0 (attribution required).
