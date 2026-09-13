#!/usr/bin/env python3
"""Find which feature group of the backstrap triggers Bambu Studio's "floating cantilever" warning:
build the backstrap with one group switched off, write it alone as a Bambu project with the real
process settings, slice it with the CLI and print the warning. Run the variants side by side.

    python bisect_backstrap.py <variant>
    variants: full, no-outfit, no-springs, no-tabs, no-buttons, no-gutter
"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cadquery as cq
import collar as C
import bambu3mf as B
import bambu as P

VARIANTS = {
    "full": {},
    "no-outfit": dict(dressed=False),
    "no-springs": dict(springs=False),
    "no-tabs": dict(tabs=False),
    "no-buttons": dict(buttons=False),
    "no-gutter": dict(gutter=False),
    # second round (springs were the culprit): which part of the spring tab?
    "flat-springs-no-nubs": dict(gable=False, nubs=False),
    "gable-springs": dict(gable=True),
}


def main():
    v = sys.argv[1]
    out = os.path.join(HERE, "out", "bisect", v)
    os.makedirs(out, exist_ok=True)
    part = C.to_bed(C.build_backstrap(**VARIANTS[v]))
    stl = os.path.join(out, "backstrap.stl")
    cq.exporters.export(part, stl, tolerance=0.02, angularTolerance=0.1)
    import numpy as np, struct
    with open(stl, "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        tri = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))["v"].reshape(-1, 3).astype(float)
    q = np.round(tri * 1e4).astype(np.int64)
    U, inv = np.unique(q, axis=0, return_inverse=True)
    mesh = (U.astype(float) / 1e4, inv.reshape(-1, 3))
    proj = next(p for p in P.PROJECTS if "backstrap" in p["name"])
    ps = B.with_filament(B.load_reference(), proj["preset"], proj["colours"][0])
    ps = B.process(ps, "bisect-" + v, **proj["process"])
    objs = B.layout([[dict(name="backstrap-" + v, parts=[dict(name="backstrap-" + v, mesh=mesh, extruder=1)], settings=dict(P.BRIM))]], ps)
    path = os.path.join(out, "backstrap-%s.3mf" % v)
    B.write_project(path, objs, ps, "bisect-" + v)
    d = os.path.join(out, "sliced")
    os.makedirs(d, exist_ok=True)
    subprocess.run([P.CLI, "--slice", "0", "--outputdir", d, path], capture_output=True, text=True, timeout=1800)
    res = os.path.join(d, "result.json")
    if not os.path.exists(res):
        print("RESULT %-11s slice failed" % v); return
    j = json.load(open(res))
    pl = j["sliced_plates"][0]
    print("RESULT %-11s %s" % (v, pl.get("warning_message") or "no warning"))


if __name__ == "__main__":
    main()
