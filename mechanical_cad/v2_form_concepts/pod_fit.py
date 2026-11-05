"""Seat the behind-the-ear pod in the groove behind each scanned pinna.

Pod frame (concepts.pod_parts): X toward the pinna (anterior), Y along the pod (up), Z away from
the scalp (lateral). Head frame (HUTUBS crops): x anterior, y left (the right ear is at -y),
z up. For each tilt (about the lateral axis) and pod height above the canal entrance, the pod
starts 38 mm behind the canal entrance, is pushed medially onto the scalp until it compresses
skin by SKIN_GIVE, then slides forward (re-settling each step) until it meets the back of the
pinna: the groove seat is the last position before the pod would have to ride up onto the
pinna by more than RIDE_MM. Reported: max penetration, contact area, contact on the pod's
pinna-facing side, how much of the pod is hidden behind the pinna seen from the side, and
how far it sits from the scalp at its outer face.

    python3 pod_fit.py <ears dir>   -> fit_bte_pod.json
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "v2_ergonomic_shell")))
import evaluate_fit as ev  # noqa: E402

SKIN_GIVE = ev.SKIN_GIVE
RIDE_MM = 3.0
M0 = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float).T   # columns: pod X, Y, Z in head coords


def rot_lat(deg):
    """Rotation about the head's lateral axis (-y)."""
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    # rotation about -y: x' = c x - s z ... (right-handed about -y)
    return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])


def place(P_local, theta, center):
    R = rot_lat(theta) @ M0
    return P_local @ R.T + center, R


def max_pen(ear, H):
    return float(ev.signed_dist(ear, H).max())


def settle(ear, Pl, theta, x, z, y_out, y_in, iters=9):
    """Most medial lateral position (y) with max penetration <= SKIN_GIVE."""
    lo, hi = y_out, y_in          # lo: lateral (outside, -y), hi: medial
    H, _ = place(Pl, theta, np.array([x, lo, z]))
    if max_pen(ear, H) > SKIN_GIVE:
        return None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        H, _ = place(Pl, theta, np.array([x, mid, z]))
        if max_pen(ear, H) > SKIN_GIVE:
            hi = mid
        else:
            lo = mid
    return lo


def seat(ear, Pl, theta, E, dz):
    z = E[2] + dz
    y_out, y_in = E[1] - 45.0, E[1] + 30.0
    x0 = E[0] - 38.0
    y0 = settle(ear, Pl, theta, x0, z, y_out, y_in)
    if y0 is None:
        return None
    best = (x0, y0)
    for x in np.arange(x0 + 3.0, E[0] - 4.0, 3.0):
        y = settle(ear, Pl, theta, x, z, y_out, y_in)
        if y is None or y < y0 - RIDE_MM:     # riding up onto the pinna (more lateral)
            break
        best = (x, y)
    return best


def metrics(ear, P, w, theta, center, pinna_side_mask):
    H, R = place(P, theta, center)
    sd = ev.signed_dist(ear, H)
    contact = (sd > -ev.CONTACT_BAND) & (sd <= SKIN_GIVE + 0.3)
    # hidden behind the pinna, seen from the side: a lateral ray from the point hits the ear
    o = H.copy()
    d = np.tile([0, -1.0, 0], (len(o), 1))
    hit = np.zeros(len(o), bool)
    idx = ear.ray.intersects_any(o + d * 0.6, d)
    hit |= idx
    outer = P[:, 2] > P[:, 2].max() - 1.0
    return dict(max_pen=round(float(sd.max()), 2), contact_mm2=round(float(w[contact].sum()), 1),
                pinna_side_contact_mm2=round(float(w[contact & pinna_side_mask].sum()), 1),
                hidden_from_side_pct=round(100.0 * float(w[hit].sum() / w.sum()), 1),
                outer_face_lateral_of_E=round(float(-(H[outer, 1].mean() - center[1]) + (-(center[1] - (center[1])))), 1))


def main():
    ears_dir = sys.argv[1]
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    pod = trimesh.load(os.path.join(HERE, "bte_pod_shell.stl"))
    P, w = ev.surface_samples(pod, 600)
    pinna_side = P[:, 0] > P[:, 0].max() - 2.5
    rows = []
    for sid in [int(k) for k in meta]:
        E = np.asarray(meta[str(sid)]["E"], float)
        ear = trimesh.load(os.path.join(ears_dir, f"ear_pp{sid}.ply"), process=False)
        near = np.linalg.norm(ear.triangles_center - E, axis=1) < 62
        ear = ear.submesh([np.where(near)[0]], append=True)
        if len(ear.faces) > 40000:
            ear = ear.simplify_quadric_decimation(face_count=40000)
        best = None
        for theta in (-20, 0, 20):
            for dz in (4.0, 12.0, 20.0, 28.0):
                s = seat(ear, P, theta, E, dz)
                if s is None:
                    continue
                c = np.array([s[0], s[1], E[2] + dz])
                m = metrics(ear, P, w, theta, c, pinna_side)
                key = (m["pinna_side_contact_mm2"] > 10.0, m["contact_mm2"] + 0.5 * m["hidden_from_side_pct"])
                if best is None or key > best[0]:
                    best = (key, theta, dz, c, m)
        if best is None:
            rows.append(dict(subject=sid, seated=False))
            print(sid, "no seat", flush=True)
            continue
        _, theta, dz, c, m = best
        lat_scalp = float(E[1] - c[1])   # pod centre lateral of the canal-entrance plane (mm, + = lateral)
        rows.append(dict(subject=sid, seated=True, theta=theta, height_above_E=dz,
                         center_head=c.round(2).tolist(), behind_E_mm=round(float(E[0] - c[0]), 1),
                         center_lateral_of_E=round(lat_scalp, 1), **{k: v for k, v in m.items() if k != "outer_face_lateral_of_E"}))
        print(sid, rows[-1], flush=True)
    json.dump(rows, open(os.path.join(HERE, "fit_bte_pod.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
