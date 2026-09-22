#!/usr/bin/env python3
"""Layer-by-layer printability check of the print STLs - what the slicer's "floating regions" and
"floating cantilever" warnings mean, with a location attached (Bambu Studio's CLI says neither
where nor what).

    python islands.py [layer_mm] [grid_mm]      # defaults 0.2 mm layers, 0.2 mm grid

Each layer's cross-section (at mid-layer) is rasterised onto a grid (even-odd scanline fill of the
triangle/plane segments) and split into islands (8-connected). Every island is compared with the
layer below, grown by one grid cell:
  FLOATING   no cell of the island rests on the layer below - it starts in mid-air
  WEAK       under 20 % rests on the layer below and the unsupported part reaches over 2 mm
             from the supported part - a cantilever printed into air
Islands under 0.5 mm2 are ignored. Reports are merged over consecutive layers; coordinates are
print (plate) coordinates, mm. numpy + scipy.ndimage only.
"""
import os, sys, struct
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PRINT = os.path.join(HERE, "out", "print")
PRE = "reachy-crowpanel"
EIGHT = np.ones((3, 3), dtype=bool)


def load(path):
    with open(path, "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        T = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))["v"].reshape(-1, 3, 3).astype(float)
    T[:, :, 2] -= T[:, :, 2].min()
    return T


def section_segments(T, z):
    """(M, 2, 2) xy segments where the plane z cuts the triangles."""
    d = T[:, :, 2] - z
    s = np.sign(d)
    s[s == 0] = 1e-9
    cut = ~((s > 0).all(axis=1) | (s < 0).all(axis=1))
    A = T[cut]; D = d[cut]
    segs = []
    for (i, j) in ((0, 1), (1, 2), (2, 0)):
        di, dj = D[:, i], D[:, j]
        m = (di * dj) < 0
        t = np.where(m, di / np.where(m, di - dj, 1.0), 0.0)
        p = A[:, i, :2] + (A[:, j, :2] - A[:, i, :2]) * t[:, None]
        segs.append((m, p))
    # each cut triangle crosses exactly two of its edges
    (m0, p0), (m1, p1), (m2, p2) = segs
    a = np.where(m0[:, None], p0, p1)
    b = np.where(m2[:, None], p2, np.where(m0[:, None] & m1[:, None], p1, p1))
    two = (m0.astype(int) + m1.astype(int) + m2.astype(int)) == 2
    return np.stack([a[two], b[two]], axis=1)


def rasterise(segs, x0, y0, nx, ny, g):
    """Even-odd fill of the closed section outlines onto an ny x nx grid (cell centres)."""
    img = np.zeros((ny, nx), dtype=bool)
    if not len(segs):
        return img
    ya, yb = segs[:, 0, 1], segs[:, 1, 1]
    lo, hi = np.minimum(ya, yb), np.maximum(ya, yb)
    rows_lo = np.clip(np.ceil((lo - y0) / g - 0.5).astype(int), 0, ny)
    rows_hi = np.clip(np.ceil((hi - y0) / g - 0.5).astype(int), 0, ny)          # rows with centre in [lo, hi)
    cnt = rows_hi - rows_lo
    keep = cnt > 0
    if not keep.any():
        return img
    S, rl, c = segs[keep], rows_lo[keep], cnt[keep]
    idx = np.repeat(np.arange(len(S)), c)
    rows = np.concatenate([np.arange(a, a + k) for a, k in zip(rl, c)])
    yc = y0 + (rows + 0.5) * g
    P, Q = S[idx, 0], S[idx, 1]
    xc = P[:, 0] + (Q[:, 0] - P[:, 0]) * (yc - P[:, 1]) / np.where(Q[:, 1] - P[:, 1] == 0, 1e-12, Q[:, 1] - P[:, 1])
    order = np.lexsort((xc, rows))
    rows, xc = rows[order], xc[order]
    starts = np.flatnonzero(np.r_[True, rows[1:] != rows[:-1]])
    ends = np.r_[starts[1:], len(rows)]
    for s0, e0 in zip(starts, ends):
        xs = xc[s0:e0]
        r = rows[s0]
        for k in range(0, len(xs) - 1, 2):
            c0 = int(np.ceil((xs[k] - x0) / g - 0.5)); c1 = int(np.ceil((xs[k + 1] - x0) / g - 0.5))
            if c1 > c0:
                img[r, max(c0, 0):min(c1, nx)] = True
    return img


def check(name, layer=0.2, g=0.2):
    T = load(os.path.join(PRINT, "%s-%s-print.stl" % (PRE, name)))
    V = T.reshape(-1, 3)
    x0, y0 = V[:, 0].min() - 1, V[:, 1].min() - 1
    nx, ny = int((V[:, 0].max() + 1 - x0) / g) + 1, int((V[:, 1].max() + 1 - y0) / g) + 1
    top = V[:, 2].max()
    cell = g * g
    below = None
    found = []
    z = layer / 2
    while z < top:
        img = rasterise(section_segments(T, z), x0, y0, nx, ny, g)
        if below is not None and img.any():
            support = ndimage.binary_dilation(below, EIGHT)
            lab, n = ndimage.label(img, EIGHT)
            if n:
                areas = ndimage.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1)) * cell
                rest = ndimage.sum(support, lab, index=np.arange(1, n + 1)) * cell
                for k in range(n):
                    if areas[k] < 0.5:
                        continue
                    frac = rest[k] / areas[k]
                    if rest[k] <= 0:
                        kind = "FLOATING"
                    elif frac < 0.20:
                        isl = lab == k + 1
                        hang = isl & ~support
                        dist = ndimage.distance_transform_edt(~(isl & support)) * g
                        if dist[hang].max(initial=0) <= 2.0:
                            continue
                        kind = "WEAK"
                    else:
                        continue
                    ys, xs = np.nonzero(lab == k + 1)
                    found.append((kind, z, x0 + (xs.mean() + 0.5) * g, y0 + (ys.mean() + 0.5) * g, areas[k],
                                  (x0 + xs.min() * g, x0 + (xs.max() + 1) * g, y0 + ys.min() * g, y0 + (ys.max() + 1) * g)))
        below = img
        z += layer
    merged = []
    for kind, zz, cx, cy, ar, bb in found:
        for m in merged:
            if m["kind"] == kind and abs(m["x"] - cx) < 5 and abs(m["y"] - cy) < 5 and zz - m["z1"] <= 1.5 * layer:
                m["z1"] = zz; m["area"] = max(m["area"], ar); break
        else:
            merged.append(dict(kind=kind, x=cx, y=cy, z0=zz, z1=zz, area=ar, bb=bb))
    print("%s: %d layers, %d issue(s)" % (name, int(top / layer), len(merged)))
    for m in merged:
        b = m["bb"]
        print("  %-8s z %6.1f..%6.1f  at x %6.1f y %6.1f  island %6.1f mm2  bbox x %.1f..%.1f y %.1f..%.1f" % (
            m["kind"], m["z0"], m["z1"], m["x"], m["y"], m["area"], b[0], b[1], b[2], b[3]))
    return merged


