"""Rev B fit study: smallest earbud shell around real part envelopes, plus a charging case.

A packaging study, not a styled product (the v3-style lofted surface comes once the internals freeze): every dimension below is a part envelope
from a datasheet or a stated assumption (see README.md). The bud shell is lofted from
one rounded-rectangle footprint that holds every part with CLR of air, extruded over the
stack height with rounded top/bottom edges, then hollowed by WALL. Run `python3 generate_rev_b_fit_study.py`.
"""
import math
import os

import numpy as np
import cadquery as cq
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pnt, gp_Pln, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_UniformAbscissa

import nozzle as nz

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- global packaging rules ----
WALL = 1.2          # resin SLA shell wall
CLR = 0.4           # air between a part and the inner wall (check threshold is 0.3)
CHECK_CLR = 0.3
GAP = 0.3           # between stacked parts (foam/adhesive)
ANT_CLEAR = 2.5     # module antenna end overhangs the battery by at least this much
NOZZLE_TILT = 15.0  # deg, nozzle leans toward +Y ("forward/up" toward the canal)

# ---- part envelopes (mm) ----
BATTERY = dict(d=12.1, h=5.4)                 # VARTA CoinPower CP1254
SPEAKERS = {
    "dyn8": dict(d=8.0, h=3.6),               # 8 mm-class dynamic micro driver (representative)
    "dyn6": dict(d=6.0, h=3.0),               # 6 mm-class dynamic micro driver (representative)
}
SPEAKER = "dyn8"
BOARD_T = 0.8                                 # Rev B board thickness (Rev A is 1.6)
BOTTOM_PARTS_H = 1.0                          # codec, PMIC, crystals, passives on the bottom side
MIC = dict(x=0.98, y=3.50, z=2.65)            # SPH0641LU4H-1 3.50 x 2.65 x 0.98, standing on +X wall
MAGNET = dict(d=3.0, h=2.0)                   # N52 disc, axis along -Y
PAD_D = 1.6                                   # gold charging pads (2), through the -Y wall
PAD_PITCH = 2.5
VARIANTS = {
    # module footprint -> board around it (module on top, antenna end toward +Y)
    "mdbt53v": dict(board=(9.0, 13.0), module=(7.8, 12.4, 1.85), label="Raytac MDBT53V-1M"),
    "isp2053": dict(board=(9.0, 9.0), module=(8.0, 8.0, 1.0), label="Insight SiP ISP2053-AX"),
}

# Published reference envelopes for comparison (mm)
REF = {
    "OpenEarable 2.0 front shell (Rev A)": (16.6, 34.6, 21.2),
    "AirPods Pro (2nd gen) bud, Apple spec": (21.8, 30.9, 24.0),
}


# ---------------------------------------------------------------- parts
def box(cx, cy, cz, sx, sy, sz):
    return cq.Solid.makeBox(sx, sy, sz, cq.Vector(cx - sx / 2, cy - sy / 2, cz - sz / 2))


def cyl_z(cx, cy, z0, d, h):
    return cq.Solid.makeCylinder(d / 2, h, cq.Vector(cx, cy, z0), cq.Vector(0, 0, 1))


