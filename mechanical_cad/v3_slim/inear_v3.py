"""Haven v3 in-ear piece, option I1 (speaker only, microphone stays on the pod): first PRINTABLE draft, 2026-11-14.

A small capsule that holds the speaker and carries a standard sealing ear tip. Two printed parts:
  - BODY: cup for the speaker with the nozzle on its front. The speaker drops in from the back, face toward the nozzle.
  - CAP: closes the back. The two-wire cable leaves through a stub on the cap, pointing up toward the top of the ear.
Seal spec is the project's existing one (PROJECT_STATUS.md "Seal spec"): nozzle 5.4 mm, 5-6 mm long, 0.3-0.5 mm lip,
for 4.5 mm-bore foam or silicone tips, NO vent.

SPEAKER, from the maker's drawing (Ole Wolff OWR-0504T-16 preliminary specification Rev 00, 2022-08-25, Fig. 4; copy in
~/.cache/haven_datasheets/speaker/): front cap 4.9 +-0.07 mm across and 1.3 mm tall with a 1.3 mm sound hole in the
centre of its face; widest point 5.1 mm (the ring behind the cap); body 4.1 +-0.15 mm tall; two flat solder tabs, 1.0 mm
wide, reach 0.8 mm past the back (4.9 mm overall); rear magnet section 3.2 mm; 0.17 g. Modelled here as a 5.1 x 4.1 mm
cylinder with 1.2 mm of room behind it for the tabs and joints. The same document gives 104 +-2.5 dB SPL at 1 kHz for
0.179 V in an IEC 60318-4 ear simulator (their test jig, not this housing). NOT measured on a real part.
SERIES RESISTOR: a 220 ohm 0402 is soldered between one speaker tab and its wire, inside the 1.2 mm space behind the
speaker (passive loudness limit, DESIGN_BRIEF_SHELL_V3.md "Worst-case loudness"; value provisional).
NOT designed: wax guard, glue channel, strain relief inside the cap, left/right difference (the part is symmetric, so one
print fits both ears), acoustic tuning of the back volume (sealed and small, which will raise the speaker's resonance: measure
in the ear simulator).

    python3 inear_v3.py   ->  inear_v3_body.step/.stl, inear_v3_cap.step/.stl, inear_v3_assembly.stl, inear_v3_section.png
"""
import math
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
SPK_D, SPK_H = 5.1, 4.1           # speaker envelope: widest diameter, body height (maker's drawing)
CLR, WALL = 0.15, 0.8             # radial clearance around the speaker, printed wall
SEAT = 0.8                        # front wall the speaker's face rests on
BORE = 2.6                        # sound bore through seat and nozzle
NOZ_D, NOZ_L = 5.4, 5.5           # nozzle for 4.5 mm-bore tips
LIP_D, LIP_L = 6.1, 0.9           # retaining lip at the nozzle end (0.35 mm proud)
BACK = 1.2                        # behind the speaker: 0.8 mm solder tabs + joints
CAP_T, CAP_PLUG = 0.8, 0.8        # cap thickness, depth of the plug that centres it in the body
CABLE_D, STUB_D, STUB_L = 1.1, 2.3, 2.0   # two-wire cable hole, stub around it, stub length
STUB_TILT = 35                    # degrees the cable stub leans back from straight up

POCKET_D = SPK_D + 2 * CLR
BODY_D = POCKET_D + 2 * WALL
BODY_L = SEAT + SPK_H + BACK + CAP_PLUG          # z = 0 is the front face of the body (nozzle root), body runs to -BODY_L

# BODY: revolve the half-profile (r, z) around z
prof = [(BORE / 2, NOZ_L), (LIP_D / 2 - 0.25, NOZ_L), (LIP_D / 2, NOZ_L - 0.3), (LIP_D / 2, NOZ_L - LIP_L + 0.3),
        (NOZ_D / 2, NOZ_L - LIP_L), (NOZ_D / 2, 0.6), (BODY_D / 2 - 0.6, 0.0), (BODY_D / 2, -0.8), (BODY_D / 2, -BODY_L),
        (POCKET_D / 2, -BODY_L), (POCKET_D / 2, -SEAT), (BORE / 2, -SEAT)]
body = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))

# CAP: disc with a centring plug and a tilted cable stub
cap = (cq.Workplane("XY").workplane(offset=-BODY_L - CAP_T).circle(BODY_D / 2).extrude(CAP_T)
       .faces(">Z").workplane().circle(POCKET_D / 2 - 0.08).extrude(CAP_PLUG))
cap = cap.edges("<Z").fillet(0.5)
tilt = math.radians(STUB_TILT)
axis = cq.Vector(0, math.cos(tilt), -math.sin(tilt))          # up (+y) and back (-z)
start = cq.Vector(0, BODY_D / 2 - 1.6, -BODY_L - CAP_T / 2)
plane = cq.Plane(origin=start, xDir=cq.Vector(1, 0, 0), normal=axis)
stub = cq.Workplane(plane).circle(STUB_D / 2).extrude(STUB_L + 1.2)
hole = cq.Workplane(cq.Plane(origin=start - axis * 3.0, xDir=cq.Vector(1, 0, 0), normal=axis)).circle(CABLE_D / 2).extrude(STUB_L + 6.0)
keep = cq.Workplane("XY").workplane(offset=-BODY_L - CAP_T - 10).circle(20).extrude(10 + CAP_T)      # nothing of the stub above the cap's inner face
cap = cap.union(stub.intersect(keep)).cut(hole)

