"""Haven v2 ergonomic shell: an in-concha body around the v2 internals.

The rev_b_fit_study bud stacked speaker, battery and board straight out of the canal (a
16.7 x 18.9 x 17.5 mm block, ~13 mm of stack along the nozzle axis), so it sat proud of
the ear. Here the battery and board stack lie flat in the cavum concha, parallel to the
side of the head, and only the speaker "nose" turns into the canal.

Frame (right ear, worn): origin = canal entrance E, X = anterior, Y = superior, Z = lateral
(out of the head). The canal entrance axis points inward, forward and slightly up
(Gray's Anatomy: the lateral canal runs "inward, forward, and slightly upward"); the exact
angles are CANAL_ANT_DEG / CANAL_SUP_DEG, checked for sensitivity in evaluate_fit.py.

The shell is an implicit surface: the parts' exact signed distance fields are offset by
CLR + WALL, closed morphologically (CLOSE_R fills concavities, so the body reads as one
smooth pebble with no hard corners), lightly smoothed, then hollowed by a uniform WALL.
The nozzle (nozzle.py dimensions), sound bore, mic port and charging-pad holes are exact
CSG on the same field, and the result is meshed with marching cubes. Two internal layouts
are generated (see layout()). Run:
    python3 generate_v2_ergonomic_shell.py [stacked] [nested]
"""
import json
import math
import os
import sys

import numpy as np
import cadquery as cq
from scipy.ndimage import gaussian_filter1d

import nozzle as nz

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- rules ----
WALL = 1.1           # resin SLA wall
CLR = 0.4            # air between part and inner wall
CHECK_CLR = 0.3
GAP = 0.3            # between neighbouring parts
NOSE_WALL = 1.0      # wall between driver front volume and nozzle base
FRONT_GAP = 0.4      # driver front volume
NOZ_BASE_OUT = 1.0   # nozzle base sits this far outside the canal entrance (tip ends 4.5 mm in)
ANT_OVERHANG = 2.5   # module antenna end overhangs the battery's edge
CANAL_ANT_DEG = 25.0
CANAL_SUP_DEG = 10.0

# ---- part envelopes (mm), same as rev_b_fit_study ----
BAT_D, BAT_H = 12.1, 5.4             # VARTA CP1254
DRV_D, DRV_H = 8.0, 3.6              # 8 mm 16-32 ohm dynamic driver (representative)
PCB = (13.0, 9.0, 0.8)               # long axis anterior-posterior
BOTTOM_H = 1.0
MODULE = (12.4, 7.8, 1.85)           # Raytac MDBT53V-1M, antenna end anterior
MIC = (3.5, 2.65, 0.98)              # SPH0641LU4H-1 lying flat, port lateral
MAG_D, MAG_H = 3.0, 2.0              # N52 disc
PAD_D, PAD_PITCH = 1.6, 2.5

# masses (g) for the centre of mass
MASS = dict(battery=1.7, module=0.4, driver=0.5, pcb=0.17, bottom_parts=0.10,
            magnet=0.11, mic=0.02, tip=0.10)
RESIN_DENSITY = 1.2e-3               # g/mm^3

# Design variant. HAVEN_VARIANT=small swaps in the smaller battery and driver Paul asked to see
# (VARTA CP0854, Ø8.0 x 5.4 mm, ~40 mAh, about 5 h loud; a representative 6 mm 16-32 ohm
# driver). Outputs get a "_small" suffix so the current design's files are untouched.
VARIANT = os.environ.get("HAVEN_VARIANT", "")
SUFFIX = "_small" if VARIANT == "small" else ""
if VARIANT == "small":
    BAT_D, BAT_H = 8.0, 5.4          # VARTA CP0854
    DRV_D, DRV_H = 6.0, 3.0          # 6 mm 16-32 ohm dynamic driver (representative)
    MASS.update(battery=1.1, driver=0.3)   # CP0854 ~1.1 g (approx.), 6 mm driver ~0.3 g (est.)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