def layout(variant, speaker=SPEAKER):
    """Place every part. Returns {name: (solid, outline_fn)} plus key frame values.

    outline_fn(z) returns the part's xy outline points if the part spans z, else [].
    """
    v = VARIANTS[variant]
    bw, bl = v["board"]
    mw, ml, mh = v["module"]
    spk = SPEAKERS[speaker]
    r_bat = BATTERY["d"] / 2

    # board centred on y=0; battery pushed toward -Y so the antenna end overhangs it
    bat_y = min(-bl / 2 + r_bat, (bl / 2 - ANT_CLEAR) - r_bat)
    spk_y = bat_y
    z = 0.0
    parts = {}

    def add_cyl(name, cx, cy, z0, d, h):
        s = cyl_z(cx, cy, z0, d, h)
        ang = np.linspace(0, 2 * np.pi, 48, endpoint=False)
        pts = [(cx + d / 2 * math.cos(a), cy + d / 2 * math.sin(a)) for a in ang]
        parts[name] = (s, (z0, z0 + h), pts)

    def add_box(name, cx, cy, cz, sx, sy, sz):
        s = box(cx, cy, cz, sx, sy, sz)
        pts = [(cx + dx * sx / 2, cy + dy * sy / 2) for dx in (-1, 1) for dy in (-1, 1)]
        parts[name] = (s, (cz - sz / 2, cz + sz / 2), pts)

    add_cyl("speaker", 0, spk_y, z, spk["d"], spk["h"]); z += spk["h"] + GAP
    add_cyl("battery", 0, bat_y, z, BATTERY["d"], BATTERY["h"]); z += BATTERY["h"] + GAP
    add_box("bottom_parts", 0, 0, z + BOTTOM_PARTS_H / 2, bw - 0.6, bl - 0.6, BOTTOM_PARTS_H)
    z += BOTTOM_PARTS_H
    add_box("pcb", 0, 0, z + BOARD_T / 2, bw, bl, BOARD_T)
    board_mid = z + BOARD_T / 2
    z += BOARD_T
    add_box("module", 0, bl / 2 - ml / 2, z + mh / 2, mw, ml, mh)
    z += mh
    add_box("mic", bw / 2 + GAP + MIC["x"] / 2, -1.0, board_mid, MIC["x"], MIC["y"], MIC["z"])
    # magnet against the -X wall in the speaker band; the charging pads flank it.
    # -X is the face the bud rests on in the case (it is the bud's smallest dimension).
    spk_mid = spk["h"] / 2
    mag_x0 = -(spk["d"] / 2 + GAP)
    mag = cq.Solid.makeCylinder(MAGNET["d"] / 2, MAGNET["h"], cq.Vector(mag_x0, spk_y, spk_mid), cq.Vector(-1, 0, 0))
    pts = [(mag_x0 - dx * MAGNET["h"], spk_y + dy * MAGNET["d"] / 2) for dx in (0, 1) for dy in (-1, 1)]
    parts["magnet"] = (mag, (spk_mid - MAGNET["d"] / 2, spk_mid + MAGNET["d"] / 2), pts)
    frame = dict(bat_y=bat_y, spk_y=spk_y, spk_mid=spk_mid, board_mid=board_mid, z_top=z, bw=bw, bl=bl)
    return parts, frame


# ---------------------------------------------------------------- shell
def rrect_wire(cx, cy, z, a, b, r):
    r = max(0.2, min(r, a - 0.05, b - 0.05))
    pts = [cq.Vector(cx - a, cy - b, z), cq.Vector(cx + a, cy - b, z),
           cq.Vector(cx + a, cy + b, z), cq.Vector(cx - a, cy + b, z)]
    w = cq.Wire.makePolygon(pts, close=True)
    return w.fillet2D(r, w.Vertices())


def contains(cx, cy, a, b, r, pts):
    for x, y in pts:
        px, py = abs(x - cx), abs(y - cy)
        if px > a or py > b:
            return False
        if px > a - r and py > b - r:
            if (px - (a - r)) ** 2 + (py - (b - r)) ** 2 > r * r:
                return False
    return True


R_OUT = 2.6          # top/bottom edge rounding of the outer shell
R_IN = R_OUT - WALL
Z_EXTRA = 0.5        # headroom so corner parts clear the inner edge rounding


def footprint(parts):
    """Smallest rounded rect (with CLR) holding every part's xy outline."""
    pts = [p for (_, _, pp) in parts.values() for p in pp]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    a, b = (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2
    while True:
        r = 0.6 * min(a, b)
        if contains(cx, cy, a, b, r, pts):
            break
        a += 0.05; b += 0.05
    return cx, cy, a + CLR, b + CLR, r + CLR


def rounded_block(cx, cy, a, b, r, z0, z1, fillet):
    face = cq.Face.makeFromWires(rrect_wire(cx, cy, z0, a, b, r))
    sol = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, z1 - z0))
    wp = cq.Workplane().add(sol)
    wp = wp.faces(">Z").edges().fillet(fillet)
    wp = wp.faces("<Z").edges().fillet(fillet)
    return wp.val()


