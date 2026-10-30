"""Map the rev_b_fit_study block bud (MDBT53V, 8 mm driver) into this folder's ear frame so
evaluate_fit.py can score it the same way: nozzle base -> B, nozzle axis -> canal axis."""
import importlib.util
import json
import math
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_v2_ergonomic_shell as gen  # noqa: E402

FS = os.path.join(HERE, "..", "rev_b_fit_study")
spec = importlib.util.spec_from_file_location("fitstudy", os.path.join(FS, "generate_rev_b_fit_study.py"))
fs = importlib.util.module_from_spec(spec)
sys.path.insert(0, FS)
spec.loader.exec_module(fs)


def align(a, b):
    a, b = gen.unit(a), gen.unit(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)


def main():
    parts, fr = fs.layout("mdbt53v")
    zs = [p[1][0] for p in parts.values()] + [p[1][1] for p in parts.values()]
    zbot = min(zs) - fs.CLR - fs.Z_EXTRA - fs.WALL
    t = math.radians(fs.NOZZLE_TILT)
    axis_old = np.array([0, math.sin(t), -math.cos(t)])
    base_old = np.array([0, fr["spk_y"], zbot])
    R = align(axis_old, gen.N_IN)
    B = -gen.N_IN * gen.NOZ_BASE_OUT
    m = trimesh.load(os.path.join(FS, "bud_mdbt53v.stl"))
    m.vertices = (m.vertices - base_old) @ R.T + B
    out = os.path.join(HERE, "ref_block_bud_in_ear_frame.stl")
    m.export(out)
    names = dict(speaker="driver")
    items = [(m.volume * gen.RESIN_DENSITY, m.center_mass)]
    for name, (solid, _, _) in parts.items():
        c = (np.array(solid.Center().toTuple()) - base_old) @ R.T + B
        items.append((gen.MASS[names.get(name, name)], c))
    items.append((gen.MASS["tip"], B + gen.N_IN * (4.0)))
    M = sum(x for x, _ in items)
    com = sum(x * c for x, c in items) / M
    json.dump(dict(stl=out, com=com.tolist(), mass_g=M, bbox=m.extents.tolist()), open(os.path.join(HERE, "ref_block.json"), "w"), indent=1)
    print("block ref", round(M, 2), "g; com", com.round(2), "extents", m.extents.round(2))


if __name__ == "__main__":
    main()