N_IN = unit([math.tan(math.radians(CANAL_ANT_DEG)), math.tan(math.radians(CANAL_SUP_DEG)), -1.0])
X_, Y_, Z_ = np.eye(3)


def V(p):
    return cq.Vector(*map(float, p))


def box(center, size):
    c, s = np.asarray(center, float), np.asarray(size, float)
    return cq.Solid.makeBox(*s, V(c - s / 2))


def cyl(base, axis, d, h):
    return cq.Solid.makeCylinder(d / 2, h, V(base), V(axis))


# ------------------------------------------------------------------ layout
def box_rot(center, size, ang_deg):
    s_ = box([0, 0, 0], size)
    return s_.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), ang_deg).translate(V(center))


def layout(mode, bat_a, bat_b, bat_z):
    """Place every part. Returns (parts, key).

    stacked: driver on the canal axis, battery stacked lateral of it; (bat_a, bat_b) = battery
             centre X, Y.
    nestled: driver faces medially at the canal; battery beside it in the cavum concha at
             in-plane angle bat_a (deg from anterior, 90 = superior, 180 = posterior) and
             centre distance bat_b from the driver axis; board spans battery and driver.
    """
    B = -N_IN * NOZ_BASE_OUT
    front = B - N_IN * (NOSE_WALL + FRONT_GAP)
    parts = {}
    if mode == "stacked":
        parts["driver"] = cyl(front - N_IN * DRV_H, N_IN, DRV_D, DRV_H)
        bat_c = np.array([bat_a, bat_b, bat_z])
        d2 = np.array([1.0, 0, 0])                 # board long axis, antenna end toward +X
        drv_top = None
    else:
        parts["driver"] = cyl(front, Z_, DRV_D, DRV_H)
        drv_top = front[2] + DRV_H
        ang = math.radians(bat_a)
        d1 = np.array([math.cos(ang), math.sin(ang), 0.0])   # driver -> battery
        bat_c = np.array([front[0], front[1], bat_z]) + d1 * bat_b
        d2 = -d1                                    # board long axis points back to the driver
    parts["battery"] = cyl(bat_c - Z_ * BAT_H / 2, Z_, BAT_D, BAT_H)
    z = bat_c[2] + BAT_H / 2 + GAP
    if drv_top is not None:
        z = max(z, drv_top + GAP)
    pcb_c2 = bat_c[:2] + d2[:2] * (BAT_D / 2 + ANT_OVERHANG - PCB[0] / 2)
    ang2 = math.degrees(math.atan2(d2[1], d2[0]))
    parts["bottom_parts"] = box_rot([*pcb_c2, z + BOTTOM_H / 2], [PCB[0] - 0.6, PCB[1] - 0.6, BOTTOM_H], ang2)
    z += BOTTOM_H
    parts["pcb"] = box_rot([*pcb_c2, z + PCB[2] / 2], PCB, ang2)
    z += PCB[2]
    mod_c2 = pcb_c2 + d2[:2] * (PCB[0] / 2 - 0.3 - MODULE[0] / 2)
    parts["module"] = box_rot([*mod_c2, z + MODULE[2] / 2], MODULE, ang2)
    z_top = z + MODULE[2]
    # mic on a short flex past the board's far (non-antenna) end, lying flat, port lateral
    mic_c2 = pcb_c2 - d2[:2] * (PCB[0] / 2 + GAP + MIC[0] / 2)
    parts["mic"] = box_rot([*mic_c2, z_top - MIC[2] / 2], MIC, ang2)
    # magnet at the battery's far edge (case-facing end); pads flank it across the board axis
    mag_dir = -d2
    mag_base = bat_c + mag_dir * (BAT_D / 2 + GAP)
    parts["magnet"] = cyl(mag_base, mag_dir, MAG_D, MAG_H)
    key = dict(mode=mode, B=B, front=front, bat_c=bat_c, z_top=z_top, d2=d2, mag_base=mag_base, mag_dir=mag_dir,
               pcb_c2=pcb_c2)
    return parts, key


