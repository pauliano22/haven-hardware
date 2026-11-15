"""Haven v3 charging CRADLE for two pods (2026-11-14). Plugs into any USB-C charger; no battery, no electronics
beyond a small contact board.

How it works
- Each pod lies head-side down in a pocket shaped like the pod. Its two spring pins (P1 = VBUS at pod x = -1.3,
  P2 = GND at x = +1.3, y = 8.65) land on two gold pads on a small circuit board (the "dock board",
  hardware_kicad/tools/gen_cradle_v3_pcb.py). The pod's own charging chip (nPM1100) does the charging.
- The pod rests on the board at its flat contact land (LAND_* in pod_v3_styled.py, z = -4.4). The pins stand 0.5 mm
  proud of the land, so the pads push them in 0.5 mm.
- The board has a hole under each pod for the rest of the pod's curved head side; a printed cup under the hole
  follows the pod's shape with CLR_FLOOR clearance, so the pod rests on the land, not on the cup.
- A lid held by 4 pairs of disc magnets presses both pods down: the lid rests on the pods (LID_GAP above the frame),
  so the magnets' pull goes into the pods, not the frame. Spring pins push back about 4 x 130 gf at most.
- The speaker cable leaves each pocket through an open-top slot at the cable end; the lid closes over it.

Parts (all printed, same resin as the shell is fine): base (under the board), frame (on the board, with the pockets),
lid. Bought: 8 disc magnets 5 x 2 mm N52 (polarity: base-frame magnets one way up, lid magnets the other), 4 screws
M2 x 8 self-tapping (through frame and board into the base). Board: JLCPCB, fully assembled.

Coordinates: cradle frame X (across both pods), Y (along the pods; +Y = the pods' cable end), Zc up, with Zc = 0 the
board's top face. A pod sits translated only: (X, Y, Zc) = (x + XJ, y, z - LAND_Z).

    python3 cradle_v3.py  ->  cradle_v3_base.stl, cradle_v3_frame.stl, cradle_v3_lid.stl,
                              cradle_v3_layout.json (read by the board generator), cradle_v3_section.png
NOT checked: printing, magnet strength in practice, contact force at 0.5 mm travel (datasheet gives 130 gf +-20 %
at the 1.0 mm working point only), whether the pods sit flat with real tolerances.
"""
import json
import os

import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

import pod_v3_styled as st

HERE = os.path.dirname(os.path.abspath(__file__))
RES = 0.1
XJ = (-8.2, 8.2)                          # pod centres across the cradle
BODY = (-21.5, 21.5, -31.0, 22.5)         # outer outline X0, X1, Y0, Y1 (rounded corners R_BODY)
R_BODY = 3.0
PCB = (-20.5, 20.5, -30.0, 21.5)          # dock board outline; 0.5 mm all round inside the body
PCB_T = 1.6
Z_BASE0, Z_FRAME1 = -4.6, 6.0             # base bottom, frame top
LID_GAP, LID_TOP = 0.3, 9.9
CLR_SIDE, CLR_FLOOR = 0.25, 0.3           # pocket clearance sideways, cup clearance under the pod
TONGUE_HALF_W, TONGUE_Y0 = 2.5, 6.8       # board tongue under the pins (inside the land, which is +-2.7, 6.6..10.6)
CUT_Y = (-18.2, 10.0)                     # board hole under each pod, Y span; X span = XJ +- CUT_HALF_W
CUT_HALF_W = 6.6
PIN_X, PIN_Y = (-1.3, 1.3), 8.65          # VBUS, GND (pod frame), from the pod board P1 / P2
MAG_D, MAG_H = 5.2, 2.1                   # pocket for a 5 x 2 mm magnet
MAGNETS = [(-18.2, -12.0), (18.2, -12.0), (-18.2, 10.0), (18.2, 10.0)]
SCREWS = [(-18.2, -27.5), (18.2, -27.5), (-18.2, 19.0), (18.2, 19.0)]
SCREW_CLR, SCREW_PILOT, SCREW_HEAD, SCREW_HEAD_H = 2.3, 1.6, 4.2, 1.8
USB = dict(x=0.0, y_edge=PCB[2], body=(-5.2, 5.2, -30.0, -20.9, 0.0, 3.6),        # receptacle + its rear pads, on the board
           plug=(-6.6, 6.6, -1.9, 5.1))                                           # opening for the plug overmold: X0, X1, Zc0, Zc1