def overhangs(name, layer=0.2, g=0.2, min_reach=0.8, min_area=1.0):
    """Overhang scan (what the slicer calls a cantilever): per layer, the cells more than one grid
    cell (45 deg at g = layer) past the layer below, split into regions. For each region: its
    area, how far it reaches from the supported edge, and on how many sides it is held (a region
    held on one side is a cantilever; on two or more, a bridge). Regions are merged over layers."""
    T = load(os.path.join(PRINT, "%s-%s-print.stl" % (PRE, name)))
    V = T.reshape(-1, 3)
    x0, y0 = V[:, 0].min() - 1, V[:, 1].min() - 1
    nx, ny = int((V[:, 0].max() + 1 - x0) / g) + 1, int((V[:, 1].max() + 1 - y0) / g) + 1
    top = V[:, 2].max()
    below, found = None, []
    z = layer / 2
    while z < top:
        img = rasterise(section_segments(T, z), x0, y0, nx, ny, g)
        if below is not None and img.any():
            sup = ndimage.binary_dilation(below, EIGHT)
            hang = img & ~sup
            lab, n = ndimage.label(hang, EIGHT)
            for k in range(1, n + 1):
                reg = lab == k
                area = reg.sum() * g * g
                if area < min_area:
                    continue
                reach = ndimage.distance_transform_edt(~(img & sup)).__getitem__(reg).max() * g
                if reach < min_reach:
                    continue
                rim = ndimage.binary_dilation(reg, EIGHT, iterations=2) & img & sup
                sides = ndimage.label(rim, EIGHT)[1]
                edge = ndimage.binary_dilation(reg, EIGHT) & ~reg
                held = (edge & img & sup).sum() / max(edge.sum(), 1)
                if sides <= 1 and held > 0.6:
                    sides = 2                                   # support all round (an enclosed roof): a bridge
                ys, xs = np.nonzero(reg)
                found.append(dict(z=z, x=x0 + (xs.mean() + 0.5) * g, y=y0 + (ys.mean() + 0.5) * g, area=area, reach=reach,
                                  kind="CANTILEVER" if sides <= 1 else "bridge", bb=(x0 + xs.min() * g, x0 + (xs.max() + 1) * g,
                                                                                     y0 + ys.min() * g, y0 + (ys.max() + 1) * g)))
        below = img
        z += layer
    merged = []
    for f in found:
        for m in merged:
            if m["kind"] == f["kind"] and abs(m["x"] - f["x"]) < 6 and abs(m["y"] - f["y"]) < 6 and f["z"] - m["z1"] <= 1.5 * layer:
                m["z1"] = f["z"]; m["area"] += f["area"]; m["reach"] = max(m["reach"], f["reach"]); break
        else:
            merged.append(dict(f, z0=f["z"], z1=f["z"]))
    merged.sort(key=lambda m: (m["kind"] != "CANTILEVER", -m["reach"]))
    cant = [m for m in merged if m["kind"] == "CANTILEVER"]
    print("%s: %d cantilever region(s), %d bridge region(s)" % (name, len(cant), len(merged) - len(cant)))
    for m in merged[:40]:
        b = m["bb"]
        print("  %-10s z %6.1f..%6.1f  at x %6.1f y %6.1f  reach %4.1f mm  area %6.1f mm2  bbox x %.1f..%.1f y %.1f..%.1f" % (
            m["kind"], m["z0"], m["z1"], m["x"], m["y"], m["reach"], m["area"], b[0], b[1], b[2], b[3]))
    return cant


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    layer = float(args[0]) if len(args) > 0 else 0.2
    g = float(args[1]) if len(args) > 1 else 0.2
    parts = ("tray-cradle", "bezel", "backstrap", "bib-strap-left", "bib-strap-right")
    parts = tuple(p for p in parts if os.path.exists(os.path.join(PRINT, "%s-%s-print.stl" % (PRE, p))))
    if "--overhangs" in sys.argv:
        for n in parts:
            overhangs(n, layer, g)
        return
    bad = 0
    for n in parts:
        bad += len(check(n, layer, g))
    print("ISLANDS " + ("CLEAN" if not bad else "%d ISSUE(S)" % bad))


if __name__ == "__main__":
    main()