def min_gap(parts):
    names = list(parts)
    worst = (1e9, None)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if names[i] in ("pcb", "bottom_parts", "module") and names[j] in ("pcb", "bottom_parts", "module"):
                continue  # stacked on purpose
            d = parts[names[i]].distance(parts[names[j]])
            if d < worst[0]:
                worst = (d, (names[i], names[j]))
    return worst


def axis_dist(p):
    """Distance from a point to the canal axis line through E."""
    p = np.asarray(p, float)
    return float(np.linalg.norm(p - np.dot(p, N_IN) * N_IN))


def choose_layout(mode):
    best = None
    if mode == "stacked":
        grid = [(x, 0.0, z) for z in np.arange(4.0, 12.01, 0.5) for x in np.arange(-9.0, 1.01, 0.5)]
    else:
        grid = [(a, d, z) for a in (105, 120, 135, 150, 165) for d in np.arange(6.0, 12.51, 0.5) for z in np.arange(3.0, 6.01, 0.5)]
    for g in grid:
        parts, key = layout(mode, *g)
        gp, _ = min_gap(parts)
        if gp < GAP - 1e-6:
            continue
        if mode == "stacked":
            cost = key["z_top"] + 0.6 * axis_dist(key["bat_c"])
        else:
            if key["bat_c"][2] - BAT_H / 2 > key["front"][2] + DRV_H - 0.5:
                continue  # must sit beside the driver, not on it
            reach = max(np.linalg.norm(np.array(p.Center().toTuple())[:2]) for p in parts.values())
            cost = key["z_top"] + 0.25 * axis_dist(key["bat_c"]) + 0.3 * reach
        if best is None or cost < best[0]:
            best = (cost, g)
    return best[1]


def spine_ctrl(key):
    bc = key["bat_c"]
    top = np.array([0.5 * (bc[0] + key["pcb_c2"][0]), 0.5 * (bc[1] + key["pcb_c2"][1]), key["z_top"] - 0.2])
    P3 = key["B"]
    h = top[2] - P3[2]
    return (top, top - Z_ * 0.35 * h, P3 - N_IN * 0.35 * h, P3)


# ------------------------------------------------------------------ signed distance fields
RES = 0.2           # mm voxel
CLOSE_R = 3.5       # closing radius: concavities tighter than this get filled
SMOOTH = 0.45       # mm gaussian on the field
BUILD_MARGIN = 0.4  # extra offset so smoothing never eats into CLR


def sd_box_z(P, center, size, ang_deg):
    """Box rotated about Z by ang_deg around its centre."""
    a = math.radians(ang_deg)
    R = np.array([[math.cos(a), math.sin(a), 0], [-math.sin(a), math.cos(a), 0], [0, 0, 1]])
    q = np.abs((P - center) @ R.T) - np.asarray(size) / 2
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(-1), 0)


def sd_cyl(P, base, axis, r, h):
    axis = unit(axis)
    v = P - base
    t = v @ axis
    rad = np.linalg.norm(v - t[..., None] * axis, axis=-1)
    d = np.stack([rad - r, np.abs(t - h / 2) - h / 2], -1)
    return np.linalg.norm(np.maximum(d, 0), axis=-1) + np.minimum(d.max(-1), 0)


def sd_cone(P, base, axis, r0, r1, h):
    axis = unit(axis)
    v = P - base
    t = v @ axis
    rad = np.linalg.norm(v - t[..., None] * axis, axis=-1)
    rt = r0 + (r1 - r0) * np.clip(t / h, 0, 1)
    side = (rad - rt) / math.sqrt(1 + ((r1 - r0) / h) ** 2)
    return np.maximum(side, np.abs(t - h / 2) - h / 2)


def part_sdfs(parts_spec, P):
    out = []
    for kind, args in parts_spec.values():
        out.append(sd_box_z(P, *args) if kind == "box" else sd_cyl(P, *args))
    return np.min(out, axis=0)