PARTS_AREA = (-9.0, 9.0, -22.2, -12.0, 0.0, 1.3)                                   # CC resistors, capacitor, tracks: on the web between the pods
USB_LEGS = (-5.6, 5.6, -30.5, -24.0, 1.3)                                          # shell legs poke out under the board: base relief X0, X1, Y0, Y1, depth
CABLE = dict(x=2.2, w=1.7, z0=4.8)                                                 # speaker-wire slot (pod x), open to the top
NOTCH = dict(y=-3.0, r=4.0, z0=2.5)                                                # finger notch on each pocket's outer side
LID_NOTCH = (-5.0, 5.0, BODY[3] - 2.0, BODY[3] + 1, 4.5)                             # thumb notch in the frame under the lid edge, to lift the lid

# ---------------------------------------------------------------- pod height maps on the cradle grid
pod = st.mask.copy()
px, py, pz = (st.lo[i] + RES * np.arange(st.shape[i]) for i in range(3))
PX, PY, PZ = np.meshgrid(px, py, pz, indexing="ij")
pod &= ~((PX >= st.LAND_X[0]) & (PX <= st.LAND_X[1]) & (PY >= st.LAND_Y[0]) & (PY <= st.LAND_Y[1]) & (PZ < st.LAND_Z))
has = pod.any(2)
zb = np.where(has, pz[np.argmax(pod, 2)], np.inf) - st.LAND_Z                       # pod underside, Zc
zt = np.where(has, pz[pod.shape[2] - 1 - np.argmax(pod[:, :, ::-1], 2)], -np.inf) - st.LAND_Z

xs = np.arange(BODY[0] - 1, BODY[1] + 1 + 1e-9, RES)
ys = np.arange(BODY[2] - 1, BODY[3] + 1 + 1e-9, RES)
zs = np.arange(Z_BASE0 - 0.5, LID_TOP + 0.5 + 1e-9, RES)
GX, GY = np.meshgrid(xs, ys, indexing="ij")
ZB = np.full(GX.shape, np.inf); ZT = np.full(GX.shape, -np.inf)
for xj in XJ:
    ix = np.round((GX - xj - px[0]) / RES).astype(int); iy = np.round((GY - py[0]) / RES).astype(int)
    ok = (ix >= 0) & (ix < len(px)) & (iy >= 0) & (iy < len(py))
    ZB[ok] = np.minimum(ZB[ok], zb[ix[ok], iy[ok]]); ZT[ok] = np.maximum(ZT[ok], zt[ix[ok], iy[ok]])
disk = lambda r: (lambda k: (np.add.outer(k * k, k * k) <= (r / RES) ** 2))(np.arange(-int(r / RES), int(r / RES) + 1))
foot = ndimage.binary_dilation(np.isfinite(ZB), disk(CLR_SIDE))                    # pocket footprint, side clearance
ZB_c = ndimage.grey_erosion(np.where(np.isfinite(ZB), ZB, 99.0), footprint=disk(CLR_SIDE))
ZT_c = ndimage.grey_dilation(np.where(np.isfinite(ZT), ZT, -99.0), footprint=disk(CLR_SIDE))


def rect(x0, x1, y0, y1):
    return (GX >= x0) & (GX <= x1) & (GY >= y0) & (GY <= y1)


def rrect(x0, x1, y0, y1, r):
    cx = np.clip(GX, x0 + r, x1 - r); cy = np.clip(GY, y0 + r, y1 - r)
    return rect(x0, x1, y0, y1) & ((GX - cx) ** 2 + (GY - cy) ** 2 <= r * r)


def circ(c, d):
    return (GX - c[0]) ** 2 + (GY - c[1]) ** 2 <= (d / 2) ** 2


body = rrect(*BODY, R_BODY)
pcb = rrect(*PCB, 1.0)
holes = np.zeros_like(body)
for xj in XJ:
    holes |= rrect(xj - CUT_HALF_W, xj + CUT_HALF_W, CUT_Y[0], CUT_Y[1], 1.0) & ~rect(xj - TONGUE_HALF_W, xj + TONGUE_HALF_W, TONGUE_Y0, 99)
for s in SCREWS:
    holes |= circ(s, 2.2)
