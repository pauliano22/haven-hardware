"""Concept colorways of the real v2 pod and in-ear shells (BioMed resin colors + silicone accent).

    python3 render_colorways.py      # writes preview_colorways.png (needs trimesh, numpy, matplotlib)
"""
import numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb

import os
D = os.path.dirname(os.path.abspath(__file__)) + "/"
pod = trimesh.load(D + "bte_pod_L.stl")
ear = trimesh.load(D + "bte_inear_A_L.stl")
slv = trimesh.load(D + "sleeve_M_L.stl")

def rot(elev, azim):
    a, e = np.radians(azim), np.radians(elev)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return Rx @ Rz

LIGHT = np.array([-0.4, 0.5, 0.8]); LIGHT /= np.linalg.norm(LIGHT)

def draw(ax, items, elev, azim, center, scale):
    R = rot(elev, azim)
    polys, cols, depth = [], [], []
    for mesh, color in items:
        v = (mesh.vertices - center) @ R.T
        f = mesh.faces
        n = mesh.face_normals @ R.T
        shade = np.clip(n @ LIGHT, 0, 1) * 0.65 + 0.35
        facing = n[:, 2] > -0.05
        base = np.array(to_rgb(color))
        for i in np.nonzero(facing)[0]:
            pass
        idx = np.nonzero(facing)[0]
        tri = v[f[idx]]
        polys.append(tri[:, :, :2]); depth.append(tri[:, :, 2].mean(axis=1))
        cols.append(np.clip(base[None, :] * shade[idx, None], 0, 1))
    polys = np.concatenate(polys); cols = np.concatenate(cols); depth = np.concatenate(depth)
    order = np.argsort(depth)
    pc = PolyCollection(polys[order], facecolors=cols[order], edgecolors=cols[order], linewidths=0.15)
    ax.add_collection(pc)
    ax.set_xlim(-scale, scale); ax.set_ylim(-scale, scale); ax.set_aspect("equal"); ax.axis("off")

ways = [
    ("Clear resin\nhoney silicone", "#cfdbe0", "#e8b04a", "BioMed Clear"),
    ("White resin\nevergreen silicone", "#efede6", "#2f6b4c", "BioMed White"),
    ("Black resin\nsand silicone", "#2a2d30", "#cdb98f", "BioMed Black"),
]
fig, axes = plt.subplots(2, 3, figsize=(13, 8.4), facecolor="#f4f6f1")
pc_ = pod.bounds.mean(axis=0); ec_ = ear.bounds.mean(axis=0)
for j, (title, shell, accent, mat) in enumerate(ways):
    draw(axes[0, j], [(pod, shell)], 12, -60, pc_, 22)
    draw(axes[1, j], [(ear, shell), (slv, accent)], 12, -60, ec_, 14)
    axes[0, j].set_title(title + "\n(" + mat + ")", fontsize=12, color="#16231c", family="serif")
axes[0, 0].text(-22, -21, "Pod (behind the ear)", fontsize=9, color="#4d5f54")
axes[1, 0].text(-14, -13.5, "In-ear unit with comfort sleeve", fontsize=9, color="#4d5f54")
fig.text(0.5, 0.01, "Concept render of the real v2 shell files. Colors approximate; clear resin shows its insides in real life.",
         ha="center", fontsize=9, color="#4d5f54")
plt.tight_layout(rect=(0, 0.03, 1, 1))
plt.savefig("preview_colorways.png", dpi=110, facecolor=fig.get_facecolor())
print("ok")