def nozzle_sdf(P, B):
    r = nz.NOZZLE_OD / 2
    root = B - N_IN * 1.5
    shaft = sd_cyl(P, root, N_IN, r, 1.5 + nz.NOZZLE_LEN - nz.LIP_LEN)
    lip0 = B + N_IN * (nz.NOZZLE_LEN - nz.LIP_LEN)
    lip = sd_cyl(P, lip0, N_IN, r + nz.LIP_HEIGHT, nz.LIP_LEN - nz.LIP_LEADIN)
    lead = sd_cone(P, B + N_IN * (nz.NOZZLE_LEN - nz.LIP_LEADIN), N_IN, r + nz.LIP_HEIGHT, r + 0.05, nz.LIP_LEADIN)
    return np.minimum(np.minimum(shaft, lip), lead)


def fin_sdf(P, key):
    """Concha-lock fin: a tapered capsule chain from the body's far end, reaching up/back under
    the antihelix (print in flexible resin or as a silicone sleeve)."""
    bc = key["bat_c"]
    far = bc - key["d2"] * (BAT_D / 2 - 1.0)
    up = unit(np.array([-0.55, 0.83, 0.0]))
    pts = [far + np.array([0, 0, 0.5]), far + up * 4.0 + [0, 0, 1.0], far + up * 7.5 + [-1.5, 0, 1.2], far + up * 9.5 + [-3.5, 0, 1.0]]
    rads = [1.6, 1.25, 0.95, 0.7]
    d = np.full(P.shape[:-1], 1e9)
    for (a, ra), (b, rb) in zip(zip(pts[:-1], rads[:-1]), zip(pts[1:], rads[1:])):
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        dist = np.linalg.norm(P - (a + t[..., None] * ab), axis=-1) - (ra + (rb - ra) * t)
        d = np.minimum(d, dist)
    return d


def spec_from_layout(mode, *g):
    """Analytic copies of the layout() parts (for the distance field)."""
    parts, key = layout(mode, *g)
    spec = {}
    for name, sol in parts.items():
        bb = sol.BoundingBox()
        spec[name] = None
    B = key["B"]
    front = key["front"]
    if mode == "stacked":
        spec["driver"] = ("cyl", (front - N_IN * DRV_H, N_IN, DRV_D / 2, DRV_H))
    else:
        spec["driver"] = ("cyl", (front, Z_, DRV_D / 2, DRV_H))
    bc = key["bat_c"]
    spec["battery"] = ("cyl", (bc - Z_ * BAT_H / 2, Z_, BAT_D / 2, BAT_H))
    d2 = key["d2"]
    ang2 = math.degrees(math.atan2(d2[1], d2[0]))
    for name in ("bottom_parts", "pcb", "module", "mic"):
        c = np.array(parts[name].Center().toTuple())
        size = {"bottom_parts": [PCB[0] - 0.6, PCB[1] - 0.6, BOTTOM_H], "pcb": list(PCB), "module": list(MODULE), "mic": list(MIC)}[name]
        spec[name] = ("box", (c, size, ang2))
    spec["magnet"] = ("cyl", (key["mag_base"], key["mag_dir"], MAG_D / 2, MAG_H))
    return parts, key, spec