def build_bud(variant, speaker=SPEAKER, envelope_only=False):
    parts, fr = layout(variant, speaker)
    zs = [p[1][0] for p in parts.values()] + [p[1][1] for p in parts.values()]
    zmin, zmax = min(zs), max(zs)
    cx, cy, A, B, r = footprint(parts)
    zbot, ztop = zmin - CLR - Z_EXTRA - WALL, zmax + CLR + Z_EXTRA + WALL
    outer = rounded_block(cx, cy, A + WALL, B + WALL, r + WALL, zbot, ztop, R_OUT)

    t = math.radians(NOZZLE_TILT)
    axis = cq.Vector(0, math.sin(t), -math.cos(t))
    base = cq.Vector(0, fr["spk_y"], zbot)
    noz = nz.nozzle_solid(base, axis, nz.NOZZLE_LEN, root_len=0.4)  # stays inside the wall
    if envelope_only:
        bb = outer.BoundingBox().add(noz.BoundingBox())
        return (bb.xlen, bb.ylen, bb.zlen)

    inner = rounded_block(cx, cy, A, B, r, zbot + WALL, ztop - WALL, R_IN)
    shell = outer.cut(inner).fuse(noz).clean()
    bore = nz.bore_solid(base - axis * (WALL + Z_EXTRA + CLR * 0.5), axis, nz.NOZZLE_LEN + WALL + Z_EXTRA + CLR)
    shell = shell.cut(bore).clean()

    mb = parts["mic"][0].BoundingBox()
    port = cq.Solid.makeCylinder(0.4, 6.0, cq.Vector(mb.xmax - 0.1, (mb.ymin + mb.ymax) / 2, (mb.zmin + mb.zmax) / 2), cq.Vector(1, 0, 0))
    shell = shell.cut(port).clean()

    pads = []
    x_in = cx - A + 0.05   # just inside the -X inner wall
    for dy in (-(PAD_PITCH + 0.6), PAD_PITCH + 0.6):
        c = cq.Solid.makeCylinder(PAD_D / 2, 10.0, cq.Vector(x_in, fr["spk_y"] + dy, fr["spk_mid"]), cq.Vector(-1, 0, 0))
        pads.append(shell.intersect(c))
        shell = shell.cut(c).clean()
    info = dict(variant=variant, speaker=speaker, frame=fr, axis=axis, base=base, zmin=zmin, zmax=zmax)
    return shell, parts, pads, info


# ---------------------------------------------------------------- checks
def _cls(shape):
    def state(p):
        c = BRepClass3d_SolidClassifier(shape.wrapped)
        c.Perform(gp_Pnt(*p), 1e-6)
        return str(c.State()).split("_")[-1]
    return state


def grown(name, solid, d):
    bb = solid.BoundingBox()
    return cq.Solid.makeBox(bb.xlen + 2 * d, bb.ylen + 2 * d, bb.zlen + 2 * d,
                            cq.Vector(bb.xmin - d, bb.ymin - d, bb.zmin - d))


