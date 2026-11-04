"""Route the BTE cable for every subject in fit_bte.json and write the result back.

From the in-ear unit's boot exit to the pod's boot entry, over an apex placed 4 mm out from the
skin above the helix root (found by casting a ray medially at each candidate x, z). The polyline
is relaxed so every interior point keeps >= 1.0 mm from skin, then smoothed; repeated until it
settles. The shortest route meeting the clearance wins; if none does, the best one is kept and
flagged.

    python3 -I cable_route.py <ears_bte dir>
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ERGO = os.path.normpath(os.path.join(HERE, "..", "v2_ergonomic_shell"))
sys.path[:0] = [HERE, ERGO]
import evaluate_fit as ev  # noqa: E402
from fit_bte import pod_R  # noqa: E402

CLR = 1.0


def clearance(ear, pts):
    cp, d, tid = trimesh.proximity.closest_point(ear, pts)
    n = ear.face_normals[tid]
    s = np.sign(np.einsum("ij,ij->i", pts - cp, n))
    return s * d, cp, n


def relax(ear, pts, iters=80):
    pts = pts.copy()
    for _ in range(iters):
        c, cp, n = clearance(ear, pts)
        bad = c < CLR + 0.15
        bad[:2] = bad[-2:] = False
        pts[bad] = cp[bad] + n[bad] * (CLR + 0.25)
        pts[1:-1] = 0.5 * pts[1:-1] + 0.25 * (pts[:-2] + pts[2:])
    c, _, _ = clearance(ear, pts)
    return pts, c


def skin_lateral(ear, x, z):
    o = np.array([[x, -160.0, z]])
    loc, _, _ = ear.ray.intersects_location(o, np.array([[0, 1.0, 0]]))
    return float(loc[:, 1].min()) if len(loc) else None


def route(ear, P0, P1, E):
    best = None
    for dx in (-16.0, -11.0, -6.0, -1.0):
        for dz in (24.0, 30.0, 36.0):
            y = skin_lateral(ear, E[0] + dx, E[2] + dz)
            if y is None:
                continue
            A = np.array([E[0] + dx, y - 4.0, E[2] + dz])
            n1, n2 = 45, 45
            pts = np.vstack([P0 + (A - P0) * np.linspace(0, 1, n1)[:, None], A + (P1 - A) * np.linspace(0, 1, n2)[1:, None]])
            pts, c = relax(ear, pts)
            cmin = float(c[3:-3].min())
            L = float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())
            key = (cmin >= CLR - 0.05, -L if cmin >= CLR - 0.05 else cmin)
            if best is None or key > best[0]:
                best = (key, L, cmin, pts)
    _, L, cmin, pts = best
    return dict(length_mm=round(L, 1), min_clearance_mm=round(cmin, 2), meets_1mm=bool(cmin >= CLR - 0.05),
                top_above_E_mm=round(float(pts[:, 2].max() - E[2]), 1), path=pts.round(2).tolist())


def main():
    ears_dir = sys.argv[1]
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    geo = json.load(open(os.path.join(HERE, "geometry.json")))
    rows = json.load(open(os.path.join(HERE, "fit_bte.json")))
    for row in rows:
        sid = row["inear"]["subject"]
        if not row.get("pod"):
            continue
        E = np.asarray(meta[str(sid)]["E"], float)
        ear = trimesh.load(os.path.join(ears_dir, f"ear_pp{sid}.ply"), process=False)
        if len(ear.faces) > 60000:
            ear = ear.simplify_quadric_decimation(face_count=60000)
        Rh, _ = ev.ear_to_head(E)
        p = row["inear"]["pose"]
        ex, _ = ev.pose_points(np.array([geo["inear_A"]["cable_exit"]]), p["roll"], p["tilt_a"], p["tilt_s"], p["insert"])
        P0 = ex[0] @ Rh.T + E
        ps = row["pod"]
        P1 = np.asarray(geo["pod"]["cable_entry"]) @ pod_R(ps["theta"], ps["yaw"]).T + np.asarray(ps["center"])
        row["cable"] = route(ear, P0, P1, E)
        print(sid, {k: v for k, v in row["cable"].items() if k != "path"}, flush=True)
    json.dump(rows, open(os.path.join(HERE, "fit_bte.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
