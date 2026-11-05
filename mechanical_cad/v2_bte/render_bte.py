"""Render each subject's fitted BTE (in-ear unit + pod + cable) from outside, behind and below,
plus iso views of the shells with their parts. Uses fit_bte.json.

    python3 -I render_bte.py <ears_bte dir>
Ear/head scans: HUTUBS HRTF database, TU Berlin (Brinkmann et al. 2019), CC BY 4.0,
doi:10.14279/depositonce-8487. Any image showing them needs that attribution.
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ERGO = os.path.normpath(os.path.join(HERE, "..", "v2_ergonomic_shell"))
sys.path[:0] = [HERE, ERGO]
import evaluate_fit as ev  # noqa: E402
import render as rd  # noqa: E402
from fit_bte import pod_R  # noqa: E402

ATTR = "Head scan: HUTUBS HRTF database, TU Berlin (Brinkmann et al. 2019), CC BY 4.0, doi:10.14279/depositonce-8487"
VIEWS = (("outside", 0, -90), ("behind", 10, 180), ("below", -70, -120))
COLORS = dict(battery="#c9b458", driver="#555b66", pcb="#2f7a4a", bottom_parts="#3d3d3d", board="#2f7a4a",
              module="#9aa3ad", mic="#b5651d", pod_mic="#b5651d", magnet="#888888", cable_boot="#777777", pad1="#d4af37", pad2="#d4af37")


def head_meshes(row, geo, E):
    Rh, _ = ev.ear_to_head(E)
    p = row["inear"]["pose"]
    ine = trimesh.load(os.path.join(HERE, "bte_inear_A_R.stl"))
    Pb, _ = ev.pose_points(ine.vertices, p["roll"], p["tilt_a"], p["tilt_s"], p["insert"])
    ine = trimesh.Trimesh(Pb @ Rh.T + E, ine.faces, process=False)
    ps = row["pod"]
    pod = trimesh.load(os.path.join(HERE, "bte_pod_R.stl"))
    pod = trimesh.Trimesh(pod.vertices @ pod_R(ps["theta"], ps["yaw"]).T + ps["center"], pod.faces, process=False)
    return ine, pod


def sheet(ears_dir, meta, row, geo):
    sid = row["inear"]["subject"]
    E = np.asarray(meta[str(sid)]["E"], float)
    ear = trimesh.load(os.path.join(ears_dir, f"ear_pp{sid}.ply"), process=False)
    near = np.linalg.norm(ear.triangles_center - (E + [-15, 0, 8]), axis=1) < 62
    ear = ear.submesh([np.where(near)[0]], append=True).simplify_quadric_decimation(face_count=22000)
    ine, pod = head_meshes(row, geo, E)
    cable = np.asarray(row["cable"]["path"]) if row.get("cable") else None
    fig = plt.figure(figsize=(18, 6.4))
    for i, (name, elev, azim) in enumerate(VIEWS):
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        rd.add(ax, ear, "#e8c4ad")
        rd.add(ax, ine, "#f2f2f0")
        rd.add(ax, pod, "#f2f2f0")
        if cable is not None:
            ax.plot(cable[:, 0], cable[:, 1], cable[:, 2], color="#222222", lw=2.2, zorder=10)
        rd.frame_axes(ax, np.vstack([ine.vertices, pod.vertices, E[None] + [[-50, -25, -25], [15, 10, 40]]]), name, elev, azim)
        ax.set_xlabel("anterior (mm)"); ax.set_ylabel("left"); ax.set_zlabel("up")
    c = row.get("cable") or {}
    fig.suptitle(f"HUTUBS pp{sid}: in-ear max pen {row['inear']['max_pen']} mm, pod max pen {row['pod']['max_pen']} mm, "
                 f"cable {c.get('length_mm', '-')} mm (min clearance {c.get('min_clearance_mm', '-')} mm)", fontsize=11)
    fig.text(0.01, 0.01, ATTR, fontsize=7)
    path = os.path.join(HERE, f"preview_fit_pp{sid}.png")
    fig.savefig(path, dpi=90, bbox_inches="tight")
    plt.close(fig)
    return path


def iso():
    fig = plt.figure(figsize=(20, 6))
    for i, (tag, pdir) in enumerate((("bte_inear_A_R", "parts_inear_A"), ("bte_inear_B_R", "parts_inear_B"), ("bte_pod_R", "parts_pod"))):
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        shell = trimesh.load(os.path.join(HERE, f"{tag}.stl"))
        rd.add(ax, shell, "#f2f2f0", alpha=0.25)
        for f in sorted(os.listdir(os.path.join(HERE, pdir))):
            if f.endswith(".stl"):
                rd.add(ax, trimesh.load(os.path.join(HERE, pdir, f)), COLORS.get(f[:-4], "#999999"))
        rd.frame_axes(ax, shell.vertices, tag.replace("_R", " (right)"), 22, -60)
    path = os.path.join(HERE, "preview_shells_iso.png")
    fig.savefig(path, dpi=90, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    ears_dir = sys.argv[1]
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    geo = json.load(open(os.path.join(HERE, "geometry.json")))
    rows = json.load(open(os.path.join(HERE, "fit_bte.json")))
    print(iso())
    for row in rows:
        if row.get("pod"):
            print(sheet(ears_dir, meta, row, geo), flush=True)


if __name__ == "__main__":
    main()