speaker = cq.Workplane("XY").workplane(offset=-SEAT - SPK_H).circle(SPK_D / 2).extrude(SPK_H)

# a generic single-flange silicone tip, for pictures only
tip_prof = [(NOZ_D / 2, 0.9), (NOZ_D / 2 + 0.7, 0.9), (5.6, 1.6), (6.0, 3.0), (5.6, 5.0), (4.2, 7.4), (2.9, 8.4), (BORE / 2 + 0.3, 8.4),
            (BORE / 2 + 0.3, NOZ_L + 0.3), (NOZ_D / 2, NOZ_L + 0.3)]
tip = cq.Workplane("XZ").polyline(tip_prof).close().revolve(360, (0, 0, 0), (0, 1, 0))

for name, part in (("body", body), ("cap", cap)):
    cq.exporters.export(part, os.path.join(HERE, f"inear_v3_{name}.step"))
    cq.exporters.export(part, os.path.join(HERE, f"inear_v3_{name}.stl"), tolerance=0.01, angularTolerance=0.1)
for name, part in (("speaker", speaker), ("tip", tip)):
    cq.exporters.export(part, os.path.join(HERE, f"inear_v3_preview_{name}.stl"), tolerance=0.02, angularTolerance=0.15)

bb = body.union(cap).val().BoundingBox()
vol = lambda p: p.val().Volume()
RHO = 1.18          # g/cm3, typical printed resin
print(f"body {BODY_D:.1f} mm across x {BODY_L + CAP_T:.1f} mm long, nozzle {NOZ_D} x {NOZ_L} mm; overall hard part "
      f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
print(f"printed volume: body {vol(body):.0f} mm3, cap {vol(cap):.0f} mm3 -> about {(vol(body) + vol(cap)) * RHO / 1000:.2f} g at {RHO} g/cm3")
print(f"back volume behind the speaker: {math.pi * (POCKET_D / 2) ** 2 * BACK:.0f} mm3")

# section picture
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
fig, ax = plt.subplots(figsize=(9, 4.6))
for sgn in (1, -1):
    ax.add_patch(Polygon([(z, sgn * r) for r, z in prof], closed=True, fc="#c9c2b6", ec="k", lw=0.8))
    ax.add_patch(Polygon([(z, sgn * r) for r, z in tip_prof], closed=True, fc="#9fc5d8", ec="k", lw=0.6, alpha=0.7))
ax.add_patch(Rectangle((-SEAT - SPK_H, -SPK_D / 2), SPK_H, SPK_D, fc="#e0a84a", ec="k", lw=0.8))
ax.add_patch(Rectangle((-BODY_L - CAP_T, -BODY_D / 2), CAP_T, BODY_D, fc="#8d8577", ec="k", lw=0.8))
ax.add_patch(Rectangle((-BODY_L, -POCKET_D / 2 + 0.08), CAP_PLUG, POCKET_D - 0.16, fc="#8d8577", ec="k", lw=0.8))
ax.text(-SEAT - SPK_H / 2, 0, "speaker\n(5.1 x 4.1 envelope)", ha="center", va="center", fontsize=8)
ax.text(NOZ_L / 2, 0, "sound bore 2.6", ha="center", va="center", fontsize=7)
ax.text(6.0, 6.6, "ear tip (stand-in shape)", ha="center", fontsize=8, color="#2b5d73")
ax.text(-BODY_L - CAP_T - 0.2, 0, "cap", ha="right", va="center", fontsize=8)
ax.annotate("", xy=(-BODY_L - CAP_T, -BODY_D / 2 - 0.9), xytext=(NOZ_L, -BODY_D / 2 - 0.9), arrowprops=dict(arrowstyle="<->", lw=0.8))
ax.text((NOZ_L - BODY_L - CAP_T) / 2, -BODY_D / 2 - 1.6, f"{BODY_L + CAP_T + NOZ_L:.1f} mm", ha="center", fontsize=8)
ax.annotate("", xy=(-BODY_L / 2, -BODY_D / 2), xytext=(-BODY_L / 2, BODY_D / 2), arrowprops=dict(arrowstyle="<->", lw=0.8))
ax.text(-BODY_L / 2 + 0.2, BODY_D / 2 + 0.3, f"{BODY_D:.1f} mm", fontsize=8)
ax.set_xlim(-9, 10.5); ax.set_ylim(-7.5, 7.5); ax.set_aspect("equal"); ax.set_xlabel("mm (ear canal to the right)")
ax.set_title("Haven v3 in-ear piece, option I1: section through the axis (cable stub not shown)")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "inear_v3_section.png"), dpi=140)