def make_field(parts, key, spec, fin=False, shift=0.0):
    from scipy.ndimage import distance_transform_edt, gaussian_filter
    bbs = [s.BoundingBox() for s in parts.values()]
    allp = np.array([[b.xmin, b.ymin, b.zmin] for b in bbs] + [[b.xmax, b.ymax, b.zmax] for b in bbs])
    tip = key["B"] + N_IN * (nz.NOZZLE_LEN + 0.5)
    lo = np.minimum(allp.min(0), tip) - (CLR + WALL + CLOSE_R + 2.0)
    hi = np.maximum(allp.max(0), tip) + (CLR + WALL + CLOSE_R + 2.0)
    if fin:
        lo -= 6; hi += 6
    axes = [np.arange(l + shift, h + RES, RES) for l, h in zip(lo, hi)]
    G = np.stack(np.meshgrid(*axes, indexing="ij"), -1).astype(np.float32)
    D = part_sdfs(spec, G)
    X0 = D <= CLR + WALL + BUILD_MARGIN
    # nozzle root region joins the body smoothly
    X0 |= sd_cyl(G, key["B"] - N_IN * 2.5, N_IN, nz.NOZZLE_OD / 2 + 0.6, 2.5) <= 0
    if fin:
        X0 |= fin_sdf(G, key) <= 0
    # closing
    dil = distance_transform_edt(~X0) * RES <= CLOSE_R
    C = distance_transform_edt(dil) * RES > CLOSE_R
    C |= X0
    sd = (distance_transform_edt(~C) - distance_transform_edt(C)) * RES
    sd = gaussian_filter(sd, SMOOTH / RES)
    shell = np.maximum(sd, -(sd + WALL))                     # uniform wall band
    shell = np.minimum(shell, nozzle_sdf(G, key["B"]))
    bore0 = key["B"] - N_IN * (NOSE_WALL + FRONT_GAP + 0.6)
    shell = np.maximum(shell, -sd_cyl(G, bore0, N_IN, nz.BORE_D / 2, nz.NOZZLE_LEN + NOSE_WALL + FRONT_GAP + 1.5))
    # mic port: straight out through the lateral wall above the mic
    mc = spec["mic"][1][0]
    shell = np.maximum(shell, -sd_cyl(G, mc, Z_, 0.45, 12.0))
    # charging pads: holes at the magnet end, flanking the magnet across the board axis
    md = key["mag_dir"]
    across = unit(np.cross(Z_, md))
    pads = []
    for sgn in (-1, 1):
        c0 = key["mag_base"] + across * sgn * PAD_PITCH - md * 0.5
        shell = np.maximum(shell, -sd_cyl(G, c0, md, PAD_D / 2, CLR + WALL + BUILD_MARGIN + 1.2))
        pads.append((c0, md))
    for ax in range(3):  # close the mesh at the grid boundary
        sl = [slice(None)] * 3
        for idx in (0, -1):
            sl[ax] = idx
            shell[tuple(sl)] = np.maximum(shell[tuple(sl)], RES)
    return dict(axes=axes, G=G, field=shell, body_sd=sd, D=D, pads=pads)


def mesh_from_field(F, axes):
    from skimage.measure import marching_cubes
    import trimesh
    verts, faces, _, _ = marching_cubes(F, level=0.0, spacing=(RES, RES, RES))
    verts += np.array([a[0] for a in axes])
    m = trimesh.Trimesh(verts, faces[:, ::-1], process=True)
    if not m.is_watertight:
        trimesh.repair.fill_holes(m)
        m.merge_vertices()
    if m.volume < 0:
        m.invert()
    return m


def checks(fd, parts):
    """Every part inside the cavity (body_sd <= -WALL) with >= CHECK_CLR to the inner wall."""
    from scipy.interpolate import RegularGridInterpolator
    f = RegularGridInterpolator(fd["axes"], fd["body_sd"], bounds_error=False, fill_value=9.0)
    res = {}
    for name, s_ in parts.items():
        v, _ = s_.tessellate(0.02, 0.1)
        P = np.array([x.toTuple() for x in v])
        clr = -(f(P) + WALL)
        res[name] = dict(clearance=round(float(clr.min()), 3), ok=bool(clr.min() >= CHECK_CLR - 0.05))
    return res


def mass_props(parts, mesh):
    m_shell = mesh.volume * RESIN_DENSITY
    items = [(m_shell, mesh.center_mass)]
    for name, s_ in parts.items():
        items.append((MASS[name], np.array(s_.Center().toTuple())))
    items.append((MASS["tip"], -N_IN * NOZ_BASE_OUT + N_IN * (nz.NOZZLE_LEN - 1.5)))
    M = sum(m for m, _ in items)
    com = sum(m * c for m, c in items) / M
    return dict(mass_g=round(M, 3), shell_g=round(m_shell, 3), com=com.round(2).tolist())


