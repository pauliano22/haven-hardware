"""Extract right-ear crops, canal entrances and tragus heights from HUTUBS head meshes.

    python3 extract_ears.py "<...>/3D head meshes" <out dir> 48,81,30,3,12,57

HUTUBS (TU Berlin, CC BY 4.0): https://doi.org/10.14279/depositonce-8487. Meshes are PLY in
metres, head frame x anterior, y left, z up; the right ear is at -y. The scans close each ear
canal at its entrance, so the canal entrance E is taken as the deepest point of the cavum
concha: a lateral height map is ray-cast, pixels walled in on >= 13 of 16 directions within
15 mm (walls >= 5 mm higher) form basins, and E is the deepest pixel of the largest basin.
Tragus height = most lateral surface in a 4-14 mm strip anterior to E.
"""
import json
import os
import sys

import numpy as np
import trimesh
from scipy.ndimage import binary_opening, label, map_coordinates

RES = 0.5


def crop_right_ear(m):
    v = m.vertices
    rp = v[v[:, 1] < 0]
    lat = -rp[:, 1]
    far = rp[lat > np.percentile(lat, 99.0)]
    cx, cz = np.median(far[:, 0]), np.median(far[:, 2])
    keep = (v[:, 1] < -30) & (np.abs(v[:, 0] - (cx + 15)) < 55) & (np.abs(v[:, 2] - cz) < 55)
    fk = keep[m.faces].all(1)
    return m.submesh([np.where(fk)[0]], append=True), cx, cz


def height_map(sub, cx, cz):
    xs = np.arange(cx - 40, cx + 55, RES)
    zs = np.arange(cz - 50, cz + 45, RES)
    X, Z = np.meshgrid(xs, zs)
    o = np.stack([X.ravel(), np.full(X.size, -250.0), Z.ravel()], 1)
    d = np.tile([0, 1.0, 0], (X.size, 1))
    loc, ri, _ = sub.ray.intersects_location(o, d, multiple_hits=False)
    L = np.full(X.size, np.nan)
    L[ri] = -loc[:, 1]
    return X, Z, L.reshape(X.shape)


def enclosure(L):
    Lf = np.where(np.isfinite(L), L, np.nanmin(L))
    R, C = np.mgrid[0:L.shape[0], 0:L.shape[1]]
    enc = np.zeros(L.shape)
    for a in np.linspace(0, 2 * np.pi, 16, endpoint=False):
        mx = np.full(L.shape, -1e9)
        for r in np.arange(1, 15.5, 0.5) / RES:
            mx = np.maximum(mx, map_coordinates(Lf, [R + r * np.sin(a), C + r * np.cos(a)], order=1, mode="nearest"))
        enc += mx >= Lf + 5.0
    return enc


def main():
    src, out_dir, subs = sys.argv[1], sys.argv[2], [int(s) for s in sys.argv[3].split(",")]
    os.makedirs(out_dir, exist_ok=True)
    meta = {}
    for sid in subs:
        m = trimesh.load(os.path.join(src, f"pp{sid}_3DheadMesh.ply"), process=False)
        m.apply_scale(1000.0)
        sub, cx, cz = crop_right_ear(m)
        X, Z, L = height_map(sub, cx, cz)
        enc = enclosure(L)
        ok = binary_opening((enc >= 13) & np.isfinite(L), iterations=2)
        lab, n = label(ok)
        k = int(np.argmax([(lab == i).sum() for i in range(1, n + 1)])) + 1
        basin = lab == k
        i = np.unravel_index(np.argmin(np.where(basin, L, np.inf)), L.shape)
        E = [float(X[i]), float(-L[i]), float(Z[i])]
        t = (X > E[0] + 2) & (X < E[0] + 14) & (np.abs(Z - E[2]) < 7) & np.isfinite(L)
        meta[str(sid)] = dict(E=E, basin_area_mm2=float(basin.sum() * RES * RES), tragus_lateral=float(L[t].max()))
        sub.export(os.path.join(out_dir, f"ear_pp{sid}.ply"))
        np.savez(os.path.join(out_dir, f"hm_pp{sid}.npz"), X=X, Z=Z, L=L)
        print(sid, meta[str(sid)], flush=True)
    json.dump(meta, open(os.path.join(out_dir, "ears.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
