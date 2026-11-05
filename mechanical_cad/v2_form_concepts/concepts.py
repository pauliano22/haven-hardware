"""Haven v2 form-factor concepts: stem, bean + wing, behind-the-ear (receiver in canal).

Same frame, rules and shell construction as ../v2_ergonomic_shell (origin = canal entrance E,
X anterior, Y superior, Z lateral; nozzle on the canal axis gen.N_IN; parts' signed distance
fields offset by clearance + wall, morphologically closed, smoothed, hollowed to a uniform
wall; nozzle, bore, mic port and charging-pad holes as exact CSG; marching cubes).

Concepts. Paul's parts are fixed (CP1254-or-better battery life, 8 mm 16-32 ohm driver,
MDBT53V-1M, ADAU1860, SPH0641, nozzle.py nozzle, 2 charging pads + magnet); only the shape
changes:
  stem_cyl       : stem concept. A stem needs a cylindrical cell: GP Batteries GP1018L10
                   (dia 10.5 x 18 mm with sleeve, 100 mAh min / 105 typ, more than the CP1254's
                   60-77 mAh). Head = 8 mm driver + the v2 board (module outward) + mic; stem =
                   cell, with pads + magnet at the tip.
  stem_head_cell : AirPods-Pro-style split with the CP1254 kept in the head. Head = driver +
                   CP1254 + codec board + mic; stem = module + PMIC board, antenna at the stem's
                   outer end, pads + magnet at the tip.
  bean / bean_wing: with CP1254 + 8 mm this is the ergonomic study's "nestled" layout (battery
                   beside the driver, board on top, optional wing); its shells and scores are
                   reused from ../v2_ergonomic_shell, not regenerated here.
  bte_inear + bte_pod: receiver-in-canal. In-ear unit = 8 mm driver + outer mic on a small
                   flex + cable boss. Behind-ear pod = CP1454 (85-120 mAh) + v2 board +
                   pads + magnet.

    python3 concepts.py [name ...]
"""
import json
import math
import os
import sys

import numpy as np
import trimesh
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import distance_transform_edt, gaussian_filter

HERE = os.path.dirname(os.path.abspath(__file__))
ERGO = os.path.normpath(os.path.join(HERE, "..", "v2_ergonomic_shell"))
sys.path.insert(0, ERGO)
import generate_v2_ergonomic_shell as gen  # noqa: E402
import nozzle as nz  # noqa: E402

N_IN = gen.N_IN
X_, Y_, Z_ = np.eye(3)
unit = gen.unit
WALL, CLR, GAP, RES = gen.WALL, gen.CLR, gen.GAP, gen.RES
RESIN = gen.RESIN_DENSITY

# part envelopes (mm) and masses (g)
CP1254 = (12.1, 5.4, 1.7)        # VARTA CoinPower CP1254, 60-77 mAh
CP1454 = (14.1, 5.4, 2.5)        # VARTA CoinPower CP1454, 85-120 mAh (mass estimated)
CYL_CELL = (10.5, 18.0, 3.5)    # GP Batteries GP1018L10, 100 mAh min (mass estimated)
DRV8 = (8.0, 3.6, 0.5)
MODULE = gen.MODULE              # 12.4 x 7.8 x 1.85, mass 0.4
MIC = gen.MIC
MAG = (3.0, 2.0, 0.11)
PAD_D, PAD_PITCH = gen.PAD_D, gen.PAD_PITCH
TIP_MASS = 0.10

# hear-through current (POWER_BUDGET.md): quiet ~3.5 mA, loud ~7.5 mA; 80 % usable
I_QUIET, I_LOUD, USABLE = 3.5, 7.5, 0.8


# ------------------------------------------------------------------ parts
def frame(long_axis, thin_hint):
    """Rotation whose columns are (width, long, thin) for a part lying along long_axis."""
    s = unit(long_axis)
    t = unit(np.asarray(thin_hint, float) - (np.asarray(thin_hint, float) @ s) * s)
    w = unit(np.cross(s, t))
    return np.stack([w, s, t], 1)


