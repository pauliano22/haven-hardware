"""Score one concept shell in the six HUTUBS ears with ../v2_ergonomic_shell/evaluate_fit.py's
pose search and metrics (same SKIN_GIVE, contact band, canal exclusion, gravity moment).
The ear crop radius is a parameter so long stems are checked against the lobe and cheek too.

    python3 run_fit.py <ears dir> <tag> [crop_radius_mm]
writes fit_<tag>.json
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "v2_ergonomic_shell")))
import evaluate_fit as ev  # noqa: E402
import generate_v2_ergonomic_shell as gen  # noqa: E402


def evaluate(shell_path, com_bud, mass_g, ears_dir, subjects, crop=35.0, n_pts=2200):
    mesh = trimesh.load(shell_path)
    P, w = ev.surface_samples(mesh, n_pts)
    excl = ev.in_canal(P)
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    rows = []
    for sid in subjects:
        m = meta[str(sid)]
        ear = trimesh.load(os.path.join(ears_dir, f"ear_pp{sid}.ply"), process=False)
        Rh, E = ev.ear_to_head(m["E"])
        near = np.linalg.norm(ear.triangles_center - E, axis=1) < crop
        ear = ear.submesh([np.where(near)[0]], append=True)
        s, pose = ev.search(ear, Rh, E, P, w, excl)
        _, Rb = ev.pose_points(P[:1], *pose)
        com = Rb @ np.asarray(com_bud) + gen.N_IN * pose[3]
        axis_off = float(np.linalg.norm(com - (com @ gen.N_IN) * gen.N_IN))
        F = np.array([0, -mass_g * ev.G, 0])
        M = float(np.linalg.norm(np.cross(com, F)))
        tragus_rel = m["tragus_lateral"] - (-m["E"][1])
        Pb, _ = ev.pose_points(mesh.vertices, *pose)
        rows.append(dict(subject=sid, pose=dict(roll=pose[0], tilt_a=pose[1], tilt_s=pose[2], insert=pose[3]),
                         max_pen=round(s["max_pen"], 2), pen_area_mm2=round(s["pen_area"], 1),
                         contact_mm2=round(s["contact"], 1), height_above_E=round(s["maxZ"], 1),
                         tragus_above_E=round(tragus_rel, 1), protrusion=round(s["maxZ"] - tragus_rel, 1),
                         lowest_below_E=round(float(-Pb[:, 1].min()), 1),
                         com_axis_offset=round(axis_off, 2), moment_Nmm=round(M, 3)))
        print(tag, rows[-1], flush=True)
    return rows


if __name__ == "__main__":
    ears_dir, tag = sys.argv[1], sys.argv[2]
    crop = float(sys.argv[3]) if len(sys.argv) > 3 else 35.0
    geo = json.load(open(os.path.join(HERE, "geometry.json")))[tag]
    subjects = [int(k) for k in json.load(open(os.path.join(ears_dir, "ears.json")))]
    rows = evaluate(os.path.join(HERE, f"{tag}_shell.stl"), geo["com"], geo["mass_g"], ears_dir, subjects, crop)
    json.dump(rows, open(os.path.join(HERE, f"fit_{tag}.json"), "w"), indent=1)