board = pcb & ~holes

# ---------------------------------------------------------------- checks on the fit
under = board & np.isfinite(ZB)
low = ZB[under].min() if under.any() else np.inf
assert low >= -0.05, f"pod dips {low:.2f} mm into the board outside the holes"
on_tongue = board & np.isfinite(ZB) & (ZB < 0.15)
pin_pads = []
for xj in XJ:
    for k, px_ in enumerate(PIN_X):
        x, y = xj + px_, PIN_Y
        i, j = int(round((x - xs[0]) / RES)), int(round((y - ys[0]) / RES))
        assert board[i, j], f"pad at ({x}, {y}) is not on the board"
        pin_pads.append(dict(x=x, y=y, net="VBUS" if k == 0 else "GND"))
press = st.PIN_FREE_TIP_Z - st.LAND_Z
print(f"pod rests on the board over {on_tongue.sum() * RES * RES:.1f} mm2 per cradle (both pods); pin travel "
      f"{-press:.2f} mm of 1.0; pod top Zc {ZT[np.isfinite(ZT)].max():.2f}; pocket floor clearance {CLR_FLOOR} mm")

# ---------------------------------------------------------------- solids on the 3-D grid (built slab by slab)
nz = len(zs)
base = np.zeros(GX.shape + (nz,), bool); frame = np.zeros_like(base); lid = np.zeros_like(base)
cup_top = np.where(foot & holes, np.minimum(ZB_c - CLR_FLOOR, 0.0), -PCB_T)        # cup surface inside each board hole
usb_box = rect(*USB["body"][:4])
parts_box = rect(*PARTS_AREA[:4])
cable = np.zeros_like(body)
for xj in XJ:
    cable |= rect(xj + CABLE["x"] - CABLE["w"] / 2, xj + CABLE["x"] + CABLE["w"] / 2, 10.0, 99)
notch2d = np.zeros_like(body)
for xj in XJ:
    side = np.sign(xj)
    notch2d |= circ((xj + side * (CUT_HALF_W + 0.4), NOTCH["y"]), 2 * NOTCH["r"]) & body
plug2d = rect(USB["plug"][0], USB["plug"][1], BODY[2] - 1, PCB[2] + 0.2)
for k, z in enumerate(zs):
    # base: under the board, plus the cups that come up through the board holes
    b = body & ((z < -PCB_T) | (holes & (z < cup_top)) | (~pcb & (z < -PCB_T)))
    b &= z >= Z_BASE0
    b &= ~(rect(*USB_LEGS[:4]) & (z >= -PCB_T - USB_LEGS[4]))
    # frame: around the board edge from the base up, and on top of the board
    f = body & (((~pcb) & (z >= -PCB_T)) | (pcb & (z >= 0.0))) & (z < Z_FRAME1)
    f &= ~(foot & (z >= np.minimum(ZB_c - CLR_FLOOR, 0.0)))                          # pockets (drop-in from above)
    f &= ~(usb_box & (z < USB["body"][5])) & ~(parts_box & (z < PARTS_AREA[5]))
    f &= ~(cable & (z >= CABLE["z0"]))
    f &= ~(notch2d & (z >= NOTCH["z0"]))
    f &= ~(rect(*LID_NOTCH[:4]) & (z >= LID_NOTCH[4]))
    f &= ~((holes & pcb) & (z < 0.0))                                               # never into the board's plane
    for m in MAGNETS:
        f &= ~(circ(m, MAG_D) & (z >= Z_FRAME1 - MAG_H))
    for s in SCREWS:
        f &= ~(circ(s, SCREW_CLR)) & ~(circ(s, SCREW_HEAD) & (z >= Z_FRAME1 - SCREW_HEAD_H))
        b &= ~circ(s, SCREW_PILOT)
    if USB["plug"][2] <= z <= USB["plug"][3]:
        f &= ~plug2d; b &= ~plug2d
    # lid: rests on the pods, LID_GAP above the frame
    l = body & (z >= Z_FRAME1 + LID_GAP) & (z <= LID_TOP) & (z >= ZT_c)
    l &= ~(cable & (z < Z_FRAME1 + LID_GAP + 0.8))                                  # groove over the cable slot
    for m in MAGNETS:
        l &= ~(circ(m, MAG_D) & (z < Z_FRAME1 + LID_GAP + MAG_H))
    base[:, :, k], frame[:, :, k], lid[:, :, k] = b, f, l

