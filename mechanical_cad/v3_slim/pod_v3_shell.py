"""Haven v3 slim pod: a PRINTABLE two-part hollow shell made from the rounded outer form of pod_v3_styled.py (2026-11-12).

For a first test print only: to judge size, feel and stiffness behind the ear, and whether the parts drop in.
- Wall: WALL (0.8 mm) everywhere, taken inward from the rounded outer surface.
- Split at the board plane (z = 0): a head-side TRAY (holds the cell) and a lateral LID (covers the module and parts).
  The tray has a 0.4 mm lip, 0.6 mm tall, that the lid slips over (0.1 mm gap). Glue or tape for the test; no latch.
- Openings: speaker-wire exit at the top front, a mic hole over the mic's sound port, two holes for the charge contacts.
  Hole positions use the board's layout coordinates (x as drawn in KiCad). WHICH EAR that matches is not checked, and
  the mic-port offset assumes the datasheet's top view; treat all three as placeholders until a board exists.
NOT checked: print orientation, supports, light-tightness, sealing, snap or screw closure, magnet pocket.

    python3 pod_v3_shell.py  ->  pod_v3_shell_tray_R.stl, pod_v3_shell_lid_R.stl
"""
import os
import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

import pod_v3_styled as st

HERE, RES, lo, shape, WALL = st.HERE, st.RES, st.lo, st.shape, st.WALL
LIP_T, LIP_H, GAP = 0.4, 0.6, 0.1
ax = [lo[i] + RES * np.arange(shape[i]) for i in range(3)]
X, Y, Z = np.meshgrid(*ax, indexing="ij")
depth = ndimage.distance_transform_edt(st.mask) * RES          # distance in from the outer surface
wall = st.mask & (depth <= WALL)
lip = st.mask & (depth > WALL) & (depth <= WALL + LIP_T) & (Z >= 0) & (Z < LIP_H)
lip_room = st.mask & (depth > WALL - 1e-6) & (depth <= WALL + LIP_T + GAP) & (Z >= -1e-6) & (Z < LIP_H + GAP)


def hole(c, axis, r, span):
    """Boolean cylinder of radius r through point c along axis (0, 1, 2), limited to span = (lo, hi) on that axis."""
    o = [X, Y, Z]; a = o.pop(axis); cc = list(c); ca = cc.pop(axis)
    return ((o[0] - cc[0]) ** 2 + (o[1] - cc[1]) ** 2 <= r * r) & (a >= span[0]) & (a <= span[1])


HOLES = dict(
    wire=hole((2.2, 0, 1.3), 1, 0.65, (11.0, 30.0)),            # two speaker wires, 1.3 mm hole, out of the top end
    mic=hole((-2.72, -0.88, 0), 2, 0.4, (1.0, 30.0)),            # 0.8 mm, over the mic port, through the lateral face
    chg_p=hole((-1.3, 8.65, 0), 2, 0.7, (-30.0, -0.5)),          # 1.4 mm, charge contact P1, through the head-side face (clears the 1.0 mm plunger of the 2.0 mm-base spring pin; barrel stops 0.2 mm short of the wall)
    chg_n=hole((1.3, 8.65, 0), 2, 0.7, (-30.0, -0.5)),           # charge contact P2
)
cut = np.zeros_like(st.mask)
for h in HOLES.values():
    cut |= h
# Charge-contact land (2026-11-14, see LAND_* in pod_v3_styled.py): cut the head-side face flat around the two pins and
# thicken the wall inward there, so a flat cradle pad meets the pins square. Pin barrels end at z = -3.4; the thickening
# stops at LAND_INNER = -3.6.
in_land = (X >= st.LAND_X[0]) & (X <= st.LAND_X[1]) & (Y >= st.LAND_Y[0]) & (Y <= st.LAND_Y[1])
land_cut = in_land & (Z < st.LAND_Z)
land_add = in_land & st.mask & (Z >= st.LAND_Z) & (Z < st.LAND_INNER)
tray = ((wall & (Z < 0)) | lip | land_add) & ~cut & ~land_cut
lid = (wall & (Z >= 0)) & ~lip_room & ~cut


