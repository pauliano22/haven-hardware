"""Renders (iso, section, seated in three ears) and explorer exports (GLB + part positions in
ear pp3) for the form concepts, using the poses in fit_<tag>.json / fit_bte_pod.json.

    python3 render_export.py <ears dir> <export dir>
Ear scans: HUTUBS HRTF database, TU Berlin (Brinkmann et al. 2019), CC BY 4.0,
doi:10.14279/depositonce-8487. Any image or model showing them needs that attribution.
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
sys.path.insert(0, ERGO)
sys.path.insert(0, HERE)
import evaluate_fit as ev  # noqa: E402
import generate_v2_ergonomic_shell as gen  # noqa: E402
import render as rd  # noqa: E402
import pod_fit as pf  # noqa: E402

ATTR = ("Ear scan: HUTUBS HRTF database, TU Berlin (Brinkmann et al. 2019), CC BY 4.0, "
        "doi:10.14279/depositonce-8487. Cropped and decimated.")
COLORS = dict(battery="#c9b458", driver="#555b66", pcb="#2f7a4a", pmic_parts="#3d3d3d", bottom_parts="#3d3d3d",
              codec_pcb="#2f7a4a", codec_parts="#3d3d3d", module="#9aa3ad", mic="#b5651d", magnet="#888888",
              flex="#c48a2c", cable_boss="#777777", pad1="#d4af37", pad2="#d4af37")
TITLES = dict(stem_cyl="Stem (cylindrical cell in the stem)", stem_head_cell="Stem (CP1254 kept in the head)",
              bean_wing="Bean + wing (nestled)", bte_inear="Behind-the-ear: in-ear unit", bte_pod="Behind-the-ear: pod")
EAR_SUBJECTS = [48, 3, 57]


EXTERNAL = dict(bean_wing=dict(shell=os.path.join(ERGO, "v2_nestled_fin_shell.stl"), parts=os.path.join(ERGO, "parts_nestled"),
                               fit=("v2_nestled_fin", os.path.join(ERGO, "fit_results.json"))))


def shell_file(tag):
    return EXTERNAL[tag]["shell"] if tag in EXTERNAL else os.path.join(HERE, f"{tag}_shell.stl")


def parts_dir(tag):
    return EXTERNAL[tag]["parts"] if tag in EXTERNAL else os.path.join(HERE, f"parts_{tag}")


def part_descs(tag):
    p = os.path.join(parts_dir(tag), "parts.json")
    if os.path.exists(p):
        return json.load(open(p))
    out = []
    for name, m in load_parts(tag).items():
        obb = m.bounding_box_oriented
        T = obb.primitive.transform
        out.append(dict(name=name, kind="obb", center=T[:3, 3].round(3).tolist(), size=np.round(obb.primitive.extents, 3).tolist(),
                        axes=T[:3, :3].T.round(4).tolist()))
    return out


def load_parts(tag):
    d = parts_dir(tag)
    return {f[:-4]: trimesh.load(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".stl")}


def posed(mesh, pose):
    Pb, Rb = ev.pose_points(mesh.vertices, pose["roll"], pose["tilt_a"], pose["tilt_s"], pose["insert"])
    return trimesh.Trimesh(Pb, mesh.faces, process=False), Rb


def iso(tag):
    shell = trimesh.load(shell_file(tag))
    parts = load_parts(tag)
    fig = plt.figure(figsize=(12, 6))
    for i, ghost in enumerate((False, True)):
        ax = fig.add_subplot(1, 2, i + 1, projection="3d")
        if ghost:
            for n, m in parts.items():
                rd.add(ax, m, COLORS.get(n, "#999999"))
            rd.add(ax, shell, "#d9d2c5", 0.18)
        else:
            rd.add(ax, shell, "#d9d2c5")
        rd.frame_axes(ax, shell.vertices, TITLES.get(tag, tag) + (" (parts visible)" if ghost else ""), 20, -60)
    plt.tight_layout(); plt.savefig(os.path.join(HERE, f"preview_{tag}_iso.png"), dpi=105); plt.close()


def section(tag, normal=None):
    shell = trimesh.load(shell_file(tag))
    parts = load_parts(tag)
    n = gen.unit(np.cross(gen.N_IN, [0, 1, 0])) if normal is None else gen.unit(normal)
    u = gen.unit(np.cross([0, 1, 0], n)); v = np.array([0, 1.0, 0])
    fig, ax = plt.subplots(figsize=(7, 8))
    sec = shell.section(plane_origin=[0, 0, 0], plane_normal=n)
    if sec is not None:
        for e in sec.discrete:
            ax.plot(e @ u, e @ v, "k-", lw=1.2)
    for name, m in parts.items():
        s = m.section(plane_origin=[0, 0, 0], plane_normal=n)
        if s is not None:
            for e in s.discrete:
                ax.fill(e @ u, e @ v, color=COLORS.get(name, "#999"), alpha=0.8)
    a = np.array([-12, 8])
    ax.plot([(gen.N_IN * t) @ u for t in a], [(gen.N_IN * t) @ v for t in a], "r--", lw=1, label="canal axis")
    ax.plot(0, 0, "r+", ms=12)
    ax.set_aspect("equal"); ax.legend(loc="lower right"); ax.set_title(f"{TITLES.get(tag, tag)}: section through the canal axis")
    ax.set_xlabel("mm"); ax.set_ylabel("superior (mm)")
    plt.tight_layout(); plt.savefig(os.path.join(HERE, f"preview_{tag}_section.png"), dpi=105); plt.close()


def in_ears(ears_dir, tag, rows, pod_rows=None, span=24):
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    shell = trimesh.load(shell_file(tag))
    pod = trimesh.load(os.path.join(HERE, "bte_pod_shell.stl")) if pod_rows else None
    fig = plt.figure(figsize=(6 * len(EAR_SUBJECTS), 6.6))
    for k, sid in enumerate(EAR_SUBJECTS):
        row = next(r for r in rows if r["subject"] == sid)
        Rh, E = ev.ear_to_head(meta[str(sid)]["E"])
        bud, _ = posed(shell, row["pose"])
        bud = trimesh.Trimesh(bud.vertices @ Rh.T + E, bud.faces, process=False)
        ear = trimesh.load(os.path.join(ears_dir, f"ear_pp{sid}.ply"), process=False)
        keep = np.linalg.norm(ear.triangles_center - E, axis=1) < span * 1.6
        ear = ear.submesh([np.where(keep)[0]], append=True).simplify_quadric_decimation(face_count=16000)
        ax = fig.add_subplot(1, len(EAR_SUBJECTS), k + 1, projection="3d")
        ax.computed_zorder = False
        rd.add(ax, ear, "#e2b8a0", z=1)
        rd.add(ax, bud, "#7fa7c9", z=2)
        title = f"HUTUBS pp{sid} (right ear)\nprotrusion past tragus {row['protrusion']:+.1f} mm, max compression {row['max_pen']:.1f} mm"
        if pod_rows:
            pr = next(r for r in pod_rows if r["subject"] == sid)
            if pr.get("seated"):
                H, _ = pf.place(pod.vertices, pr["theta"], np.array(pr["center_head"]))
                rd.add(ax, trimesh.Trimesh(H, pod.faces, process=False), "#7fa7c9", z=0)
                title += f"\npod {pr['hidden_from_side_pct']:.0f}% hidden behind the ear"
        lo, hi = E - span, E + span
        if pod_rows:
            lo = lo - np.array([14, 0, 0]); hi = hi + np.array([0, 0, 10])
        r = (hi - lo).max() / 2; c = (hi + lo) / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=5, azim=-90); ax.set_axis_off()
        ax.set_title(title, fontsize=9)
    fig.text(0.5, 0.01, ATTR, ha="center", fontsize=7)
    plt.tight_layout(rect=(0, 0.03, 1, 1)); plt.savefig(os.path.join(HERE, f"preview_{tag}_in_ears.png"), dpi=95); plt.close()


def xform_desc(desc, R, t):
    out = dict(desc)
    for key in ("center", "base"):
        if key in desc:
            out[key] = (R @ np.asarray(desc[key]) + t).round(3).tolist()
    if "axis" in desc:
        out["axis"] = (R @ np.asarray(desc["axis"])).round(4).tolist()
    if "axes" in desc:
        out["axes"] = [(R @ np.asarray(a)).round(4).tolist() for a in desc["axes"]]
    return out


def export(ears_dir, out_dir, tag, row, pod_row=None, sid=3):
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))[str(sid)]
    Rh, E = ev.ear_to_head(meta["E"])
    ear = trimesh.load(os.path.join(ears_dir, f"ear_pp{sid}.ply"), process=False)
    rad = 52 if pod_row else 40
    keep = np.linalg.norm(ear.triangles_center - E, axis=1) < rad
    ear = ear.submesh([np.where(keep)[0]], append=True)
    ear.vertices = (ear.vertices - E) @ Rh
    ear = ear.simplify_quadric_decimation(face_count=42000)
    scene = trimesh.Scene()
    ear.visual = trimesh.visual.ColorVisuals(ear, face_colors=[226, 184, 160, 255])
    scene.add_geometry(ear, node_name=f"ear_HUTUBS_pp{sid}_CC-BY-4.0")
    shell = trimesh.load(shell_file(tag))
    sp, Rb = posed(shell, row["pose"])
    t = gen.N_IN * row["pose"]["insert"]
    sp = sp.simplify_quadric_decimation(face_count=12000)
    sp.visual = trimesh.visual.ColorVisuals(sp, face_colors=[242, 242, 238, 255])
    scene.add_geometry(sp, node_name=f"{tag}_shell")
    descs = []
    pj = part_descs(tag)
    for name, m in load_parts(tag).items():
        pm, _ = posed(m, row["pose"])
        col = (np.array(matplotlib.colors.to_rgb(COLORS.get(name, "#999999"))) * 255).astype(int).tolist() + [255]
        pm.visual = trimesh.visual.ColorVisuals(pm, face_colors=col)
        scene.add_geometry(pm, node_name=f"part_{name}")
    descs = [xform_desc(d, Rb, t) for d in pj]
    out = dict(concept=tag, frame="ear frame of HUTUBS pp3: origin = canal entrance, X anterior, Y superior, Z lateral, mm",
               pose=row["pose"], shell=f"{tag}_shell", parts=descs, attribution=ATTR)
    if pod_row and pod_row.get("seated"):
        pod = trimesh.load(os.path.join(HERE, "bte_pod_shell.stl"))
        H, Rp = pf.place(pod.vertices, pod_row["theta"], np.array(pod_row["center_head"]))
        pm = trimesh.Trimesh((H - E) @ Rh, pod.faces, process=False).simplify_quadric_decimation(face_count=9000)
        pm.visual = trimesh.visual.ColorVisuals(pm, face_colors=[242, 242, 238, 255])
        scene.add_geometry(pm, node_name="bte_pod_shell")
        Rpe = Rh.T @ Rp
        tpe = (np.array(pod_row["center_head"]) - E) @ Rh
        for name, m in load_parts("bte_pod").items():
            Hm, _ = pf.place(m.vertices, pod_row["theta"], np.array(pod_row["center_head"]))
            mm = trimesh.Trimesh((Hm - E) @ Rh, m.faces, process=False)
            col = (np.array(matplotlib.colors.to_rgb(COLORS.get(name, "#999999"))) * 255).astype(int).tolist() + [255]
            mm.visual = trimesh.visual.ColorVisuals(mm, face_colors=col)
            scene.add_geometry(mm, node_name=f"pod_part_{name}")
        out["pod"] = dict(shell="bte_pod_shell", theta=pod_row["theta"],
                          parts=[xform_desc(d, Rpe, tpe) for d in json.load(open(os.path.join(HERE, "parts_bte_pod", "parts.json")))])
    scene.metadata["attribution"] = ATTR
    gp = os.path.join(out_dir, f"haven_concept_{tag}_pp{sid}.glb")
    scene.export(gp)
    json.dump(out, open(os.path.join(out_dir, f"haven_concept_{tag}_pp{sid}.json"), "w"), indent=1)
    print(tag, "glb", round(os.path.getsize(gp) / 1e6, 2), "MB", flush=True)


def main():
    ears_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    pod_rows = json.load(open(os.path.join(HERE, "fit_bte_pod.json")))
    for tag in ("stem_cyl", "stem_head_cell", "bte_inear", "bte_pod"):
        iso(tag)
    for tag in ("stem_cyl", "stem_head_cell", "bte_inear"):
        section(tag)
    for tag in ("stem_cyl", "stem_head_cell", "bte_inear", "bean_wing"):
        if tag in EXTERNAL:
            name, path = EXTERNAL[tag]["fit"]
            rows = json.load(open(path))[name]
        else:
            rows = json.load(open(os.path.join(HERE, f"fit_{tag}.json")))
        is_bte = tag == "bte_inear"
        if tag not in EXTERNAL:
            in_ears(ears_dir, tag, rows, pod_rows if is_bte else None, span=30 if tag.startswith("stem") else 24)
        row3 = next(r for r in rows if r["subject"] == 3)
        pr3 = next((r for r in pod_rows if r["subject"] == 3), None) if is_bte else None
        export(ears_dir, out_dir, tag, row3, pr3)


if __name__ == "__main__":
    main()
