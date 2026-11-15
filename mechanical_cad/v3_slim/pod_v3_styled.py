"""Haven v3 slim pod: a STYLED outer shape (2026-11-11). A smooth convex "pebble" drawn around the same parts as
pod_v3.py concept A (17 mm cell, 0.8 mm board), instead of the generator's shrink-wrap.

How: the outer surface is the convex hull of small spheres placed at the corners of every part, so every flat face
of a part has at least WALL + CLR of cover and every corner at least WALL. Because the module side is narrower than
the cell side, the hull slopes into a dome on the lateral face and stays flat on the head side. Two larger spheres
round off the ends. This is the OUTER FORM ONLY (solid mesh for looking at and for size); the printable hollow shell
with cable hole, mic hole and charge contacts still has to be made from it.

    python3 pod_v3_styled.py  ->  pod_v3_styled_R.stl, prints size and the cover check
"""
import os
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
WALL, CLR = 0.8, 0.25
R = 1.32                      # corner sphere radius
D = R - (WALL + CLR)          # sphere centres sit this far inside each part corner
# parts as boxes (x0, x1, y0, y1, z0, z1): x toward the pinna, y up, z lateral. Board centre = origin.
# Cell: 3.5 x 8 x 20 mm pouch (TinyCircuits ASR00072 class; size from a search extract, NOT yet confirmed) + 0.3 swell.
# It is narrower than the board, and the module is narrower still, so the section is widest at the board and narrows
# toward both faces: an oval for free. The board's four corners are cut back (0.8 x 2.5 mm) so the ends can round.
PARTS = dict(
    pcb=(-4.8, 4.8, -11.0, 11.0, -0.4, 0.4),
    pcb_ends=(-4.0, 4.0, -13.5, 13.5, -0.4, 0.4),
    module=(-3.9, 3.9, 1.1, 13.5, 0.4, 2.25),
    top_parts=(-4.2, 4.2, -12.5, 0.8, 0.4, 1.4),
    cell=(-4.0, 4.0, -13.5, 6.5, -4.3, -0.5),
    back_strip=(-4.0, 4.0, 6.5, 9.7, -1.4, -0.4),
    magnet=(-1.5, 1.5, -15.9, -13.9, -3.0, 0.0),
)
# Charge-contact land (2026-11-14, for the charging cradle): the head-side face is curved where the two spring pins
# come out (it slopes about 25 degrees there), so a flat cradle pad would hit the shell before it reached the pins.
# The shell is cut flat at z = LAND_Z over this box, and thickened inward there to keep 0.8 mm of wall. The 4.5 mm pin's
# free tip is at z = -0.4 - 4.5 = -4.9, so it stands 0.5 mm proud of the land; the cradle pad pushes it in 0.5 mm.
# Used by pod_v3_shell.py and cradle_v3.py; the outer form above (this file's mesh) is NOT changed by it.
LAND_X, LAND_Y, LAND_Z, LAND_INNER = (-2.7, 2.7), (6.6, 10.6), -4.4, -3.6
PIN_FREE_TIP_Z = -0.4 - 4.5

ico = trimesh.creation.icosphere(subdivisions=3, radius=1.0).vertices
pts = []
for x0, x1, y0, y1, z0, z1 in PARTS.values():
    for cx in (x0 + D, x1 - D):
        for cy in (y0 + D, y1 - D):
            for cz in (z0 + D, z1 - D):
                pts.append(ico * R + [cx, cy, cz])
# end caps: one rounded nose at each end, inside the footprint so they add length only
for c, r in (([0, -13.6, -1.7], 3.6), ([0, 12.4, 0.7], 2.9)):
    pts.append(ico * r + c)
hull = trimesh.convex.convex_hull(np.vstack(pts))

# The hull is a prism with flat chamfers. Round it: on a 0.1 mm voxel grid, grow it by GROW, then "open" it with a
# ball of radius ROUND (shrink by ROUND, grow by ROUND). Opening turns every convex edge into a ROUND-radius curve and
# removes very little at shallow edges. GROW is raised until every part still has WALL of cover.
from scipy import ndimage
from skimage import measure
RES, ROUND, PAD = 0.1, 3.0, 2.0
lo = hull.bounds[0] - PAD
shape = np.ceil((hull.bounds[1] + PAD - lo) / RES).astype(int)
G = np.stack(np.meshgrid(*[lo[i] + RES * np.arange(shape[i]) for i in range(3)], indexing="ij"), -1).reshape(-1, 3)
A_, b_ = hull.facets_normal if False else hull.face_normals, None
inside = np.ones(len(G), bool)
planes = np.unique(np.round(np.c_[hull.face_normals, (hull.face_normals * hull.triangles[:, 0]).sum(1)], 4), axis=0)
sd = np.full(len(G), -1e9)
for n0, n1, n2, d0 in planes:                       # signed distance to a convex solid = max over its face planes (exact outside near faces)
    sd = np.maximum(sd, G @ np.array([n0, n1, n2]) - d0)
sd = sd.reshape(shape)


def part_cover(mask):
    dist_in = ndimage.distance_transform_edt(mask) * RES
    out = {}
    for name, (x0, x1, y0, y1, z0, z1) in PARTS.items():
        box = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0]); box.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
        P = np.vstack([box.sample(3000), box.vertices])
        idx = np.clip(np.round((P - lo) / RES).astype(int), 0, shape - 1)
        out[name] = round(float(dist_in[idx[:, 0], idx[:, 1], idx[:, 2]].min()), 2)
    return out


for GROW in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8):
    solid = sd <= GROW
    core = ndimage.distance_transform_edt(solid) * RES > ROUND
    mask = ndimage.distance_transform_edt(~core) * RES <= ROUND
    worst = part_cover(mask)
    if min(worst.values()) >= WALL - RES:
        break
vol = ndimage.gaussian_filter(mask.astype(np.float32), 1.0)
v, f, _, _ = measure.marching_cubes(vol, 0.5, spacing=(RES,) * 3)
mesh = trimesh.Trimesh(v + lo, f, process=True)
mesh = trimesh.smoothing.filter_taubin(mesh, lamb=0.5, nu=-0.53, iterations=60)    # removes the voxel steps without shrinking
mesh = mesh.simplify_quadric_decimation(face_count=40000)
trimesh.repair.fix_normals(mesh)
mesh.export(os.path.join(HERE, "pod_v3_styled_R.stl"))
print("rounding radius", ROUND, "mm; grown by", GROW, "mm to keep the cover")
print("size (width, length, thickness):", mesh.extents.round(1).tolist(), " volume cm3:", round(abs(mesh.volume) / 1000, 2))
print("thinnest cover over each part (mm, 0.1 mm grid):", worst)
