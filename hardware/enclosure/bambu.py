#!/usr/bin/env python3
"""Bambu Studio projects for the dungarees enclosure: one project per plate, every part set on
the plate the way it prints best, with its own settings.

    python bambu.py            # -> out/bambu/*.3mf (reads out/print/, written by enclosure.py)
    python bambu.py --slice    # + overhang audit, and slice each project with Bambu Studio's CLI:
                               #   time, filament, supports, the slicer's warnings

Printer and process start from bambu/project_settings.json (X1 Carbon, 0.4 mm nozzle, textured
PEI; taken from luna-hardware). bambu3mf.py (also Luna's) swaps in Bambu's own PETG preset from
the installed slicer and writes the per-part settings into the project as object settings.

Two plates, both Bambu PETG Basic at 0.20 mm (every fit in geom.py is sized for that layer), no
supports anywhere:
  reachy-dungarees-tray-cradle      the tray-cradle upright, as it sits on the robot: 5 mm brim
                                    (95 mm tall collar and ribs on a band-thin footprint)
  reachy-dungarees-bezel-backstrap  the bezel face down (textured PEI gives the bib a fabric-like
                                    finish; no brim, the engraving is at the plate), the backstrap
                                    upright, turned 90 deg to fit beside it, with a 5 mm brim
"""
import json, os, struct, subprocess, sys, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bambu3mf as B

PRINT = os.path.join(HERE, "out", "print")
OUTB = os.path.join(HERE, "out", "bambu")
CLI = r"C:\Program Files\Bambu Studio\bambu-studio.exe"
PRE = "reachy-crowpanel"

DENIM = "#3D6497"
# elefant_foot_compensation: the bezel's stitching is engraved into its first layers and the backstrap's
# tongue slides over the strip at the plate - neither may grow a foot
COMMON = dict(layer_height="0.2", wall_loops="3", top_shell_layers="5", bottom_shell_layers="4",
              sparse_infill_density="20%", sparse_infill_pattern="gyroid", seam_position="aligned",
              ironing_type="no ironing", elefant_foot_compensation="0.15", enable_support="0")
BRIM = {"brim_type": "outer_only", "brim_width": "5"}
PROJECTS = [
    dict(name="reachy-dungarees-tray-cradle", preset="Bambu PETG Basic @BBL X1C", colours=[DENIM],
         process=dict(COMMON, brim_type="no_brim"),
         rows=[[("tray-cradle", 0.0, dict(BRIM))]]),
    dict(name="reachy-dungarees-bezel-backstrap", preset="Bambu PETG Basic @BBL X1C", colours=[DENIM],
         process=dict(COMMON, brim_type="no_brim"),
         rows=[[("bezel", 0.0, {})], [("backstrap", 90.0, dict(BRIM))]]),
]


def load_stl(name, rot_deg=0.0):
    """A print STL as (vertices, triangles), welded, turned rot_deg about z."""
    path = os.path.join(PRINT, "%s-%s-print.stl" % (PRE, name))
    with open(path, "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        v = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))["v"].reshape(-1, 3).astype(float)
    if rot_deg:
        c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
        v = np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], axis=1)
    q = np.round(v * 1e4).astype(np.int64)
    U, inv = np.unique(q, axis=0, return_inverse=True)
    return U.astype(float) / 1e4, inv.reshape(-1, 3)


