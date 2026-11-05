"""Export one HUTUBS ear (CC BY 4.0) with the seated v2 shell as a GLB for the 3D explorer.

    python3 export_explorer.py <ears dir> <subject> <shell tag> <out.glb>
Units: mm, ear frame (X anterior, Y superior, Z lateral, origin = canal entrance).
Attribution required wherever this is shown: "Ear scan: HUTUBS HRTF database, TU Berlin
(Brinkmann et al. 2019), CC BY 4.0, doi:10.14279/depositonce-8487. Cropped and decimated."
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import evaluate_fit as ev  # noqa: E402


def main():
    ears_dir, sid, tag, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))[str(sid)]
    res = next(r for r in json.load(open(os.path.join(HERE, "fit_results.json")))[tag] if r["subject"] == sid)
    Rh, E = ev.ear_to_head(meta["E"])
    ear = trimesh.load(os.path.join(ears_dir, f"ear_pp{sid}.ply"), process=False)
    keep = np.linalg.norm(ear.triangles_center - E, axis=1) < 40
    ear = ear.submesh([np.where(keep)[0]], append=True)
    ear.vertices = (ear.vertices - E) @ Rh          # head -> ear frame
    if len(ear.faces) > 110000:
        ear = ear.simplify_quadric_decimation(face_count=110000)
    shell = trimesh.load(os.path.join(HERE, f"{tag}_shell.stl"))
    p = res["pose"]
    Pb, _ = ev.pose_points(shell.vertices, p["roll"], p["tilt_a"], p["tilt_s"], p["insert"])
    shell = trimesh.Trimesh(Pb, shell.faces, process=False).simplify_quadric_decimation(face_count=30000)
    ear.visual = trimesh.visual.ColorVisuals(ear, face_colors=[226, 184, 160, 255])
    shell.visual = trimesh.visual.ColorVisuals(shell, face_colors=[242, 242, 238, 255])
    scene = trimesh.Scene()
    scene.add_geometry(ear, node_name="ear_HUTUBS_pp%d_CC-BY-4.0" % sid)
    scene.add_geometry(shell, node_name=f"{tag}_shell")
    scene.metadata["attribution"] = ("Ear scan: HUTUBS HRTF database, TU Berlin (Brinkmann et al. 2019), "
                                     "CC BY 4.0, doi:10.14279/depositonce-8487. Cropped and decimated.")
    scene.export(out)
    print("wrote", out, "faces", len(ear.faces) + len(shell.faces), "pose", p)


if __name__ == "__main__":
    main()
