"""Swappable soft comfort sleeves for the in-ear unit (S / M / L).

S is the bare reshaped shell. M and L are silicone sleeves (Shore ~30-40A, or flexible resin for a
test print) that slip over the concha part of the body: everything medial of a plane just inside
the faceplate, minus the nozzle (the ear tip goes there) and a clearance ring around its base. The
faceplate (mic hole, cable boot) stays bare. The sleeve is a uniform offset of the shell's outer
surface, so it fills a larger concha more and puts soft material, not resin, on the skin.

    python3 sleeves.py            -> sleeve_{M,L}_{R,L}.stl, sleeves.json
    python3 sleeves.py --fit <ears_bte dir>   (also scores shell+sleeve on the six HUTUBS ears)
"""
import json
import os
import sys

import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "v2_form_concepts"), os.path.join(HERE, "..", "v2_ergonomic_shell")]
import bte  # noqa: E402
import concepts as cc  # noqa: E402

SIZES = {"M": 0.8, "L": 1.5}
VOX = 0.08
FACEPLATE_MARGIN = 1.2     # sleeve stops this far inside the board plane (toward the ear)
NOZZLE_RING = 4.6          # no sleeve within this radius of the nozzle axis near its base
NOZZLE_RING_DEPTH = 2.0    # ...for this far out of the nozzle base


def region_sd(P, info):
    """Signed distance-like field, < 0 where a sleeve may be: medial of the faceplate plane and
    outside a ring around the nozzle base."""
    plane = P @ cc.OUT - info["s_face"]
    rel = P - info["nozzle_B"]
    ax = rel @ cc.OUT
    rad = np.linalg.norm(rel - np.outer(ax, cc.OUT), axis=1)
    ring = np.minimum(NOZZLE_RING - rad, NOZZLE_RING_DEPTH - ax)       # > 0 inside the excluded ring
    return np.maximum(plane, ring)


def build():
    shell = trimesh.load(os.path.join(HERE, "bte_inear_A_R.stl"))
    parts, kw, _ = bte.inear_parts("A")
    board = next(p for p in parts if p.name == "board")
    info = dict(s_face=float(board.c @ cc.OUT) - FACEPLATE_MARGIN, nozzle_B=np.asarray(kw["nozzle_B"], float))
    tmax = max(SIZES.values())
    lo = shell.bounds[0] - tmax - 1.0
    vg = shell.voxelized(VOX).fill()
    inside = vg.matrix
    origin = vg.transform[:3, 3]
    pad = int(np.ceil((tmax + 1.0) / VOX))
    inside = np.pad(inside, pad)
    origin = origin - pad * VOX
    dist_out = ndimage.distance_transform_edt(~inside) * VOX            # mm from the shell, outside
    sd = ndimage.gaussian_filter(dist_out - ndimage.distance_transform_edt(inside) * VOX, 1.0)   # smooth signed distance
    idx = np.indices(inside.shape).reshape(3, -1).T
    P = origin + idx * VOX
    reg = region_sd(P, info).reshape(inside.shape)
    allowed = reg < 0
    out = {}
    for name, t in SIZES.items():
        # field < 0 inside the sleeve: outside the shell, within t of it, in the allowed region
        f = np.maximum(np.maximum(sd - t, 0.02 - sd), reg)            # shell offset band, trimmed smoothly
        v, fa, _, _ = measure.marching_cubes(f, 0.0, spacing=(VOX, VOX, VOX))
        m = trimesh.Trimesh(v + origin, fa, process=True)
        if m.volume < 0:
            m.invert()
        comps = m.split(only_watertight=False)
        m = max(comps, key=lambda q: len(q.faces))
        for n in (60000, 90000, 120000):
            d = m.simplify_quadric_decimation(face_count=n)
            d.merge_vertices(); trimesh.repair.fill_holes(d)
            if d.is_watertight:
                m = d
                break
        m.export(os.path.join(HERE, f"sleeve_{name}_R.stl"))
        bte.mirror_x(m).export(os.path.join(HERE, f"sleeve_{name}_L.stl"))
        out[name] = dict(thickness_mm=t, watertight=bool(m.is_watertight), volume_mm3=round(float(m.volume), 1),
                         mass_g_silicone=round(float(m.volume) * 1.1e-3, 3), bbox_mm=m.extents.round(2).tolist(),
                         dropped_pieces=len(comps) - 1)
        # combined outer surface (shell + this sleeve) for the fit check
        comb = (inside | ((dist_out <= t) & allowed)).astype(np.float32)
        v, fa, _, _ = measure.marching_cubes(ndimage.gaussian_filter(comb, 0.8), 0.5, spacing=(VOX, VOX, VOX))
        c = trimesh.Trimesh(v + origin, fa, process=True)
        if c.volume < 0:
            c.invert()
        c = max(c.split(only_watertight=False), key=lambda q: len(q.faces))
        c.export(os.path.join(HERE, f"_comb_{name}.stl"))
        print(name, out[name], flush=True)
    return shell, out


def fit(shell, out, ears_dir):
    import run_fit as rf
    geo = json.load(open(os.path.join(HERE, "geometry.json")))["inear_A"]
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    subs = [int(k) for k in meta]
    for name in SIZES:
        path = os.path.join(HERE, f"_comb_{name}.stl")
        rf.tag = f"inear_A+sleeve_{name}"
        rows = rf.evaluate(path, geo["com"], geo["mass_g"] + out[name]["mass_g_silicone"], ears_dir, subs, crop=35.0)
        out[name]["fit"] = {r["subject"]: dict(max_press_mm=r["max_pen"], area_over_1mm_mm2=r["pen_area_mm2"],
                                               contact_mm2=r["contact_mm2"]) for r in rows}
    for name in SIZES:
        os.remove(os.path.join(HERE, f"_comb_{name}.stl"))


def main():
    shell, out = build()
    if "--fit" in sys.argv:
        fit(shell, out, sys.argv[sys.argv.index("--fit") + 1])
    json.dump(out, open(os.path.join(HERE, "sleeves.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