class Box:
    def __init__(self, name, c, size, R=np.eye(3), mass=0.0):
        self.name, self.c, self.size, self.R, self.mass = name, np.asarray(c, float), np.asarray(size, float), np.asarray(R, float), mass

    def sdf(self, P):
        q = np.abs((P - self.c) @ self.R) - self.size / 2
        return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(-1), 0)

    def mesh(self):
        T = np.eye(4); T[:3, :3] = self.R; T[:3, 3] = self.c
        return trimesh.creation.box(extents=self.size, transform=T)

    def center(self):
        return self.c

    def desc(self):
        return dict(name=self.name, kind="box", center=self.c.round(3).tolist(), size=self.size.round(3).tolist(),
                    axes=self.R.T.round(4).tolist(), mass_g=self.mass)


class Cyl:
    def __init__(self, name, base, axis, d, h, mass=0.0):
        self.name, self.base, self.axis, self.d, self.h, self.mass = name, np.asarray(base, float), unit(axis), d, h, mass

    def sdf(self, P):
        return gen.sd_cyl(P, self.base, self.axis, self.d / 2, self.h)

    def mesh(self):
        m = trimesh.creation.cylinder(radius=self.d / 2, height=self.h, sections=48)
        T = trimesh.geometry.align_vectors([0, 0, 1], self.axis)
        T[:3, 3] = self.center()
        m.apply_transform(T)
        return m

    def center(self):
        return self.base + self.axis * self.h / 2

    def desc(self):
        return dict(name=self.name, kind="cylinder", base=self.base.round(3).tolist(), axis=self.axis.round(4).tolist(),
                    diameter=self.d, height=self.h, center=self.center().round(3).tolist(), mass_g=self.mass)


def capsule_chain(P, pts, rads):
    d = np.full(P.shape[:-1], 1e9, np.float32)
    for (a, ra), (b, rb) in zip(zip(pts[:-1], rads[:-1]), zip(pts[1:], rads[1:])):
        a, b = np.asarray(a, float), np.asarray(b, float)
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        dist = np.linalg.norm(P - (a + t[..., None] * ab), axis=-1) - (ra + (rb - ra) * t)
        d = np.minimum(d, dist)
    return d