lid_rest = (ZT_c[foot].max() - (Z_FRAME1 + LID_GAP))
assert lid_rest > 0, "pods do not reach the lid"
assert not (base & frame).any() and not (frame & lid).any()


def export(m, name):
    lo = np.array([xs[0], ys[0], zs[0]])
    sl = ndimage.find_objects(m.astype(np.uint8))[0]
    sub = np.pad(m[sl], 1)
    v, fcs, _, _ = measure.marching_cubes(ndimage.gaussian_filter(sub.astype(np.float32), 0.6), 0.5, spacing=(RES,) * 3)
    off = lo + RES * (np.array([s.start for s in sl]) - 1)
    me = trimesh.Trimesh(v + off, fcs, process=True)
    dec = me.simplify_quadric_decimation(face_count=120000)
    if dec.is_watertight:
        me = dec
    trimesh.repair.fix_normals(me)
    me.export(os.path.join(HERE, name))
    print(f"{name}: {me.extents.round(1).tolist()} mm, watertight {me.is_watertight}, about {abs(me.volume) * 1.2 / 1000:.1f} g resin")
    return me


export(base, "cradle_v3_base.stl")
export(frame, "cradle_v3_frame.stl")
export(lid, "cradle_v3_lid.stl")
print(f"lid sits on the pods with the frame gap {LID_GAP} mm; pods reach {lid_rest:.2f} mm into the lid's recess")

layout = dict(note="written by hardware/mechanical_cad/v3_slim/cradle_v3.py; cradle frame mm (X right, Y toward the "
              "pods' cable end); KiCad uses x = 100 + X, y = 100 - Y", pcb=PCB, pcb_corner_r=1.0, pcb_t=PCB_T,
              pods=XJ, hole_half_w=CUT_HALF_W, hole_y=CUT_Y, tongue_half_w=TONGUE_HALF_W, tongue_y0=TONGUE_Y0,
              pads=pin_pads, screws=SCREWS, usb=USB, parts_area=PARTS_AREA, magnets=MAGNETS)
json.dump(layout, open(os.path.join(HERE, "cradle_v3_layout.json"), "w"), indent=1)

# ---------------------------------------------------------------- section picture through one pod's pins
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axs = plt.subplots(1, 2, figsize=(13, 5))
i = int(round((XJ[1] + PIN_X[0] - xs[0]) / RES))
j = int(round((PIN_Y - ys[0]) / RES))
for ax, (name, cut, ext, lab) in zip(axs, [("along the pod, through the VBUS pin", np.s_[i, :, :], (ys[0], ys[-1]), "Y (mm)"),
                                           ("across both pods, through the pins", np.s_[:, j, :], (xs[0], xs[-1]), "X (mm)")]):
    img = np.zeros(base[cut].shape + (3,)) + 1
    img[base[cut]] = (0.55, 0.6, 0.7); img[frame[cut]] = (0.75, 0.78, 0.85); img[lid[cut]] = (0.6, 0.7, 0.6)
    brd = (board[i, :] if cut[0] == i else board[:, j])[:, None] & ((zs >= -PCB_T) & (zs < 0))[None, :]
    img[brd] = (0.2, 0.5, 0.25)
    podsec = (np.isfinite(ZB[i, :]) if cut[0] == i else np.isfinite(ZB[:, j]))
    zb_ = ZB[i, :] if cut[0] == i else ZB[:, j]; zt_ = ZT[i, :] if cut[0] == i else ZT[:, j]
    inpod = podsec[:, None] & (zs[None, :] >= zb_[:, None]) & (zs[None, :] <= zt_[:, None])
    img[inpod] = (0.95, 0.85, 0.6)
    ax.imshow(np.transpose(img, (1, 0, 2)), origin="lower", extent=(ext[0], ext[1], zs[0], zs[-1]), aspect="equal")
    ax.set_title(name); ax.set_xlabel(lab); ax.set_ylabel("Zc (mm)")
fig.suptitle("Haven v3 cradle section: base (blue-grey), frame (light), lid (green), dock board (dark green), pod (sand, outer form)")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "cradle_v3_section.png"), dpi=110)
print("wrote cradle_v3_section.png, cradle_v3_layout.json")