def mesh_to_step(mesh, path, faces=5000):
    """Faceted STEP from the (decimated) mesh. The STL is the smooth master."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.TopoDS import TopoDS
    from OCP.gp import gp_Pnt
    from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
    m = mesh.simplify_quadric_decimation(face_count=min(faces, len(mesh.faces)))
    sew = BRepBuilderAPI_Sewing(1e-4)
    for tri in m.triangles:
        poly = BRepBuilderAPI_MakePolygon(*[gp_Pnt(*map(float, p)) for p in tri], True)
        sew.Add(BRepBuilderAPI_MakeFace(poly.Wire()).Face())
    sew.Perform()
    sh = sew.SewedShape()
    try:
        solid = BRepBuilderAPI_MakeSolid(TopoDS.Shell_s(sh)).Solid()
    except Exception:
        solid = sh
    w = STEPControl_Writer()
    w.Transfer(solid, STEPControl_AsIs)
    w.Write(path)


def export_parts(parts, fd, d):
    os.makedirs(d, exist_ok=True)
    for name, s_ in parts.items():
        cq.exporters.export(s_, os.path.join(d, f"{name}.stl"), tolerance=0.02, angularTolerance=0.2)
    for i, (c0, md) in enumerate(fd["pads"]):
        pad = cq.Solid.makeCylinder(PAD_D / 2 - 0.05, 1.2, V(c0 + md * 0.5), V(md))
        cq.exporters.export(pad, os.path.join(d, f"pad{i + 1}.stl"))


def main(modes=("stacked", "nestled")):
    import time
    cache_p = os.path.join(HERE, "layout_cache.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    gp = os.path.join(HERE, "geometry.json")
    report = json.load(open(gp)) if os.path.exists(gp) else {}
    report.update(canal_axis_in=N_IN.round(4).tolist(), canal_ant_deg=CANAL_ANT_DEG, canal_sup_deg=CANAL_SUP_DEG)
    for mode in modes:
        ck = mode + SUFFIX
        if ck not in cache:
            cache[ck] = [float(x) for x in choose_layout(mode)]
            json.dump(cache, open(cache_p, "w"), indent=1)
        parts, key, spec = spec_from_layout(mode, *cache[ck])
        print(ck, "layout", cache[ck], "gap", round(min_gap(parts)[0], 3), flush=True)
        for fin in ((False,) if SUFFIX else (False, True)):
            t = time.time()
            tag = f"v2_{mode}{SUFFIX}" + ("_fin" if fin else "")
            for shift in (0.0, 0.07, 0.13):   # re-sample if marching cubes pinches an edge
                fd = make_field(parts, key, spec, fin=fin, shift=shift)
                mesh = mesh_from_field(fd["field"], fd["axes"])
                if mesh.is_watertight:
                    break
            mesh.export(os.path.join(HERE, f"{tag}_shell.stl"))
            mesh_to_step(mesh, os.path.join(HERE, f"{tag}_shell.step"))
            export_parts(parts, fd, os.path.join(HERE, f"parts_{mode}{SUFFIX}"))
            ext = mesh.extents
            rep = dict(layout=cache[ck], variant=VARIANT or "current", battery=[BAT_D, BAT_H], driver=[DRV_D, DRV_H], battery_center=key["bat_c"].round(2).tolist(),
                       bbox_mm=[round(float(x), 2) for x in ext], max_lateral_above_E=round(float(mesh.bounds[1][2]), 2),
                       watertight=bool(mesh.is_watertight), faces=int(len(mesh.faces)),
                       checks=checks(fd, parts), **mass_props(parts, mesh))
            report[tag] = rep
            json.dump(report, open(gp, "w"), indent=1)
            print(tag, round(time.time() - t), "s", json.dumps(rep), flush=True)


if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or ("stacked", "nestled"))