def min_gap(parts, skip=()):
    """Smallest distance between parts, from sampled surfaces (mm)."""
    meshes = {p.name: p.mesh() for p in parts}
    worst = (1e9, None)
    names = list(meshes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if frozenset((names[i], names[j])) in skip:
                continue
            pts = meshes[names[i]].sample(1500, seed=2) if hasattr(meshes[names[i]], "sample") else meshes[names[i]].vertices
            pts = np.vstack([pts, meshes[names[i]].vertices])
            inside = meshes[names[j]].contains(pts)
            if inside.any():
                return (-1.0, (names[i], names[j]))
            d = np.abs(trimesh.proximity.signed_distance(meshes[names[j]], pts)).min()
            if d < worst[0]:
                worst = (float(d), (names[i], names[j]))
    return worst


# ------------------------------------------------------------------ shell from parts
CLOSE_R = gen.CLOSE_R
SMOOTH = gen.SMOOTH
BUILD_MARGIN = gen.BUILD_MARGIN


def build_shell(parts, nozzle_B=None, fins=(), mic=None, pads=None, close_r=CLOSE_R, shift=0.0):
    meshes = [p.mesh() for p in parts]
    lo = np.min([m.bounds[0] for m in meshes], 0)
    hi = np.max([m.bounds[1] for m in meshes], 0)
    if nozzle_B is not None:
        tip = nozzle_B + N_IN * (nz.NOZZLE_LEN + 0.5)
        lo, hi = np.minimum(lo, tip), np.maximum(hi, tip)
    for pts, rads in fins:
        P_ = np.asarray(pts); r_ = max(rads)
        lo, hi = np.minimum(lo, P_.min(0) - r_), np.maximum(hi, P_.max(0) + r_)
    pad = CLR + WALL + close_r + 2.0
    lo, hi = lo - pad, hi + pad
    axes = [np.arange(l + shift, h + RES, RES) for l, h in zip(lo, hi)]
    G = np.stack(np.meshgrid(*axes, indexing="ij"), -1).astype(np.float32)
    D = None
    for p in parts:
        d = p.sdf(G).astype(np.float32)
        D = d if D is None else np.minimum(D, d)
    X0 = D <= CLR + WALL + BUILD_MARGIN
    if nozzle_B is not None:
        X0 |= gen.sd_cyl(G, nozzle_B - N_IN * 2.5, N_IN, nz.NOZZLE_OD / 2 + 0.6, 2.5) <= 0
    for pts, rads in fins:
        X0 |= capsule_chain(G, pts, rads) <= 0
    dil = distance_transform_edt(~X0) * RES <= close_r
    C = distance_transform_edt(dil) * RES > close_r
    C |= X0
    sd = ((distance_transform_edt(~C) - distance_transform_edt(C)) * RES).astype(np.float32)
    sd = gaussian_filter(sd, SMOOTH / RES)
    shell = np.maximum(sd, -(sd + WALL))
    if nozzle_B is not None:
        shell = np.minimum(shell, gen.nozzle_sdf(G, nozzle_B))
        bore0 = nozzle_B - N_IN * (gen.NOSE_WALL + gen.FRONT_GAP + 0.6)
        shell = np.maximum(shell, -gen.sd_cyl(G, bore0, N_IN, nz.BORE_D / 2, nz.NOZZLE_LEN + gen.NOSE_WALL + gen.FRONT_GAP + 1.5))
    if mic is not None:
        c, d = mic
        shell = np.maximum(shell, -gen.sd_cyl(G, c, d, 0.45, 12.0))
    pad_list = []
    if pads is not None:
        base, md, across = pads
        for sgn in (-1, 1):
            c0 = base + across * sgn * PAD_PITCH - md * 0.5
            shell = np.maximum(shell, -gen.sd_cyl(G, c0, md, PAD_D / 2, CLR + WALL + BUILD_MARGIN + 1.2))
            pad_list.append((c0, md))
    for ax in range(3):
        sl = [slice(None)] * 3
        for idx in (0, -1):
            sl[ax] = idx
            shell[tuple(sl)] = np.maximum(shell[tuple(sl)], RES)
    del G, D
    return dict(axes=axes, field=shell, body_sd=sd, pads=pad_list)


def shell_mesh(parts, **kw):
    for shift in (0.0, 0.07, 0.13):
        fd = build_shell(parts, shift=shift, **kw)
        mesh = gen.mesh_from_field(fd["field"], fd["axes"])
        if mesh.is_watertight:
            break
    return mesh, fd


def clearances(fd, parts):
    f = RegularGridInterpolator(fd["axes"], fd["body_sd"], bounds_error=False, fill_value=9.0)
    out = {}
    for p in parts:
        m = p.mesh()
        P = np.vstack([m.vertices, m.sample(2000, seed=3)])
        clr = -(f(P) + WALL)
        out[p.name] = dict(clearance=round(float(clr.min()), 3), ok=bool(clr.min() >= gen.CHECK_CLR - 0.05))
    return out


def mass_props(mesh, parts, tip=True):
    items = [(mesh.volume * RESIN, mesh.center_mass)]
    items += [(p.mass, p.center()) for p in parts if p.mass > 0]
    if tip:
        items.append((TIP_MASS, -N_IN * gen.NOZ_BASE_OUT + N_IN * (nz.NOZZLE_LEN - 1.5)))
    M = sum(m for m, _ in items)
    com = sum(m * c for m, c in items) / M
    return dict(mass_g=round(float(M), 3), shell_g=round(float(mesh.volume * RESIN), 3), com=com.round(2).tolist())


def hours(cap_lo, cap_hi):
    return dict(loud_h=[round(cap_lo * USABLE / I_LOUD, 1), round(cap_hi * USABLE / I_LOUD, 1)],
                quiet_h=[round(cap_lo * USABLE / I_QUIET, 1), round(cap_hi * USABLE / I_QUIET, 1)])


# ------------------------------------------------------------------ common head pieces
B = -N_IN * gen.NOZ_BASE_OUT
FRONT = B - N_IN * (gen.NOSE_WALL + gen.FRONT_GAP)
OUT = -N_IN


def driver(spec):
    d, h, m = spec
    return Cyl("driver", FRONT - N_IN * h, N_IN, d, h, m)


def codec_board_on(center_top, R, size=(8.0, 7.0)):
    """Codec board (ADAU1860 + crystal + passives) with parts facing down onto center_top's plane.
    R columns: (x, y, normal-out)."""
    n = R[:, 2]
    bot = Box("codec_parts", center_top + n * (GAP + 0.4), [size[0] - 0.6, size[1] - 0.6, 0.8], R, 0.05)
    pcb = Box("codec_pcb", center_top + n * (GAP + 0.8 + 0.4), [size[0], size[1], 0.8], R, 0.08)
    top = center_top + n * (GAP + 0.8 + 0.8)
    return [bot, pcb], top


def head_plane_R(normal):
    n = unit(normal)
    x = unit(np.cross(Y_, n))
    if np.linalg.norm(x) < 1e-6:
        x = X_
    y = np.cross(n, x)
    return np.stack([x, y, n], 1)


# ------------------------------------------------------------------ concepts
STEM_AXIS = unit([0.22, -1.0, 0.18])   # down, slightly forward and outward (pose search rolls/tilts it)


def stem_parts(root, length_parts, R):
    """Module board stacked along the stem; R columns (width, long, thin)."""
    w, s, t = R[:, 0], R[:, 1], R[:, 2]
    L = 13.0
    c = root + s * (length_parts + L / 2)
    bot = Box("pmic_parts", c - t * (0.4 + 0.5), [L - 0.6, 8.4 - 0.6, 1.0], R, 0.06)
    pcb = Box("pcb", c, [L, 8.4, 0.8], R, 0.12)
    mod = Box("module", c + s * (L / 2 - 0.3 - MODULE[0] / 2) + t * (0.4 + MODULE[2] / 2), [MODULE[1], MODULE[0], MODULE[2]], R, 0.4)
    end = root + s * (length_parts + L)
    return [bot, pcb, mod], end


def concept_stem_head_cell():
    lay = json.load(open(os.path.join(ERGO, "layout_cache.json")))["stacked"]
    bc = np.array(lay, float)                      # CP1254 centre (stacked layout)
    drv = driver(DRV8)
    bat = Cyl("battery", bc - Z_ * CP1254[1] / 2, Z_, CP1254[0], CP1254[1], CP1254[2])
    Rh = head_plane_R(Z_)
    cb, top = codec_board_on(bc + Z_ * CP1254[1] / 2, Rh)
    mic = Box("mic", top + Rh[:, 0] * 1.8 + Rh[:, 1] * 1.2 + Z_ * MIC[2] / 2, MIC, Rh, 0.02)
    R = frame(STEM_AXIS, Z_)
    root = bc - Y_ * (CP1254[0] / 2 - 1.0) + Z_ * 0.2
    sp, end = stem_parts(root, 3.2, R)
    s, w = R[:, 1], R[:, 0]
    mag = Cyl("magnet", end + s * GAP, s, MAG[0], MAG[1], MAG[2])
    parts = [drv, bat, *cb, mic, *sp, mag]
    # close_r 5.5 (vs 3.5): fills the notches between head, battery and stem so the body reads as one
    # smooth form instead of lumps around each part (Paul's review, 2026-10-31)
    kw = dict(nozzle_B=B, mic=(mic.c, Z_), pads=(end + s * GAP, s, w), close_r=5.5)
    return parts, kw, hours(60, 77), dict(cell="VARTA CP1254 (60-77 mAh)", driver="8 mm")


def concept_stem_cyl():
    """Stem with a cylindrical Li-ion cell (GP Batteries GP1018L10: 3.7 V, 100 mAh min / 105 typ,
    dia 10.5 x 18.0 mm with sleeve). The head keeps the 8 mm driver plus the module board (module
    on the outer face, antenna end toward the front) and the mic; the stem holds only the cell,
    with the charging pads and magnet at its tip."""
    drv = driver(DRV8)
    Rh = head_plane_R(OUT)
    back = FRONT - N_IN * DRV8[1]
    n = OUT
    L, W = 13.0, 9.0
    bot = Box("bottom_parts", back + n * (GAP + 0.5), [L - 0.6, W - 0.6, 1.0], Rh, 0.06)
    pcb = Box("pcb", back + n * (GAP + 1.0 + 0.4), [L, W, 0.8], Rh, 0.12)
    mod = Box("module", back + n * (GAP + 1.8 + MODULE[2] / 2) + Rh[:, 0] * (L / 2 - 0.3 - MODULE[0] / 2), [MODULE[0], MODULE[1], MODULE[2]], Rh, 0.4)
    mic = Box("mic", back + n * (GAP + 1.8 + MIC[2] / 2) - Rh[:, 0] * (L / 2 - 0.3 - MIC[0] / 2), MIC, Rh, 0.02)
    R = frame(STEM_AXIS, Z_)
    w, s_, t = R[:, 0], R[:, 1], R[:, 2]
    root = back + n * 1.6 - Y_ * (DRV8[0] / 2 + 0.8)
    cd, ch, cm = CYL_CELL
    cell = Cyl("battery", root + s_ * 1.5, s_, cd, ch, cm)
    end = root + s_ * (1.5 + ch)
    mag = Cyl("magnet", end + s_ * GAP, s_, MAG[0], MAG[1], MAG[2])
    parts = [drv, bot, pcb, mod, mic, cell, mag]
    kw = dict(nozzle_B=B, mic=(mic.c, OUT), pads=(end + s_ * GAP, s_, w))
    return parts, kw, hours(100, 105), dict(cell="GP Batteries GP1018L10, cylindrical Li-ion, 100-105 mAh", driver="8 mm")


def concept_bte_inear():
    drv = driver(DRV8)
    Rh = head_plane_R(OUT)
    back = FRONT - N_IN * DRV8[1]
    flex = Box("flex", back + OUT * (GAP + 0.3), [6.0, 6.0, 0.6], Rh, 0.03)
    mic = Box("mic", back + OUT * (GAP + 0.6 + MIC[2] / 2), MIC, Rh, 0.02)
    cdir = unit([-0.35, 1.0, 0.25])               # cable leaves up and back toward the helix root
    cable = Cyl("cable_boss", back + OUT * 1.4 + Y_ * 2.2, cdir, 1.8, 6.0, 0.05)
    parts = [drv, flex, mic, cable]
    kw = dict(nozzle_B=B, mic=(mic.c, OUT), pads=None)
    return parts, kw, None, dict(driver="8 mm", note="receiver-in-canal unit; electronics in the pod")


def pod_parts():
    """Behind-ear pod in its own frame: X anterior (toward the pinna), Y along the pod (up),
    Z lateral (away from the scalp). Battery at the top, module board below, pads at the bottom."""
    bat = Cyl("battery", np.array([0.0, 0.0, -CP1454[1] / 2]), Z_, CP1454[0], CP1454[1], CP1454[2])
    R = np.eye(3)
    L = 13.0
    c = np.array([0.0, -(CP1454[0] / 2 + GAP + L / 2), -0.6])
    bot = Box("pmic_parts", c - Z_ * 0.9, [9.0 - 0.6, L - 0.6, 1.0], R, 0.06)
    pcb = Box("pcb", c, [9.0, L, 0.8], R, 0.12)
    mod = Box("module", c + Y_ * (-(L / 2) + 0.3 + MODULE[0] / 2) + Z_ * (0.4 + MODULE[2] / 2), [MODULE[1], MODULE[0], MODULE[2]], R, 0.4)
    end = np.array([0.0, -(CP1454[0] / 2 + GAP + L), -0.6])
    mag = Cyl("magnet", end - Y_ * GAP, -Y_, MAG[0], MAG[1], MAG[2])
    parts = [bat, bot, pcb, mod, mag]
    kw = dict(nozzle_B=None, mic=None, pads=(end - Y_ * GAP, -Y_, X_))
    return parts, kw


# ------------------------------------------------------------------ run
def export_parts(parts, fd, d):
    os.makedirs(d, exist_ok=True)
    for p in parts:
        p.mesh().export(os.path.join(d, f"{p.name}.stl"))
    for i, (c0, md) in enumerate(fd["pads"]):
        Cyl(f"pad{i + 1}", c0 + md * 0.5, md, PAD_D - 0.1, 1.2).mesh().export(os.path.join(d, f"pad{i + 1}.stl"))
    json.dump([p.desc() for p in parts] + [dict(name=f"pad{i + 1}", kind="cylinder", base=(c0 + md * 0.5).round(3).tolist(),
                                                axis=np.asarray(md).round(4).tolist(), diameter=PAD_D - 0.1, height=1.2)
                                           for i, (c0, md) in enumerate(fd["pads"])],
              open(os.path.join(d, "parts.json"), "w"), indent=1)


def run_parts_concept(tag, parts, kw, life, info, report, tip=True, skip_pairs=()):
    import time
    t0 = time.time()
    gp = min_gap(parts, skip_pairs)
    mesh, fd = shell_mesh(parts, **kw)
    mesh.export(os.path.join(HERE, f"{tag}_shell.stl"))
    export_parts(parts, fd, os.path.join(HERE, f"parts_{tag}"))
    rep = dict(info, bbox_mm=[round(float(x), 2) for x in mesh.extents], watertight=bool(mesh.is_watertight),
               faces=int(len(mesh.faces)), min_part_gap=[round(gp[0], 3), gp[1]], checks=clearances(fd, parts),
               **mass_props(mesh, parts, tip=tip))
    if life:
        rep["battery_life"] = life
    report[tag] = rep
    print(tag, round(time.time() - t0), "s", json.dumps(rep), flush=True)
    return mesh


STACKED = {frozenset(p) for p in [("pcb", "pmic_parts"), ("pcb", "module"), ("pmic_parts", "module"), ("pcb", "bottom_parts"), ("bottom_parts", "module"), ("mic", "pcb"), ("mic", "bottom_parts"), ("mic", "module"),
                                  ("codec_pcb", "codec_parts"), ("codec_pcb", "mic"), ("codec_parts", "mic"),
                                  ("flex", "mic"), ("flex", "cable_boss"), ("mic", "cable_boss")]}


def main(names):
    gp = os.path.join(HERE, "geometry.json")
    report = json.load(open(gp)) if os.path.exists(gp) else {}
    if "stem_head_cell" in names:
        parts, kw, life, info = concept_stem_head_cell()
        run_parts_concept("stem_head_cell", parts, kw, life, info, report, skip_pairs=STACKED)
    if "stem_cyl" in names:
        parts, kw, life, info = concept_stem_cyl()
        run_parts_concept("stem_cyl", parts, kw, life, info, report, skip_pairs=STACKED)
    if "bte" in names:
        parts, kw, life, info = concept_bte_inear()
        run_parts_concept("bte_inear", parts, kw, None, info, report, skip_pairs=STACKED)
        pparts, pkw = pod_parts()
        run_parts_concept("bte_pod", pparts, pkw, hours(85, 120), dict(cell="VARTA CP1454 (85-120 mAh)"), report, tip=False,
                          skip_pairs=STACKED)
    json.dump(report, open(gp, "w"), indent=1)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or {"stem_head_cell", "stem_cyl", "bte"})