def mesh_of(m, name):
    vol = ndimage.gaussian_filter(m.astype(np.float32), 0.7)
    v, f, _, _ = measure.marching_cubes(vol, 0.5, spacing=(RES,) * 3)
    me = trimesh.Trimesh(v + lo, f, process=True)
    me = trimesh.smoothing.filter_taubin(me, lamb=0.5, nu=-0.53, iterations=12)
    parts = me.split(only_watertight=False)
    me = max(parts, key=lambda p: len(p.faces))
    for n in (60000, 90000, 120000):      # decimation sometimes tears thin walls: try a finer count, else keep the full mesh
        dec = me.simplify_quadric_decimation(face_count=n)
        if dec.is_watertight:
            me = dec
            break
    if not me.is_watertight:
        trimesh.repair.fill_holes(me)
    trimesh.repair.fix_normals(me)
    me.export(os.path.join(HERE, name))
    # Decimating the in-memory mesh can tear it; a re-loaded copy (vertices merged on load) decimates cleanly.
    # Keeps the print files small enough to e-mail (the lid was 13 MB at full resolution).
    re = trimesh.load(os.path.join(HERE, name))
    if len(re.faces) > 120000:
        dec = re.simplify_quadric_decimation(face_count=90000)
        if dec.is_watertight:
            trimesh.repair.fix_normals(dec)
            dec.export(os.path.join(HERE, name))
            me = dec
    print(f"{name}: size {me.extents.round(1).tolist()} mm, watertight {me.is_watertight}, pieces {len(parts)}, "
          f"volume {abs(me.volume):.0f} mm3, about {abs(me.volume) * 1.2 / 1000:.2f} g at 1.2 g/cm3")
    return me


t = mesh_of(tray, "pod_v3_shell_tray_R.stl")
l = mesh_of(lid, "pod_v3_shell_lid_R.stl")
cav = st.mask & (depth > WALL)
print("cavity volume cm3:", round(cav.sum() * RES ** 3 / 1000, 2))
for name, (x0, x1, y0, y1, z0, z1) in st.PARTS.items():      # does every part box sit inside the cavity?
    box = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1) & (Z >= z0) & (Z <= z1)
    out = box & ~cav
    # the lip intrudes into the cavity by LIP_T just above the board plane; report that separately
    hit_lip = (box & lip).sum() * RES ** 3
    print(f"  {name}: {out.sum() * RES ** 3:.2f} mm3 pokes into the wall, {hit_lip:.2f} mm3 collides with the lip")

# cross-section picture: tray (blue), lid (orange), part boxes (grey outlines)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axs = plt.subplots(1, 4, figsize=(15, 4.6))
for a_, (title, yv) in zip(axs[:3], (("through the cell and audio chip, y = -5", -5.0), ("through the mic hole, y = -0.9", -0.88), ("through the charge contacts, y = 8.65", 8.65))):
    j = int(round((yv - lo[1]) / RES))
    img = np.zeros(tray[:, j, :].T.shape + (3,)) + 1
    img[tray[:, j, :].T] = (0.2, 0.45, 0.8); img[lid[:, j, :].T] = (0.95, 0.6, 0.2)
    a_.imshow(img, origin="lower", extent=(ax[0][0], ax[0][-1], ax[2][0], ax[2][-1]))
    for name, (x0, x1, y0, y1, z0, z1) in st.PARTS.items():
        if y0 <= yv <= y1:
            a_.add_patch(plt.Rectangle((x0, z0), x1 - x0, z1 - z0, fill=False, ec="0.35", lw=1)); a_.text(x0 + 0.1, z0 + 0.1, name, fontsize=6)
    a_.set_title(title, fontsize=9); a_.set_xlabel("x (mm)"); a_.set_ylabel("z, lateral up (mm)"); a_.set_aspect("equal")
i = int(round((0 - lo[0]) / RES))
img = np.zeros(tray[i].T.shape + (3,)) + 1
img[tray[i].T] = (0.2, 0.45, 0.8); img[lid[i].T] = (0.95, 0.6, 0.2)
axs[3].imshow(img, origin="lower", extent=(ax[1][0], ax[1][-1], ax[2][0], ax[2][-1])); axs[3].set_aspect("equal")
axs[3].set_title("lengthwise, x = 0 (top of pod at right)", fontsize=9); axs[3].set_xlabel("y (mm)")
fig.suptitle("Haven v3 pod test-print shell: tray (blue, head side) and lid (orange). Grey = part envelopes. Not verified by a print.", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "pod_v3_shell_sections.png"), dpi=110)
