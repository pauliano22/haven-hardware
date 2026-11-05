"""Seat a bud shell in scanned right ears and score the fit.

Ear data: HUTUBS head meshes (TU Berlin, CC BY 4.0, see README.md). Not stored in this repo;
download "3D head meshes.zip" from https://doi.org/10.14279/depositonce-8487 and run
`extract_ears.py <meshes dir> <out dir>` first. That writes, per subject, a right-ear crop
(mm, head frame: x anterior, y left, z up) and ears.json with the canal entrance E (deepest
point of the enclosed cavum concha; the scans close the canal there) and the tragus height.

Ear frame per subject: origin E, X = anterior (+x), Y = superior (+z), Z = lateral (-y).
The bud model uses the same frame, with its nozzle on the canal axis N_IN.

For each ear and shell the pose search varies roll about the canal axis, two tilts, and
insertion depth, and keeps the pose with the least tissue penetration (skin is allowed
SKIN_GIVE of compression), breaking ties by contact area. Points of the nozzle/tip inside
the canal are excluded (the scan's canal is a closed patch, not tissue).

    python3 evaluate_fit.py <ears dir> [shell.stl ...]
"""
import json
import math
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_v2_ergonomic_shell as gen  # noqa: E402

SKIN_GIVE = 0.5        # mm of soft-tissue compression treated as acceptable contact
CONTACT_BAND = 0.8     # mm: points this close to skin (outside) count as touching
G = 9.81e-3            # N per gram


def ear_to_head(E):
    ex, ey, ez = np.eye(3)
    R = np.stack([ex, ez, -ey], 1)   # columns: bud X, Y, Z in head coords
    return R, np.asarray(E, float)


def rot(axis, deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), axis)[:3, :3]


def surface_samples(mesh, n):
    pts, fid = trimesh.sample.sample_surface_even(mesh, n, seed=1)
    area = mesh.area / len(pts)
    return pts, np.full(len(pts), area)


def in_canal(p):
    ax = p @ gen.N_IN
    rad = np.linalg.norm(p - np.outer(ax, gen.N_IN), axis=1)
    return (ax > -0.5) & (rad < 4.6)


def signed_dist(ear, pts):
    """Positive = inside tissue (penetration depth)."""
    cp, d, tid = trimesh.proximity.closest_point(ear, pts)
    n = ear.face_normals[tid]
    s = np.sign(np.einsum("ij,ij->i", pts - cp, n))
    return -s * d


def pose_points(P, roll, tilt_a, tilt_s, ins):
    R = rot(gen.N_IN, roll)
    R = rot([1, 0, 0], tilt_s) @ rot([0, 1, 0], tilt_a) @ R
    return P @ R.T + gen.N_IN * ins, R


def score(ear, Rh, E, P, w, excl, pose):
    Pb, Rb = pose_points(P, *pose)
    H = Pb @ Rh.T + E
    sd = signed_dist(ear, H)
    sd[excl] = -9.0
    pen = np.clip(sd - SKIN_GIVE, 0, None)
    contact = w[(sd > -CONTACT_BAND) & (sd <= SKIN_GIVE + 0.3)].sum()
    return dict(cost=float((w * pen**2).sum()), max_pen=float(sd.max()), pen_area=float(w[sd > SKIN_GIVE + 0.5].sum()),
                contact=float(contact), maxZ=float(Pb[:, 2].max())), Rb


def search(ear, Rh, E, P, w, excl):
    best = None
    grid = [(r, ta, ts, i) for r in range(-60, 61, 15) for ta in (-10, 0, 10) for ts in (-10, 0, 10) for i in (0.0, 1.5)]
    def better(a, b):
        if b is None:
            return True
        if abs(a["cost"] - b["cost"]) > 0.5:
            return a["cost"] < b["cost"]
        return a["contact"] > b["contact"]
    for pose in grid:
        s, _ = score(ear, Rh, E, P, w, excl, pose)
        if better(s, best and best[0]):
            best = (s, pose)
    # local refinement
    s0, p0 = best
    for dr in (-7, 0, 7):
        for dta in (-5, 0, 5):
            for dts in (-5, 0, 5):
                for di in (-0.75, 0, 0.75):
                    pose = (p0[0] + dr, p0[1] + dta, p0[2] + dts, p0[3] + di)
                    s, _ = score(ear, Rh, E, P, w, excl, pose)
                    if better(s, best[0]):
                        best = (s, pose)
    return best


def evaluate(shell_path, com_bud, mass_g, ears_dir, subjects, n_pts=1800):
    mesh = trimesh.load(shell_path)
    P, w = surface_samples(mesh, n_pts)
    excl = in_canal(P)
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    rows = []
    for sid in subjects:
        m = meta[str(sid)]
        ear = trimesh.load(os.path.join(ears_dir, f"ear_pp{sid}.ply"), process=False)
        Rh, E = ear_to_head(m["E"])
        near = np.linalg.norm(ear.triangles_center - E, axis=1) < 35
        ear = ear.submesh([np.where(near)[0]], append=True)
        s, pose = search(ear, Rh, E, P, w, excl)
        _, Rb = pose_points(P[:1], *pose)
        com = Rb @ np.asarray(com_bud) + gen.N_IN * pose[3]
        axis_off = float(np.linalg.norm(com - (com @ gen.N_IN) * gen.N_IN))
        # moment of gravity (head upright: -Y) about the canal entrance
        F = np.array([0, -mass_g * G, 0])
        M = float(np.linalg.norm(np.cross(com, F)))
        tragus_rel = m["tragus_lateral"] - (-m["E"][1])
        rows.append(dict(subject=sid, pose=dict(roll=pose[0], tilt_a=pose[1], tilt_s=pose[2], insert=pose[3]),
                         max_pen=round(s["max_pen"], 2), pen_area_mm2=round(s["pen_area"], 1),
                         contact_mm2=round(s["contact"], 1), height_above_E=round(s["maxZ"], 1),
                         tragus_above_E=round(tragus_rel, 1), protrusion=round(s["maxZ"] - tragus_rel, 1),
                         com_axis_offset=round(axis_off, 2), moment_Nmm=round(M, 3)))
        print(shell_path.split('/')[-1], rows[-1], flush=True)
    return rows


if __name__ == "__main__":
    # evaluate_fit.py <ears dir> [job name ...]: with names, only those jobs run and their rows
    # are merged into the existing fit_results.json instead of replacing it.
    ears_dir, only = sys.argv[1], set(sys.argv[2:])
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    subjects = [int(k) for k in meta]
    jobs = json.load(open(os.path.join(HERE, "fit_jobs.json")))
    res_p = os.path.join(HERE, "fit_results.json")
    out = json.load(open(res_p)) if only and os.path.exists(res_p) else {}
    for job in jobs:
        if only and job["name"] not in only:
            continue
        out[job["name"]] = evaluate(job["stl"], job["com"], job["mass_g"], ears_dir, subjects)
    json.dump(out, open(res_p, "w"), indent=1)
