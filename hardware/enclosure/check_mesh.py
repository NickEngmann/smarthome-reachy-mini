#!/usr/bin/env python3
"""Watertightness check for every exported STL - run before anything is printed
or committed.

    python check_mesh.py [dir ...]      # default: enclosure/out and mold/out

For each binary STL: the signed mesh volume (a solid with outward normals is
positive), agreement between stored and geometric normals, and the number of
edges used by other than exactly two triangles (must be 0: a slicer treats an
open shell as hollow and fills nothing - which is how a 110-crack tray STL was
caught on 2026-09-08). Exit 1 on any failure.

Edges are keyed on their two endpoints quantised to 0.1 um and ordered
lexicographically, so two different edges never share a key (an earlier
version took the per-axis min/max of the endpoints, which maps the diagonals
of a square to the same key and could hide a crack behind a healthy edge).
"""
import os, struct, sys
import numpy as np

def load(path):
    with open(path, "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        data = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    if len(data) != n:
        raise ValueError("%s: header promises %d triangles, file holds %d" % (path, n, len(data)))
    return data["n"].astype(float), data["v"].reshape(-1, 3, 3).astype(float)

def edge_counts(T):
    """Counts of the distinct undirected edges, plus the number of zero-length edges."""
    q = np.round(T * 1e4).astype(np.int64)                        # 0.1 um grid: exact for STL floats
    e = np.concatenate([q[:, [0, 1]], q[:, [1, 2]], q[:, [2, 0]]])   # (3N, 2, 3)
    p, r = e[:, 0], e[:, 1]
    lt = (p[:, 0] < r[:, 0]) | ((p[:, 0] == r[:, 0]) & ((p[:, 1] < r[:, 1]) | ((p[:, 1] == r[:, 1]) & (p[:, 2] < r[:, 2]))))
    a = np.where(lt[:, None], p, r); b = np.where(lt[:, None], r, p)
    degenerate = int((p == r).all(axis=1).sum())
    _, counts = np.unique(np.concatenate([a, b], axis=1), axis=0, return_counts=True)
    return counts, degenerate

def check(path):
    N, T = load(path)
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6.0
    fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    agree = (np.einsum("ij,ij->i", fn, N) > 0).mean() if len(T) else 0.0
    counts, degenerate = edge_counts(T)
    bad = int((counts != 2).sum())
    ok = len(T) > 0 and vol > 0 and agree > 0.99 and bad == 0 and degenerate == 0
    print("%-4s %-40s %7d tris  %9.2f cm3  normals %3.0f%%  open edges %d%s" %
          ("ok" if ok else "FAIL", os.path.basename(path), len(T), vol / 1000, agree * 100, bad,
           "  degenerate %d" % degenerate if degenerate else ""))
    return ok

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    dirs = sys.argv[1:] or [os.path.join(here, "out", "stl"), os.path.join(here, "out", "print")]
    allok, seen = True, 0
    for d in dirs:
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(".stl"):
                allok &= check(os.path.join(d, f)); seen += 1
    if not seen:
        print("no STL files found in", ", ".join(dirs)); sys.exit(1)
    print("MESH CHECK " + ("PASSED" if allok else "FAILED"))
    sys.exit(0 if allok else 1)

if __name__ == "__main__":
    main()
