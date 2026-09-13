#!/usr/bin/env python3
"""Reachy Mini shell proxy: a smooth cadquery solid of the body's outer surface.

    python shell.py            # writes out/cache/shell_proxy.brep and shell_profile.csv

Built from cad/reachy-mini/reachy_mini_body.stl (Pollen's URDF meshes, mm, +X front,
+Y robot left, Z up, 0 = table). The mesh is coarse: slicing it leaves ~3 mm false dips
where a slice falls between vertices, so each ring takes the MAX radius over z +/- 5 mm
(the real surface is the outermost sample), then a closed spline through 72 radii (5 deg)
per ring, lofted ring to ring every 10 mm. Enclosure parts cut this solid (offset by their
clearance) to hug the shell.
"""
import os, struct, math
import numpy as np
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BODY_STL = os.path.join(REPO, "cad", "reachy-mini", "reachy_mini_body.stl")
CACHE = os.path.join(HERE, "out", "cache")

Z_RINGS = list(range(20, 141, 10))      # measured rings; the shell's front top runs higher but nothing reaches it
Z_EXTEND = (10.0, 150.0)                # copies of the end rings so cuts overshoot cleanly
STEP_DEG, WINDOW = 5, 5.0


def load_stl(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    return np.frombuffer(d, np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)["v"].astype(float)


def profile():
    """{z: np.array(72) of outer radius at 0,5,..355 deg (0 = +X)}."""
    tri = load_stl(BODY_STL)
    pts = np.concatenate([tri.reshape(-1, 3), tri.mean(1),
                          (tri[:, 0] + tri[:, 1]) / 2, (tri[:, 1] + tri[:, 2]) / 2, (tri[:, 2] + tri[:, 0]) / 2])
    th = np.degrees(np.arctan2(pts[:, 1], pts[:, 0])) % 360
    r = np.hypot(pts[:, 0], pts[:, 1])
    out = {}
    for z in Z_RINGS:
        m = np.abs(pts[:, 2] - z) <= WINDOW
        row = np.full(360 // STEP_DEG, np.nan)
        for i, a in enumerate(range(0, 360, STEP_DEG)):
            d = np.abs((th[m] - a + 180) % 360 - 180)
            sel = d <= STEP_DEG / 2 + 1.0
            if sel.any():
                row[i] = r[m][sel].max()
        ok = ~np.isnan(row)                                  # fill gaps around the ring
        idx = np.arange(len(row))
        row = np.interp(idx, np.concatenate([idx[ok] - len(row), idx[ok], idx[ok] + len(row)]),
                        np.concatenate([row[ok]] * 3))
        # symmetric shell: average with its mirror about the XZ plane (theta -> -theta)
        row = 0.5 * (row + np.roll(row[::-1], 1))
        out[z] = row
    return out


def ring_wire(z, radii, offset=0.0):
    pts = []
    for i, rr in enumerate(radii):
        a = math.radians(i * STEP_DEG)
        pts.append(cq.Vector((rr + offset) * math.cos(a), (rr + offset) * math.sin(a), z))
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(pts, periodic=True)])


def build_proxy(offset=0.0, prof=None):
    """Solid of the shell grown outward by `offset` mm (radially)."""
    prof = prof or profile()
    zs = sorted(prof)
    rings = [(Z_EXTEND[0], prof[zs[0]])] + [(z, prof[z]) for z in zs] + [(Z_EXTEND[1], prof[zs[-1]])]
    wires = [ring_wire(z, r, offset) for z, r in rings]
    return cq.Solid.makeLoft(wires, False)


def radius_at(prof, z, theta_deg):
    """Interpolated shell radius at height z and angle theta (for placing features)."""
    zs = sorted(prof)
    z = min(max(z, zs[0]), zs[-1])
    t = (theta_deg % 360) / STEP_DEG
    def ring(zz):
        row = prof[zz]; i0 = int(math.floor(t)) % len(row); f = t - math.floor(t)
        return row[i0] * (1 - f) + row[(i0 + 1) % len(row)] * f
    lo = max(zz for zz in zs if zz <= z); hi = min(zz for zz in zs if zz >= z)
    if hi == lo:
        return ring(lo)
    f = (z - lo) / (hi - lo)
    return ring(lo) * (1 - f) + ring(hi) * f


def main():
    os.makedirs(CACHE, exist_ok=True)
    prof = profile()
    with open(os.path.join(CACHE, "shell_profile.csv"), "w") as f:
        f.write("z," + ",".join(str(a) for a in range(0, 360, STEP_DEG)) + "\n")
        for z, row in prof.items():
            f.write(f"{z}," + ",".join(f"{v:.2f}" for v in row) + "\n")
    s = build_proxy(0.0, prof)
    bb = s.BoundingBox()
    print("shell proxy valid=%s vol %.0f cm3 bbox x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f"
          % (s.isValid(), s.Volume() / 1000, bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
    for z in (30, 60, 90, 120, 140):
        print("  z %3d: front %.1f  side %.1f  corner45 %.1f  back %.1f" % (
            z, radius_at(prof, z, 0), radius_at(prof, z, 90), radius_at(prof, z, 45), radius_at(prof, z, 180)))
    cq.exporters.export(cq.Workplane().add(s), os.path.join(CACHE, "shell_proxy.step"))
    print("wrote", CACHE)


if __name__ == "__main__":
    main()
