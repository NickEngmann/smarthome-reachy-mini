#!/usr/bin/env python3
"""Ask Bambu Studio WHERE its "floating cantilever" is: re-write each project with tree supports on
critical regions only (the regions behind that warning), slice it with the CLI, and cluster the
support extrusions. Each cluster is reported in the part's own print coordinates (the plate
position minus where layout() put the part), so it can be matched to a feature.

    python probe.py            # -> out/bambu/probe/*.3mf, sliced; prints the clusters

The real projects (bambu.py) keep supports off; this is a diagnostic only.
"""
import os, re, sys, json, math, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bambu3mf as B
import bambu as P

OUT = os.path.join(HERE, "out", "bambu", "probe")


def main():
    os.makedirs(OUT, exist_ok=True)
    for p in P.PROJECTS:
        ps = B.load_reference()
        ps = B.with_filament(ps, p["preset"], p["colours"][0])
        # NORMAL supports stand straight under what they hold (tree trunks wander, even into the gaps
        # between parts, so their xy says little); only the "Support interface" moves that touch the
        # part are reported
        proc = dict(p["process"], enable_support="1", support_type="normal(auto)", support_critical_regions_only="1")
        ps = B.process(ps, p["name"] + "-probe", **proc)
        rows = [[dict(name="%s-%s" % (P.PRE, n), parts=[dict(name="%s-%s" % (P.PRE, n), mesh=P.load_stl(n, rot), extruder=1)], settings=s)
                 for n, rot, s in row] for row in p["rows"]]
        objs = B.layout(rows, ps)
        path = os.path.join(OUT, p["name"] + "-probe.3mf")
        B.write_project(path, objs, ps, p["name"] + "-probe")
        feet = []
        for ob in objs:
            V = np.concatenate([q["mesh"][0] for q in ob["parts"]])
            (x, y) = ob["at"][0]
            c = (V.min(0) + V.max(0)) / 2                       # write_project centres the mesh on its bbox
            half = (V[:, :2].max(0) - V[:, :2].min(0)) / 2
            rot = next(r for row in p["rows"] for n, r, s in row if "%s-%s" % (P.PRE, n) == ob["name"])
            feet.append((ob["name"].replace(P.PRE + "-", ""), x, y, c, half, rot))
        d = os.path.join(OUT, "sliced", p["name"])
        os.makedirs(d, exist_ok=True)
        subprocess.run([P.CLI, "--slice", "0", "--outputdir", d, path], capture_output=True, text=True, timeout=1800)
        res = os.path.join(d, "result.json")
        if not os.path.exists(res):
            print(p["name"], "probe slice failed"); continue
        j = json.load(open(res))
        print("%s: %s" % (p["name"], j["sliced_plates"][0].get("warning_message") or "no warning"))
        g = open(os.path.join(d, "plate_1.gcode"), encoding="utf-8", errors="ignore").read()
        pts = []
        z, feature = 0.0, ""
        for line in g.split("\n"):
            if line.startswith("; Z_HEIGHT:"):
                z = float(line.split(":")[1])
            elif line.startswith("; FEATURE:"):
                feature = line[10:].strip()
            elif feature == "Support interface" and line.startswith("G1") and " E" in line:
                m = re.search(r"X([\d.]+) Y([\d.]+)", line)
                if m:
                    pts.append((float(m.group(1)), float(m.group(2)), z))
        if not pts:
            print("  no support interface at all"); continue
        A = np.array(pts)
        for name, ax, ay, c, half, rot in feet:
            inside = (np.abs(A[:, 0] - ax) <= half[0] + 1) & (np.abs(A[:, 1] - ay) <= half[1] + 1)
            S = A[inside]
            if not len(S):
                print("  %-12s no support" % name); continue
            # part print coordinates: plate xy - placement + bbox centre offset, then undo the plate rotation
            S = S.copy(); S[:, 0] += c[0] - ax; S[:, 1] += c[1] - ay
            if rot:
                t = -math.radians(rot)
                x, y = S[:, 0].copy(), S[:, 1].copy()
                S[:, 0], S[:, 1] = x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)
            cells = {}
            for x, y, zz in S:
                k = (int(x // 6), int(y // 6))
                e = cells.setdefault(k, [x, x, y, y, zz, zz, 0])
                e[0] = min(e[0], x); e[1] = max(e[1], x); e[2] = min(e[2], y); e[3] = max(e[3], y)
                e[4] = min(e[4], zz); e[5] = max(e[5], zz); e[6] += 1
            print("  %-12s %d support moves in %d cells (part print coords):" % (name, len(S), len(cells)))
            for k, e in sorted(cells.items(), key=lambda kv: -kv[1][6])[:25]:
                print("      x %6.1f..%6.1f  y %6.1f..%6.1f  z %6.1f..%6.1f  (%d moves)" % tuple(e))


if __name__ == "__main__":
    main()
