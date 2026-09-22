#!/usr/bin/env python3
"""Renders of the bib straps on the dressed robot.

    python render_overalls.py

Reuses render.py's painter (STL triangles in one Poly3DCollection, no GPU). Reads the three
existing enclosure STLs unchanged and adds the strap pair, so the renders show exactly what a
print would look like beside what is already on the robot.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as R
import overalls as O

OUT = os.path.join(HERE, "out")
RDIR = os.path.join(OUT, "render")
STRAP = (0.30, 0.46, 0.70)          # a shade lighter than the denim, so the strap reads against the shell


def load(name):
    return R.subdivide(R.load_stl(os.path.join(OUT, "stl", "%s-%s.stl" % (R.PRE, name))))


def main():
    os.makedirs(RDIR, exist_ok=True)
    reachy = R.load_stl(os.path.join(R.REPO, "cad", "reachy-mini", "reachy_mini_body.stl"))
    base = {n: load(n) for n in ("bezel", "tray-cradle", "backstrap")}
    straps = [load("%s-%s" % (O.NAME, s)) for s in ("left", "right")]
    full = ([(reachy, R.REACHY), (R.board_in_robot(), R.BOARD), (base["tray-cradle"], R.DENIM),
             (base["backstrap"], R.DENIM), (base["bezel"], R.DENIM_DARK)]
            + [(s, STRAP) for s in straps])
    R.draw(full, "overalls-front", 8, 0, "bib straps: over the rim, down the shell, hooked behind the panel")
    R.draw(full, "overalls-hero", 20, 38, "bib straps - three-quarter")
    R.draw(full, "overalls-side", 6, 90, "bib straps - robot's left", light=(0.2, 0.9, 0.35))
    R.draw(full, "overalls-high", 34, 20, "bib straps - from above the shoulder")
    # the gap on its own: the strap, the shell and the panel's back, nothing else in the way
    R.draw(full, "overalls-gap", 2, 62, "the gap behind the panel: shell run, lean-in, bezel hook",
           lims=((30.0, 110.0), (18.0, 60.0), (120.0, 190.0)), zoom=1.0, light=(0.25, 0.85, 0.4))
    for s in ("left", "right"):
        T = R.subdivide(R.load_stl(os.path.join(OUT, "print", "%s-%s-%s-print.stl" % (R.PRE, O.NAME, s))))
        R.draw([(T, STRAP)], "print-%s-%s" % (O.NAME, s), 32, -60, "bib strap %s - as printed (on the bed)" % s)
    print("wrote", RDIR)


if __name__ == "__main__":
    main()
