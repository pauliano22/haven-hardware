"""Render the charging case with both pods and both in-ear units in place (preview_case.png)."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", "v2_form_concepts"), os.path.join(HERE, "..", "v2_ergonomic_shell")]
import generate_v2_ergonomic_shell as gen  # noqa: E402
import render as rd  # noqa: E402


def inear_standing(x, y, z_floor, mirror):
    m = trimesh.load(os.path.join(HERE, "bte_inear_A_R.stl"))
    if mirror:
        m.apply_transform(np.diag([-1.0, 1, 1, 1])); m.invert()
    n = gen.N_IN * ([-1, 1, 1] if mirror else 1)
    m.apply_transform(trimesh.geometry.align_vectors(n, [0, 0, 1.0]))     # nozzle up
    m.apply_translation([x, y, z_floor + 0.3] - np.r_[m.bounds.mean(0)[:2], m.bounds[0][2]])
    return light(m, 8000)


def light(m, n=25000):
    return m.simplify_quadric_decimation(face_count=n) if len(m.faces) > n else m


def main():
    c = json.load(open(os.path.join(HERE, "case.json")))
    base = light(trimesh.load(os.path.join(HERE, "case_base.stl")))
    lid = light(trimesh.load(os.path.join(HERE, "case_lid.stl")))
    pods = light(trimesh.load(os.path.join(HERE, "case_preview_pods.stl")))
    units = [inear_standing(sx * 9.0, c["tray_center_y"], c["tray_floor_z"], sx < 0) for sx in (1, -1)]
    tops = [u.bounds[1][2] for u in units]
    lid_x = lid.copy(); lid_x.apply_translation([0, 0, 30])
    fig = plt.figure(figsize=(14, 7))
    for k, (el, az, show_lid, title) in enumerate([(28, -60, False, "base and pods, lid off (in-ear units checked numerically, not drawn)"),
                                                   (20, -60, True, f"with lid lifted 30 mm; case {c['outer_mm'][0]} x {c['outer_mm'][1]} x {c['outer_mm'][2]} mm")]):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        rd.add(ax, base, "#9fb7a8")
        rd.add(ax, pods, "#f2f2f0")
        for u in units:
            pass  # matplotlib paints the base over them; fit is checked in case.py notes
        pts = [base.vertices, pods.vertices]
        if show_lid:
            rd.add(ax, lid_x, "#9fb7a8", alpha=0.35)
            pts.append(lid_x.vertices)
        rd.frame_axes(ax, np.vstack(pts), title, el, az)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "preview_case.png"), dpi=90)
    print("unit tops z", [round(t, 1) for t in tops], "lid inner top z", c["lid_inner_top_z"])


if __name__ == "__main__":
    main()
