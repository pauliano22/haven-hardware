"""PNG previews: iso + section of the shells, and the seated bud in scanned ears.

    python3 render.py <ears dir>
Uses the poses saved in fit_results.json.
"""
import json
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import evaluate_fit as ev  # noqa: E402
import generate_v2_ergonomic_shell as gen  # noqa: E402

LIGHT = gen.unit([0.4, 0.5, 1.0])
PART_COLORS = dict(battery="#c9b458", driver="#555b66", pcb="#2f7a4a", bottom_parts="#3d3d3d",
                   module="#9aa3ad", mic="#b5651d", magnet="#888888")


def shade(mesh, color, alpha=1.0):
    n = mesh.face_normals
    k = 0.35 + 0.65 * np.clip(n @ LIGHT, 0, 1)
    base = np.array(matplotlib.colors.to_rgb(color))
    cols = np.clip(base[None, :] * k[:, None], 0, 1)
    return np.concatenate([cols, np.full((len(cols), 1), alpha)], 1)


def add(ax, mesh, color, alpha=1.0, lw=0.0, z=None):
    fc = shade(mesh, color, alpha)
    pc = Poly3DCollection(mesh.vertices[mesh.faces], facecolors=fc, edgecolors=fc, linewidths=lw)
    if z is not None:
        pc.set_zorder(z)
    ax.add_collection3d(pc)


def frame_axes(ax, pts, title, elev, azim):
    lo, hi = pts.min(0), pts.max(0)
    c, r = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim)
    ax.set_title(title, fontsize=10); ax.set_xlabel("anterior (mm)"); ax.set_ylabel("superior"); ax.set_zlabel("lateral")


def parts_meshes(mode):
    return {n: trimesh.load(os.path.join(HERE, f"parts_{mode}", f"{n}.stl")) for n in PART_COLORS}


def shell_path(tag):
    return os.path.join(HERE, "ref_block_bud_in_ear_frame.stl") if tag == "block_reference" else os.path.join(HERE, f"{tag}_shell.stl")


def iso(tag, title, mode):
    shell = trimesh.load(shell_path(tag))
    fig = plt.figure(figsize=(12, 6))
    for i, (elev, azim, ghost) in enumerate([(20, -60, False), (20, -60, True)]):
        ax = fig.add_subplot(1, 2, i + 1, projection="3d")
        if ghost:
            for n, m in parts_meshes(mode).items():
                add(ax, m, PART_COLORS[n])
            add(ax, shell, "#d9d2c5", 0.18)
        else:
            add(ax, shell, "#d9d2c5")
        frame_axes(ax, shell.vertices, title + (" (parts visible)" if ghost else ""), elev, azim)
    plt.tight_layout(); plt.savefig(os.path.join(HERE, f"preview_{tag}_iso.png"), dpi=110); plt.close()


def section(tag, mode):
    shell = trimesh.load(shell_path(tag))
    # plane through the canal axis and the superior direction
    n = gen.unit(np.cross(gen.N_IN, [0, 1, 0]))
    fig, ax = plt.subplots(figsize=(7, 7))
    sec = shell.section(plane_origin=[0, 0, 0], plane_normal=n)
    u = gen.unit(np.cross([0, 1, 0], n)); v = np.array([0, 1.0, 0])
    if sec is not None:
        for e in sec.discrete:
            ax.plot(e @ u, e @ v, "k-", lw=1.2)
    for name, m in parts_meshes(mode).items():
        s = m.section(plane_origin=[0, 0, 0], plane_normal=n)
        if s is not None:
            for e in s.discrete:
                ax.fill(e @ u, e @ v, color=PART_COLORS[name], alpha=0.8)
    a = np.array([-12, 8]); ax.plot([(gen.N_IN * t) @ u for t in a], [(gen.N_IN * t) @ v for t in a], "r--", lw=1, label="canal axis")
    ax.plot(0, 0, "r+", ms=12); ax.text(0.3, -0.8, "canal entrance", color="r", fontsize=8)
    ax.set_aspect("equal"); ax.legend(loc="lower right"); ax.set_title(f"{tag}: section through the canal axis")
    ax.set_xlabel("mm (along the section, outward = lateral-posterior)"); ax.set_ylabel("superior (mm)")
    plt.tight_layout(); plt.savefig(os.path.join(HERE, f"preview_{tag}_section.png"), dpi=110); plt.close()


def in_ear(ears_dir, results, tag, subjects):
    fig = plt.figure(figsize=(6 * len(subjects), 6.5))
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    shell = trimesh.load(shell_path(tag))
    for k, sid in enumerate(subjects):
        row = next(r for r in results[tag] if r["subject"] == sid)
        p = row["pose"]
        Pb, Rb = ev.pose_points(shell.vertices, p["roll"], p["tilt_a"], p["tilt_s"], p["insert"])
        Rh, E = ev.ear_to_head(meta[str(sid)]["E"])
        bud = trimesh.Trimesh(Pb @ Rh.T + E, shell.faces, process=False)
        ear = trimesh.load(os.path.join(ears_dir, f"ear_pp{sid}.ply"), process=False)
        keep = np.linalg.norm(ear.triangles_center - E, axis=1) < 32
        ear = ear.submesh([np.where(keep)[0]], append=True)
        ear = ear.simplify_quadric_decimation(face_count=min(14000, len(ear.faces)))
        ax = fig.add_subplot(1, len(subjects), k + 1, projection="3d")
        ax.computed_zorder = False
        add(ax, ear, "#e2b8a0", z=1)
        add(ax, bud, "#7fa7c9", z=2)
        lo, hi = E - 24, E + 24
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2]); ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=5, azim=-90)   # looking at the right ear from the side
        ax.set_axis_off()
        ax.set_title(f"HUTUBS pp{sid} (right ear)\nprotrusion past tragus {row['protrusion']:+.1f} mm, "
                     f"max skin compression {row['max_pen']:.1f} mm", fontsize=10)
    plt.tight_layout(); plt.savefig(os.path.join(HERE, f"preview_{tag}_in_ears.png"), dpi=100); plt.close()


if __name__ == "__main__":
    ears_dir = sys.argv[1]
    results = json.load(open(os.path.join(HERE, "fit_results.json")))
    subs = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [48, 3, 57]
    for mode in ("nestled", "stacked"):
        if not os.path.exists(os.path.join(HERE, f"v2_{mode}_shell.stl")):
            continue
        iso(f"v2_{mode}", f"v2 ergonomic shell ({mode} layout)", mode)
        iso(f"v2_{mode}_fin", f"v2 ergonomic shell ({mode}) with concha-lock fin", mode)
        section(f"v2_{mode}", mode)
    for tag in results:
        in_ear(ears_dir, results, tag, subs)
