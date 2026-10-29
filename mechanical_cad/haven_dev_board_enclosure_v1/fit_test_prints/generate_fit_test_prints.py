"""S/M/L fit-test shells: the v3 body scaled, with ONE nozzle size for all three.

The first set (Sep 18) scaled the whole v3 part uniformly, so the nozzle went
4.9 / 5.4 / 5.9 mm. That's wrong: ear-canal size is handled by tip size, so
every body size takes the same 5.4 mm nozzle and the same tips
(../../rev_a_shell/nozzle.py, the 2026-10-28 seal spec).

Bodies are empty fit mocks: v3 outer loft scaled by S/M/L, constant 1.2 mm
wall, no electronics cut-outs. The nozzle bore runs into the hollow body,
which also lets resin drain when printing.

Run: `python generate_fit_test_prints.py` (writes the three STLs and a preview).
"""
import math
import os
import sys

import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rev_a_shell"))
import nozzle as nz  # noqa: E402

WALL = 1.2
SCALES = {"S": 0.9, "M": 1.0, "L": 1.1}
# v3 stations, top to bottom: (z, half-width-x, half-width-y, centre-y offset)
# Copied from ../inear_v3_lofted/generate_inear_enclosure_v3.py.
STATIONS = [
    (17.0, 3.2, 2.7, 0.0),
    (12.0, 10.5, 9.0, 0.0),
    (5.0, 10.3, 8.8, -0.6),
    (-3.0, 8.5, 7.2, -2.0),
    (-9.5, 5.5, 4.8, -4.0),
    (-14.5, 3.0, 2.7, -5.8),
]
NOZZLE_TILT = 20  # degrees, same as v3


def loft(stations):
    wp = cq.Workplane("XY")
    z_prev = cy_prev = None
    for i, (z, rx, ry, cy) in enumerate(stations):
        if i == 0:
            wp = wp.workplane(offset=z).center(0, cy).ellipse(rx, ry)
        else:
            wp = wp.workplane(offset=z - z_prev).center(0, cy - cy_prev).ellipse(rx, ry)
        z_prev, cy_prev = z, cy
    return wp.loft(ruled=False).val()


def build(scale):
    outer_st = [(z * scale, rx * scale, ry * scale, cy * scale) for z, rx, ry, cy in STATIONS]
    inner_st = [(z, max(rx - WALL, 0.3), max(ry - WALL, 0.3), cy) for z, rx, ry, cy in outer_st[:5]]
    inner_st[0] = (inner_st[0][0] - 1.5,) + inner_st[0][1:]
    body = loft(outer_st).cut(loft(inner_st))
    a = math.radians(180 - NOZZLE_TILT)
    axis = cq.Vector(0, -math.sin(a), math.cos(a))
    tip_z, tip_cy = outer_st[-1][0], outer_st[-1][3]
    base = cq.Vector(0, tip_cy, tip_z)
    body = body.fuse(nz.nozzle_solid(base, axis, nz.NOZZLE_LEN, root_len=1.0))
    back = 6.0 * scale  # reach back through the solid neck into the hollow
    body = body.cut(nz.bore_solid(base - axis * back, axis, back + nz.NOZZLE_LEN + 1.0)).clean()
    return body, base, axis


def check(body, base, axis):
    c = BRepClass3d_SolidClassifier(body.wrapped)

    def st(p):
        c.Perform(gp_Pnt(*p.toTuple()), 1e-6)
        return str(c.State()).split("_")[-1]

    u = cq.Vector(1, 0, 0)
    bore_ok = all(st(base + axis * s) == "OUT" for s in np.arange(-5.0, nz.NOZZLE_LEN + 0.5, 0.25))
    wall_ok = st(base + axis * 2.0 + u * ((nz.BORE_D + nz.NOZZLE_OD) / 4)) == "IN"
    lip_ok = st(base + axis * (nz.NOZZLE_LEN - 0.9) + u * (nz.NOZZLE_OD / 2 + 0.2)) == "IN"
    seat_ok = st(base + axis * (nz.NOZZLE_LEN - nz.LIP_LEN - 0.6) + u * (nz.NOZZLE_OD / 2 + 0.15)) == "OUT"
    return bore_ok, wall_ok, lip_ok, seat_ok


def main():
    fig = plt.figure(figsize=(12, 4.6))
    for i, (size, s) in enumerate(SCALES.items()):
        body, base, axis = build(s)
        bore_ok, wall_ok, lip_ok, seat_ok = check(body, base, axis)
        bb = body.BoundingBox()
        print(f"{size}: scale {s}  bbox {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm  "
              f"bore open {bore_ok}, wall {wall_ok}, lip {lip_ok}, tip seat {seat_ok}")
        cq.exporters.export(cq.Workplane(obj=body), os.path.join(HERE, f"haven_fit_test_{size}.stl"),
                            tolerance=0.01, angularTolerance=0.1)
        verts, tris = body.tessellate(0.05, 0.3)
        V = np.array([v.toTuple() for v in verts]); T = np.array(tris)
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(V[T], facecolor="#c9d3d8", edgecolor="#4b5560", linewidths=0.04))
        lim = 26
        ax.set_xlim(-lim / 2, lim / 2); ax.set_ylim(-lim / 2 - 5, lim / 2 - 5); ax.set_zlim(-22, 20)
        ax.view_init(5, 0); ax.set_title(f"{size}: body x{s}, nozzle 5.4 mm", fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Fit-test shells: body scales, nozzle doesn't (same axes for all three)", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "preview_fit_test_SML.png"), dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
