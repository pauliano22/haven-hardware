"""Haven v3 slim pod: rough 3D check for DESIGN_BRIEF_SHELL_V3.md (2026-11-11). NOT a release shell.

Layout ("sandwich"): a pouch cell lies flat against the head-side face of a narrow board for its full
length; every component, including the radio module, is on the other (lateral) face. Same shell
construction as ../v2_bte/bte.py. Frame: X toward the pinna, Y up along the pod, Z lateral.

    python3 pod_v3.py A    Raytac MDBT53V-1M (12.4 x 7.8 x 1.85), cell 4.0 x 10 x 22
    python3 pod_v3.py B    Insight SiP ISP2053 (8 x 8 x 1.0),     cell 4.0 x 10 x 22
    python3 pod_v3.py A 0.8 0.25   optional wall and clearance (default: v2's 1.1 and 0.4)
Writes pod_v3_<A|B>[_thin]_R.stl and prints the bounding box and estimated mass.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "v2_bte"))
import bte  # noqa: E402
from bte import cc, gen, Box, Cyl, Y_, Z_, X_, unit  # noqa: E402

variant = sys.argv[1] if len(sys.argv) > 1 else "A"
thin = len(sys.argv) > 3
if thin:
    for m in (cc, gen):
        m.WALL, m.CLR = float(sys.argv[2]), float(sys.argv[3])

BOARD = dict(A=(9.6, 27.0, 0.8), B=(9.6, 24.0, 0.8))[variant]   # 0.8 mm: JLCPCB thinnest 6-layer
MODULE = dict(A=(12.4, 7.8, 1.85, 0.4), B=(8.0, 8.0, 1.0, 0.2))[variant]   # length along Y, width, height, mass g
CELL = (10.0, 17.0, 4.0, 1.0)        # 17 mm cell chosen 2026-11-11 (width, length incl. protection board, thickness, mass g est.)
SWELL = 0.3                          # room for the pouch to swell
TOP_H = 1.0                          # tallest non-module part on the lateral face (inductor)

W, L, T = BOARD
pcb = Box("pcb", [0, 0, 0], [W, L, T], np.eye(3), 0.30 * W * L / (13 * 27))
mod = Box("module", [0, L / 2 - MODULE[0] / 2, T / 2 + MODULE[2] / 2], [MODULE[1], MODULE[0], MODULE[2]], np.eye(3), MODULE[3])
top = Box("top_parts", [0, -MODULE[0] / 2, T / 2 + TOP_H / 2], [W - 0.6, L - MODULE[0] - 0.6, TOP_H], np.eye(3), 0.15)
cell_h = CELL[2] + SWELL
bat = Box("battery", [0, -L / 2 + CELL[1] / 2, -(T / 2 + 0.1 + cell_h / 2)], [CELL[0], CELL[1], cell_h], np.eye(3), CELL[3])
end = np.array([0.0, -L / 2 - bte.GAP, -1.5])
mag = Cyl("magnet", end - Y_ * 0.1, -Y_, cc.MAG[0], cc.MAG[1], cc.MAG[2])
cable_in = np.array([W / 2 - 0.4, L / 2 - 9.0, 0.9])
cable_dir = unit([0.55, 1.0, 0.1])
boot = Cyl("cable_boot", cable_in, cable_dir, 2.0, 3.0, 0.04)
parts = [pcb, top, mod, bat, mag, boot]
kw = dict(nozzle_B=None, mic=None, pads=(end - Y_ * 0.1, -Y_, X_))
mesh, fd = bte.shell_with_hole(parts, kw, cable_in, cable_dir, hole_d=1.4)
mp = cc.mass_props(mesh, parts, tip=False)
tag = f"pod_v3_{variant}" + ("_thin" if thin else "")
mesh.export(os.path.join(HERE, tag + "_R.stl"))
rep = dict(tag=tag, wall=cc.WALL, clr=cc.CLR, board=BOARD, bbox_mm=[round(float(x), 2) for x in mesh.extents],
           watertight=bool(mesh.is_watertight), checks=cc.clearances(fd, parts), mass_g=mp.get("mass_g"), shell_g=mp.get("shell_g"))
print(json.dumps(rep))
