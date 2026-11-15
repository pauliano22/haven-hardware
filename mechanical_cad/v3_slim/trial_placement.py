"""Haven v3 concept A: trial placement of every pod part on ONE face of a 9.6 x 27 mm board (2026-11-11).

This is a packing test only: it answers "is there room", not "can it be routed". Parts are placed bottom-left
first, biggest first, with no electrical grouping. Each rectangle is the part's body + pads + a keep-apart margin
(so rectangles may touch). Part list = the v2 pod (v2_pod_parts.json, read from the v2 board) with these changes:
  - mic moves to the pod only: cable pads W1-W4 and three of the six ESD diodes go
  - L101/L102 (never fitted) go; L2 becomes a real 2.0 x 1.6 mm power inductor (design review finding 2)
  - X1 (32.768 kHz, 3.2 x 1.5) becomes a 1.6 x 1.0 mm crystal (a part change, not yet chosen)
    python3 trial_placement.py  ->  trial_placement.png, prints the fill and anything that did not fit
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
W, L, EDGE, G = 9.6, 27.0, 0.3, 0.05
MOD = (7.8, 12.4)                        # Raytac module, antenna end at the top edge
SIZE = {  # footprint -> rectangle incl. margin (mm)
    "C0201": (0.95, 0.45), "R0201": (0.95, 0.45), "C0402": (1.5, 0.75), "D_SOD-523": (1.9, 0.9),
    "TestPad_0.8": (1.0, 1.0), "WirePad_0.8": (1.0, 1.0), "Pad_1.2": (1.4, 1.4), "PogoPad_1.6": (1.4, 1.4)}
SPECIAL = {"U15": (3.4, 3.0, "audio chip"), "U2": (2.5, 2.5, "power chip"), "U14": (3.9, 3.1, "mic"), "L2": (2.5, 2.0, "inductor"),
           "CRYSTAL1": (2.5, 2.1, "24.576 MHz"), "X1": (2.0, 1.4, "32 kHz"), "U3": (1.1, 1.1, "switch"), "Q2": (0.9, 0.9, ""), "U4": (0.9, 0.45, "")}
DROP = {"W1", "W2", "W3", "W4", "L101", "L102", "U1", "D4", "D5", "D6"}

parts = []
for p in json.load(open(os.path.join(HERE, "v2_pod_parts.json"))):
    if p["ref"] in DROP:
        continue
    if p["ref"] in SPECIAL:
        w, h, lab = SPECIAL[p["ref"]]
    else:
        w, h = SIZE[p["fp"]]; lab = ""
    parts.append([p["ref"], w, h, lab])
parts.sort(key=lambda p: -max(p[1], p[2]) * 100 - p[1] * p[2])

y_free_top = L - MOD[1] - 0.3            # parts stay 0.3 mm below the module
nx, ny = int(round((W - 2 * EDGE) / G)), int(round((y_free_top - EDGE) / G))
occ = np.zeros((ny, nx), bool)
placed, failed = [], []
for ref, w, h, lab in parts:
    done = False
    for (a, b) in ((w, h), (h, w)):
        ia, ib = int(round(a / G)), int(round(b / G))
        for j in range(0, ny - ib + 1):
            for i in range(0, nx - ia + 1):
                if not occ[j:j + ib, i:i + ia].any():
                    occ[j:j + ib, i:i + ia] = True
                    placed.append((ref, EDGE + i * G, EDGE + j * G, a, b, lab)); done = True; break
            if done: break
        if done: break
    if not done:
        failed.append(ref)
area = sum(p[1] * p[2] for p in parts)
region = (W - 2 * EDGE) * (y_free_top - EDGE)
top_used = max(p[2] + p[4] for p in placed)
print(f"parts {len(parts)}  placed {len(placed)}  failed {failed}")
print(f"part area {area:.1f} mm2 of {region:.1f} mm2 = {100 * area / region:.0f} % ; highest used y = {top_used:.2f} of {y_free_top:.2f} mm")

fig, ax = plt.subplots(figsize=(5, 11))
ax.add_patch(plt.Rectangle((0, 0), W, L, fc="#e8f1e4", ec="k", lw=1.5))
ax.add_patch(plt.Rectangle(((W - MOD[0]) / 2, L - MOD[1]), MOD[0], MOD[1], fc="#9db7d6", ec="k"))
ax.text(W / 2, L - MOD[1] / 2, "radio module\n(antenna at top)", ha="center", va="center", fontsize=9)
for ref, x, y, a, b, lab in placed:
    big = a * b > 2
    ax.add_patch(plt.Rectangle((x, y), a, b, fc="#f2c079" if big else "#c9c9c9", ec="k", lw=0.5))
    if big:
        ax.text(x + a / 2, y + b / 2, f"{ref}\n{lab}", ha="center", va="center", fontsize=6)
ax.set_xlim(-0.5, W + 0.5); ax.set_ylim(-0.5, L + 0.5); ax.set_aspect("equal")
ax.set_title(f"v3 concept A trial placement, one face, 9.6 × 27 mm\n{len(placed)}/{len(parts)} parts, {100 * area / region:.0f} % of the free area. Packing only, not routed.", fontsize=9)
ax.set_xlabel("mm"); fig.tight_layout(); fig.savefig(os.path.join(HERE, "trial_placement.png"), dpi=120)
