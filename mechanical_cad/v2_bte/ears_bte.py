"""Right-ear crops with enough scalp behind the pinna to seat a behind-the-ear pod.

Same canal-entrance (E) and tragus detection as ../v2_ergonomic_shell/extract_ears.py, but the
exported crop keeps 80 mm behind and 70 mm in front of the ear's lateral peak, +-65 mm
vertically, and everything lateral of y = -25 mm (head frame: x anterior, y left, z up; the right
ear is at -y). HUTUBS (TU Berlin, CC BY 4.0): https://doi.org/10.14279/depositonce-8487.

    python3 -I ears_bte.py "<...>/3D head meshes" <out dir> 48,81,30,3,12,57
"""
import json
import os
import sys

import numpy as np
import trimesh
from scipy.ndimage import binary_opening, label

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "v2_ergonomic_shell")))
import extract_ears as xe  # noqa: E402


def main():
    src, out_dir, subs = sys.argv[1], sys.argv[2], [int(s) for s in sys.argv[3].split(",")]
    os.makedirs(out_dir, exist_ok=True)
    meta = {}
    for sid in subs:
        m = trimesh.load(os.path.join(src, f"pp{sid}_3DheadMesh.ply"), process=False)
        m.apply_scale(1000.0)
        sub, cx, cz = xe.crop_right_ear(m)
        X, Z, L = xe.height_map(sub, cx, cz)
        enc = xe.enclosure(L)
        ok = binary_opening((enc >= 13) & np.isfinite(L), iterations=2)
        lab, n = label(ok)
        k = int(np.argmax([(lab == i).sum() for i in range(1, n + 1)])) + 1
        basin = lab == k
        i = np.unravel_index(np.argmin(np.where(basin, L, np.inf)), L.shape)
        E = [float(X[i]), float(-L[i]), float(Z[i])]
        t = (X > E[0] + 2) & (X < E[0] + 14) & (np.abs(Z - E[2]) < 7) & np.isfinite(L)
        v = m.vertices
        keep = (v[:, 1] < -25) & (v[:, 0] > cx - 80) & (v[:, 0] < cx + 70) & (np.abs(v[:, 2] - cz) < 65)
        big = m.submesh([np.where(keep[m.faces].all(1))[0]], append=True)
        big.export(os.path.join(out_dir, f"ear_pp{sid}.ply"))
        meta[str(sid)] = dict(E=E, basin_area_mm2=float(basin.sum() * xe.RES * xe.RES),
                              tragus_lateral=float(L[t].max()), crop_faces=int(len(big.faces)))
        print(sid, meta[str(sid)], flush=True)
    json.dump(meta, open(os.path.join(out_dir, "ears.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