def audit(name):
    """Overhang audit of a print STL (Luna v2's rule): area facing down more than 45 deg past
    vertical and more than 0.3 mm above the plate, grouped into height bands, plus the area on the
    plate. Short bridges (window tops, slit tops) and sub-mm ledges show up here and are fine."""
    V, T = load_stl(name)
    V = V - np.array([0.0, 0.0, V[:, 2].min()])          # measured from the mesh's real lowest point
    P = V[T]
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    a = np.linalg.norm(n, axis=1) / 2
    nz = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
    zmin = P[:, :, 2].min(axis=1)
    over = (nz < -math.cos(math.radians(45))) & (zmin > 0.3)
    bed = (nz < -0.99) & (P[:, :, 2].max(axis=1) < 0.01)
    bands = {}
    for z, ar in zip(zmin[over], a[over]):
        k = int(z // 10) * 10
        bands[k] = bands.get(k, 0.0) + ar
    worst = sorted(bands.items(), key=lambda kv: -kv[1])[:4]
    print("  %-12s on plate %6.0f mm2   overhang >45 deg %5.0f mm2   largest bands: %s" % (
        name, a[bed].sum(), a[over].sum(), ", ".join("z%d-%d %.0f" % (k, k + 10, v) for k, v in worst) or "none"))


def build(p):
    ps = B.load_reference()
    ps = B.with_filament(ps, p["preset"], p["colours"][0])
    ps = B.process(ps, p["name"], **p["process"])
    rows = [[dict(name="%s-%s" % (PRE, n), parts=[dict(name="%s-%s" % (PRE, n), mesh=load_stl(n, rot), extruder=1)], settings=s)
             for n, rot, s in row] for row in p["rows"]]
    objs = B.layout(rows, ps)
    path = os.path.join(OUTB, p["name"] + ".3mf")
    B.write_project(path, objs, ps, p["name"])
    feet = []
    for ob in objs:
        V = np.concatenate([q["mesh"][0] for q in ob["parts"]])
        (x, y), half = ob["at"][0], (V[:, :2].max(0) - V[:, :2].min(0)) / 2
        feet.append((ob["name"].replace(PRE + "-", ""), x - half[0] - 1, x + half[0] + 1, y - half[1] - 1, y + half[1] + 1))
    return path, feet


def slice_one(path, feet):
    """Slice with Bambu Studio's own CLI: minutes, grams, the slicer's warning, and per part the
    support moves it was given (there should be none)."""
    import re
    d = os.path.join(OUTB, "sliced", os.path.splitext(os.path.basename(path))[0])
    os.makedirs(d, exist_ok=True)
    r = subprocess.run([CLI, "--slice", "0", "--outputdir", d, path], capture_output=True, text=True, timeout=3600)
    res = os.path.join(d, "result.json")
    if not os.path.exists(res):
        return dict(error="no result.json (exit %s): %s" % (r.returncode, (r.stdout + r.stderr)[-400:]))
    j = json.load(open(res))
    if j.get("return_code") != 0:
        return dict(error=j.get("error_string"))
    pl = j["sliced_plates"][0]
    g = open(os.path.join(d, "plate_1.gcode"), encoding="utf-8", errors="ignore").read()
    support = {n: [0, 0.0] for n, *_ in feet}
    z, feature = 0.0, ""
    for line in g.split("\n"):
        if line.startswith("; Z_HEIGHT:"):
            z = float(line.split(":")[1])
        elif line.startswith("; FEATURE:"):
            feature = line[10:].strip()
        elif feature.startswith("Support") and line.startswith("G1") and " E" in line:
            m = re.search(r"X([\d.]+) Y([\d.]+)", line)
            if m:
                x, y = float(m.group(1)), float(m.group(2))
                for n, x0, x1, y0, y1 in feet:
                    if x0 <= x <= x1 and y0 <= y <= y1:
                        support[n][0] += 1; support[n][1] = max(support[n][1], z)
    return dict(minutes=pl["total_predication"] / 60, grams=[round(f["total_used_g"], 1) for f in pl["filaments"]],
                per_part=support, warning=pl.get("warning_message", ""), layers=g.count("; CHANGE_LAYER"))


def main():
    os.makedirs(OUTB, exist_ok=True)
    built = [build(p) for p in PROJECTS]
    if "--slice" not in sys.argv:
        return
    print("overhang audit (print orientation):")
    for n in ("tray-cradle", "bezel", "backstrap"):
        audit(n)
    if not os.path.exists(CLI):
        print("no Bambu Studio at %s: projects written, not sliced" % CLI); return
    print("Bambu Studio slicer pass:")
    for path, feet in built:
        r = slice_one(path, feet)
        name = os.path.basename(path)
        if r is None or "error" in r:
            print("  %-36s SLICE FAILED %s" % (name, (r or {}).get("error", "")))
            continue
        print("  %-36s %4.0f min  %-8s %s" % (name, r["minutes"], "+".join("%sg" % g for g in r["grams"]), r["warning"] or "no warnings"))
        for part, (moves, top) in r["per_part"].items():
            print("      %-12s %s" % (part, "no support" if not moves else "SUPPORT: %d moves, up to %.1f mm" % (moves, top)))


if __name__ == "__main__":
    main()
