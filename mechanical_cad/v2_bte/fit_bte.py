"""Fit the BTE in-ear unit, pod and cable on the six HUTUBS subjects (large crops from ears_bte.py).

In-ear unit: ../v2_form_concepts/run_fit.py pose search (same metrics as every earlier study;
rigid skin, 0.5 mm give, canal excluded). Pod: starts 45 mm behind the canal entrance, and at
each step forward is placed against the scalp from the inside out (the first non-penetrating
lateral position, so it can never "land" on the pinna's lateral face), until the groove gets too
tight; tilt about the lateral axis, yaw about vertical and height are searched. Cable: a
polyline from the in-ear unit's boot to the pod's boot through an apex above the helix root,
relaxed so every point keeps >= 1.0 mm from skin, smoothed; the shortest valid route wins.

    python3 -I fit_bte.py <ears_bte dir>   -> fit_bte.json
Head frame: x anterior, y left (right ear at -y), z up, mm.
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
FORM = os.path.normpath(os.path.join(HERE, "..", "v2_form_concepts"))
ERGO = os.path.normpath(os.path.join(HERE, "..", "v2_ergonomic_shell"))
sys.path[:0] = [FORM, ERGO]
import evaluate_fit as ev  # noqa: E402
import run_fit as rf  # noqa: E402

GIVE = ev.SKIN_GIVE
CABLE_CLR = 1.0
R_POD0 = np.stack([[1, 0, 0], [0, 0, 1], [0, -1, 0]], 1).astype(float)   # columns: pod X, Y, Z in head coords


def rot(axis, deg):
    return trimesh.transformations.rotation_matrix(np.radians(deg), axis)[:3, :3]


def pod_R(theta, yaw):
    return rot([0, 0, 1], yaw) @ rot([0, -1, 0], theta) @ R_POD0


def pen(ear, H):
    return float(ev.signed_dist(ear, H).max())


def place_y(ear, P, R, x, z, y_in, y_out):
    """First lateral (more negative y) position where the pod no longer penetrates beyond GIVE,
    scanning out from inside the head."""
    prev = y_in
    for y in np.arange(y_in, y_out, -2.0):
        if pen(ear, P @ R.T + [x, y, z]) <= GIVE:
            lo, hi = y, prev           # lo feasible, hi infeasible
            for _ in range(5):
                mid = 0.5 * (lo + hi)
                if pen(ear, P @ R.T + [x, mid, z]) <= GIVE:
                    lo = mid
                else:
                    hi = mid
            return lo
        prev = y
    return None


def seat_pod(ear, P, w, E):
    best = None
    for theta in (-20, -10, 0, 10):
        for yaw in (0, -20, -35):
            R = pod_R(theta, yaw)
            for dz in (6.0, 14.0, 22.0):
                z = E[2] + dz
                last = None
                for x in np.arange(E[0] - 45.0, E[0] - 8.0, 3.0):
                    y = place_y(ear, P, R, x, z, E[1] + 18.0, E[1] - 40.0)
                    if y is None:
                        break
                    if last is not None and y < last[1] - 3.0:      # had to move out a lot: groove too tight
                        break
                    last = (x, y)
                if last is None:
                    continue
                c = np.array([last[0], last[1], z])
                H = P @ R.T + c
                sd = ev.signed_dist(ear, H)
                contact = float(w[(sd > -ev.CONTACT_BAND) & (sd <= GIVE + 0.3)].sum())
                hid = ear.ray.intersects_any(H + [0, -0.6, 0], np.tile([0, -1.0, 0], (len(H), 1)))
                hidden = float(100 * w[hid].sum() / w.sum())
                key = contact + 3.0 * hidden
                if best is None or key > best[0]:
                    best = (key, dict(theta=theta, yaw=yaw, dz=dz, center=c.round(2).tolist(), max_pen=round(float(sd.max()), 2),
                                      contact_mm2=round(contact, 1), hidden_from_side_pct=round(hidden, 1),
                                      behind_E_mm=round(float(E[0] - c[0]), 1)))
    return best[1] if best else None


def relax(ear, pts, iters=40):
    pts = pts.copy()
    for _ in range(iters):
        cp, d, tid = trimesh.proximity.closest_point(ear, pts)
        n = ear.face_normals[tid]
        s = np.sign(np.einsum("ij,ij->i", pts - cp, n))
        clr = s * d                                      # + outside
        bad = clr < CABLE_CLR + 0.05
        bad[0] = bad[-1] = False
        pts[bad] = cp[bad] + n[bad] * (CABLE_CLR + 0.1)
        sm = pts.copy()
        sm[1:-1] = 0.5 * pts[1:-1] + 0.25 * (pts[:-2] + pts[2:])
        pts[1:-1] = sm[1:-1]
    cp, d, tid = trimesh.proximity.closest_point(ear, pts)
    s = np.sign(np.einsum("ij,ij->i", pts - cp, ear.face_normals[tid]))
    return pts, s * d


def route_cable(ear, P0, P1, E):
    best = None
    for dx in (-14.0, -8.0, -2.0):
        for dz in (26.0, 32.0, 38.0):
            A = np.array([E[0] + dx, E[1] - 6.0, E[2] + dz])
            n = 70
            t = np.linspace(0, 1, n)[:, None]
            k = n // 2
            pts = np.vstack([P0 + (A - P0) * np.linspace(0, 1, k)[:, None], A + (P1 - A) * np.linspace(0, 1, n - k + 1)[1:, None]])
            pts, clr = relax(ear, pts)
            ok = clr[3:-3].min() >= CABLE_CLR - 0.05
            L = float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())
            if ok and (best is None or L < best[0]):
                best = (L, pts, float(clr[3:-3].min()), A)
    if best is None:
        return None
    L, pts, cmin, A = best
    return dict(length_mm=round(L, 1), min_clearance_mm=round(cmin, 2), top_above_E_mm=round(float(pts[:, 2].max() - E[2]), 1),
                path=pts.round(2).tolist())


def main():
    ears_dir = sys.argv[1]
    geo = json.load(open(os.path.join(HERE, "geometry.json")))
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    subs = [int(k) for k in meta]
    rf.tag = "inear_B"
    rows_b = rf.evaluate(os.path.join(HERE, "bte_inear_B_R.stl"), geo["inear_B"]["com"], geo["inear_B"]["mass_g"], ears_dir, subs, crop=35.0)
    rf.tag = "inear_A"
    rows = rf.evaluate(os.path.join(HERE, "bte_inear_A_R.stl"), geo["inear_A"]["com"], geo["inear_A"]["mass_g"], ears_dir, subs, crop=35.0)
    pod = trimesh.load(os.path.join(HERE, "bte_pod_R.stl"))
    P, w = ev.surface_samples(pod, 450)
    out = []
    for row in rows:
        sid = row["subject"]
        E = np.asarray(meta[str(sid)]["E"], float)
        ear = trimesh.load(os.path.join(ears_dir, f"ear_pp{sid}.ply"), process=False)
        if len(ear.faces) > 45000:
            ear = ear.simplify_quadric_decimation(face_count=45000)
        Rh, _ = ev.ear_to_head(E)
        p = row["pose"]
        ex, _ = ev.pose_points(np.array([geo["inear_A"]["cable_exit"]]), p["roll"], p["tilt_a"], p["tilt_s"], p["insert"])
        P0 = ex[0] @ Rh.T + E
        ps = seat_pod(ear, P, w, E)
        rec = dict(inear=row, inear_B=next(r for r in rows_b if r["subject"] == sid), pod=ps)
        if ps:
            R = pod_R(ps["theta"], ps["yaw"])
            P1 = np.asarray(geo["pod"]["cable_entry"]) @ R.T + np.asarray(ps["center"])
            rec["cable"] = route_cable(ear, P0, P1, E)
        print(sid, json.dumps({k: (v if k != "cable" else {kk: vv for kk, vv in (v or {}).items() if kk != "path"}) for k, v in rec.items()}), flush=True)
        out.append(rec)
    json.dump(out, open(os.path.join(HERE, "fit_bte.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