def check_bud(shell, parts, pads, info):
    res = []
    names = list(parts)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = parts[a][0].intersect(parts[b][0]).Volume()
            if v > 1e-3:
                res.append((f"overlap {a}/{b}", False, f"{v:.3f} mm3"))
    res.append(("no part overlaps another", not any(not ok for _, ok, _ in res), ""))
    worst = []
    for n, (s, _, _) in parts.items():
        if n == "magnet":
            # sits against the -Y wall on purpose; check it doesn't penetrate
            v = s.intersect(shell).Volume()
            res.append((f"{n} does not penetrate wall", v < 1e-3, f"{v:.3f} mm3"))
            continue
        # cylinders: grow the cylinder itself, not its bbox
        if n in ("battery", "speaker"):
            bb = s.BoundingBox()
            g = cq.Solid.makeCylinder(bb.xlen / 2 + CHECK_CLR, bb.zlen + 2 * CHECK_CLR,
                                      cq.Vector((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, bb.zmin - CHECK_CLR))
        else:
            g = grown(n, s, CHECK_CLR)
        v = g.intersect(shell).Volume()
        worst.append((n, v))
        res.append((f"{n}: >= {CHECK_CLR} mm to wall", v < 1e-3, f"{v:.3f} mm3 intrusion"))
    # sound path open: points along the nozzle axis from the tip back into the cavity
    st = _cls(shell)
    a, base = info["axis"], info["base"]
    open_path = all(st((base + a * s).toTuple()) == "OUT" for s in np.linspace(-(WALL + Z_EXTRA + CLR * 0.4), nz.NOZZLE_LEN - 0.1, 30))
    res.append(("nozzle bore open to the cavity", open_path, ""))
    # sealed: no other opening on the ear side (bottom) other than the bore
    res.append(("pads present", all(p.Volume() > 0.05 for p in pads), ""))
    return res


def bud_envelope(shell):
    bb = shell.BoundingBox()
    return bb.xlen, bb.ylen, bb.zlen


# ---------------------------------------------------------------- case
CASE_WALL = 1.5
POGO = dict(d=1.5, h=4.0)
CASE_BAT = (30.0, 5.0, 20.0)   # 502030 LiPo (x, thickness, y): lies flat behind the buds
CASE_PCB = (25.0, 1.0, 20.0)   # 25 x 20 board (x, thickness, y), stacked on the battery
USBC = (9.0, 7.3, 3.2)


def _place_in_case(shape, right):
    """Bud frame -> case frame. The pad face (-X; +X once mirrored) goes down."""
    s = shape.mirror("YZ") if right else shape
    return s.rotate((0, 0, 0), (0, 1, 0), 90 if right else -90)


def build_case(bud_shell, bud_pads, parts):
    gap = 2.0
    buds, pogos = [], {}
    for right in (False, True):
        sh = _place_in_case(bud_shell, right)
        pads = [_place_in_case(p, right) for p in bud_pads]
        bb = sh.BoundingBox()
        dx = (gap / 2 - bb.xmin) if right else (-gap / 2 - bb.xmax)
        mv = cq.Vector(dx, -bb.ymin, -bb.zmin)
        sh = sh.translate(mv)
        buds.append(sh)
        for k, p in enumerate(pads):
            pb = p.translate(mv).BoundingBox()
            pogos[f"pogo_{'R' if right else 'L'}{k}"] = cq.Solid.makeCylinder(
                POGO["d"] / 2, POGO["h"], cq.Vector((pb.xmin + pb.xmax) / 2, (pb.ymin + pb.ymax) / 2, pb.zmin - 0.2 - POGO["h"]),
                cq.Vector(0, 0, 1))
    floor_z = min(p.BoundingBox().zmin for p in pogos.values())
    budbb = buds[0].BoundingBox().add(buds[1].BoundingBox())
    # battery flat on the floor behind the buds, case PCB stacked on it, USB-C out the back
    by = budbb.ymax + 1.0
    items = dict(pogos)
    items["case_battery"] = box(0, by + CASE_BAT[2] / 2, floor_z + CASE_BAT[1] / 2, CASE_BAT[0], CASE_BAT[2], CASE_BAT[1])
    pz = floor_z + CASE_BAT[1] + 0.5
    items["case_pcb"] = box(0, by + CASE_PCB[2] / 2, pz + CASE_PCB[1] / 2, CASE_PCB[0], CASE_PCB[2], CASE_PCB[1])
    items["usb_c"] = box(0, by + CASE_PCB[2] - USBC[1] / 2 + 1.0, pz + CASE_PCB[1] + USBC[2] / 2, USBC[0], USBC[1], USBC[2])
    allbb = budbb
    for s_ in items.values():
        allbb = allbb.add(s_.BoundingBox())
    c = 0.8
    ox, oy, oz = allbb.xmin - c - CASE_WALL, allbb.ymin - c - CASE_WALL, allbb.zmin - c - CASE_WALL
    sx, sy, sz = allbb.xlen + 2 * (c + CASE_WALL), allbb.ylen + 2 * (c + CASE_WALL), allbb.zlen + 2 * (c + CASE_WALL)
    outer = cq.Workplane().box(sx, sy, sz, centered=False).translate((ox, oy, oz)).edges().fillet(4.0).val()
    inner = cq.Workplane().box(sx - 2 * CASE_WALL, sy - 2 * CASE_WALL, sz - 2 * CASE_WALL, centered=False) \
        .translate((ox + CASE_WALL, oy + CASE_WALL, oz + CASE_WALL)).edges().fillet(1.5).val()
    shell = outer.cut(inner)
    ub = items["usb_c"].BoundingBox()
    shell = shell.cut(cq.Solid.makeBox(ub.xlen + 0.6, 6.0, ub.zlen + 0.6, cq.Vector(ub.xmin - 0.3, ub.ymin, ub.zmin - 0.3)))
    split_z = oz + sz * 0.6
    cutter_top = cq.Solid.makeBox(sx + 2, sy + 2, sz, cq.Vector(ox - 1, oy - 1, split_z))
    lid = shell.intersect(cutter_top)
    base = shell.cut(cutter_top)
    return dict(base=base, lid=lid, buds=buds, items=items, env=(sx, sy, sz))


def check_case(case):
    res = []
    objs = {f"bud_{i}": b for i, b in enumerate(case["buds"])}
    objs.update(case["items"])
    names = list(objs)
    bad = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = objs[a].intersect(objs[b]).Volume()
            if v > 1e-3:
                bad.append(f"{a}/{b} {v:.2f}")
    res.append(("no case part overlaps another", not bad, "; ".join(bad)))
    shell = case["base"].fuse(case["lid"])
    for n, s in objs.items():
        if n == "usb_c":
            continue
        v = grown(n, s, CHECK_CLR).intersect(shell).Volume() if not n.startswith("bud") else s.intersect(shell).Volume()
        res.append((f"{n} clear of case walls", v < 1e-3, f"{v:.3f} mm3"))
    return res


# ---------------------------------------------------------------- rendering
COLORS = dict(speaker="#6b7a8f", battery="#c9a227", bottom_parts="#3c8d5a", pcb="#2e6b3f",
              module="#8a8f96", mic="#b04a3a", magnet="#555555")


def _mesh(ax, shape, color, alpha=1.0, lw=0.03):
    verts, tris = shape.tessellate(0.05, 0.3)
    V = np.array([v.toTuple() for v in verts]); T = np.array(tris)
    ax.add_collection3d(Poly3DCollection(V[T], facecolor=color, edgecolor="#333333", linewidths=lw, alpha=alpha))
    return V


def _frame(ax, pts):
    pts = np.vstack(pts)
    c = (pts.max(0) + pts.min(0)) / 2; r = (pts.max(0) - pts.min(0)).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")


def render_bud(shell, parts, pads, path, title, explode=0.0, cutaway=True):
    fig = plt.figure(figsize=(7, 7)); ax = fig.add_subplot(111, projection="3d")
    pts = []
    s = shell
    if cutaway:
        bb = s.BoundingBox()
        s = s.cut(cq.Solid.makeBox(bb.xlen + 2, bb.ylen + 2, bb.zlen + 2, cq.Vector(bb.xmin - 1, bb.ymin - 1, bb.zmin - 1)).translate(cq.Vector(-(bb.xmin - 1), 0, 0)))
    pts.append(_mesh(ax, s, "#d9dee2", alpha=0.35 if not cutaway else 0.9))
    order = ["speaker", "battery", "bottom_parts", "pcb", "module", "mic", "magnet"]
    for i, n in enumerate(order):
        sol = parts[n][0].translate(cq.Vector(0, 0, explode * i))
        pts.append(_mesh(ax, sol, COLORS[n]))
    for p in pads:
        pts.append(_mesh(ax, p, "#d4af37"))
    _frame(ax, pts); ax.view_init(elev=18, azim=-58)
    fig.suptitle(title, fontsize=10); fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def _section_lines(shape, x=0.0):
    sec = BRepAlgoAPI_Section(shape.wrapped, gp_Pln(gp_Pnt(x, 0, 0), gp_Dir(1, 0, 0)))
    sec.Build()
    lines = []
    for e in cq.Shape.cast(sec.Shape()).Edges():
        pts = [e.positionAt(t) for t in np.linspace(0, 1, 40)]
        lines.append(np.array([(p.y, p.z) for p in pts]))
    return lines


def render_section(shell, parts, info, path, title):
    fig, ax = plt.subplots(figsize=(7, 7))
    for l in _section_lines(shell):
        ax.plot(l[:, 0], l[:, 1], color="black", lw=1.2)
    for n, (s, _, _) in parts.items():
        for l in _section_lines(s, x=0.0 if n != "mic" else s.BoundingBox().center.x):
            ax.plot(l[:, 0], l[:, 1], color=COLORS[n], lw=1.0)
    a, b = info["axis"], info["base"]
    p0, p1 = b - a * 3, b + a * (nz.NOZZLE_LEN + 1)
    ax.plot([p0.y, p1.y], [p0.z, p1.z], "r--", lw=0.8, label="nozzle axis")
    for n, c in COLORS.items():
        ax.plot([], [], color=c, label=n)
    ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.set_xlabel("y (mm)"); ax.set_ylabel("z (mm)")
    ax.legend(fontsize=7, loc="upper left"); ax.set_title(title, fontsize=10)
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)


def render_case(case, path, title):
    fig = plt.figure(figsize=(8, 7)); ax = fig.add_subplot(111, projection="3d")
    pts = [_mesh(ax, case["base"], "#cfd6dc", alpha=0.25), _mesh(ax, case["lid"].translate(cq.Vector(0, 0, 12)), "#cfd6dc", alpha=0.18)]
    for b in case["buds"]:
        pts.append(_mesh(ax, b, "#eef1f3"))
    col = dict(case_battery="#c9a227", case_pcb="#2e6b3f", usb_c="#8a8f96")
    for n, s in case["items"].items():
        pts.append(_mesh(ax, s, col.get(n, "#d4af37")))
    _frame(ax, pts); ax.view_init(elev=24, azim=-60)
    fig.suptitle(title, fontsize=10); fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


# ---------------------------------------------------------------- main
def export(shape, stem):
    cq.exporters.export(shape, os.path.join(HERE, stem + ".step"))
    cq.exporters.export(shape, os.path.join(HERE, stem + ".stl"), tolerance=0.02, angularTolerance=0.15)


def main():
    lines = ["# Rev B fit study results (generated)", ""]
    allok = True
    envs = {}
    for variant in VARIANTS:
        for spk in SPEAKERS:
            if spk != SPEAKER:
                envs[(variant, spk)] = build_bud(variant, spk, envelope_only=True)
                continue
            print(f"building {variant}/{spk}", flush=True)
            shell, parts, pads, info = build_bud(variant, spk)
            envs[(variant, spk)] = bud_envelope(shell)
            print("  checking", flush=True)
            res = check_bud(shell, parts, pads, info)
            lines += [f"## Bud, {VARIANTS[variant]['label']}, speaker {spk}", ""]
            for name, ok, detail in res:
                lines.append(f"- {'PASS' if ok else 'FAIL'}: {name} {detail}".rstrip())
                allok &= ok
            lines.append("")
            print("  exporting + rendering", flush=True)
            stem = f"bud_{variant}"
            export(shell, stem)
            asm = cq.Compound.makeCompound([shell] + [p[0] for p in parts.values()] + pads)
            export(asm, stem + "_assembly")
            label = VARIANTS[variant]["label"]
            render_bud(shell, parts, pads, os.path.join(HERE, f"preview_{stem}_iso.png"), f"Rev B bud, {label} (cutaway)")
            render_bud(shell, parts, pads, os.path.join(HERE, f"preview_{stem}_exploded.png"), f"Rev B bud, {label} (exploded)", explode=4.0, cutaway=False)
            render_section(shell, parts, info, os.path.join(HERE, f"preview_{stem}_section.png"), f"Section x=0, {label}")
            if variant == "mdbt53v":
                print("  case", flush=True)
                case = build_case(shell, pads, parts)
                cres = check_case(case)
                lines += ["## Charging case (holds two MDBT53V buds)", ""]
                for name, ok, detail in cres:
                    lines.append(f"- {'PASS' if ok else 'FAIL'}: {name} {detail}".rstrip())
                    allok &= ok
                sx, sy, sz = case["env"]
                lines += ["", f"Case envelope: {sx:.1f} x {sy:.1f} x {sz:.1f} mm (x, y, z)", ""]
                export(case["base"], "case_base"); export(case["lid"], "case_lid")
                asm = cq.Compound.makeCompound([case["base"], case["lid"]] + case["buds"] + list(case["items"].values()))
                export(asm, "case_assembly")
                render_case(case, os.path.join(HERE, "preview_case_iso.png"), "Rev B charging case concept (lid raised)")
    lines += ["## Bud envelopes (x, y, z incl. nozzle, mm)", "", "| Variant | Speaker | Envelope | Volume of box |", "|---|---|---|---|"]
    for (v, s), (x, y, z) in envs.items():
        lines.append(f"| {VARIANTS[v]['label']} | {s} | {x:.1f} x {y:.1f} x {z:.1f} | {x*y*z/1000:.1f} cm3 |")
    for n, (x, y, z) in REF.items():
        lines.append(f"| {n} | — | {x:.1f} x {y:.1f} x {z:.1f} | {x*y*z/1000:.1f} cm3 |")
    lines += ["", f"All checks pass: {allok}"]
    open(os.path.join(HERE, "results.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
