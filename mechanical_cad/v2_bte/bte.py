"""Haven v2 behind-the-ear (BTE) mechanics: in-ear unit, behind-ear pod, board outlines.

Builds on ../v2_form_concepts (bte_inear / bte_pod) with the same shell construction (parts'
signed distance fields offset by clearance + wall, closed, smoothed, hollowed; exact nozzle,
bore, mic port and pad holes). Changes from the concept:
  - In-ear unit: the 6 x 6 mm board carries the SPH0641 mic (port lateral) and the cable/driver
    pads; the cable leaves through a tapered strain-relief boot with a 1.5 mm cable hole.
  - Pod: one large flat board (13 x 27 mm) instead of 9 x 13. CP1454 sits on the board's lateral
    face at the bottom; the MDBT53V-1M sits on the lateral face at the top with its antenna end
    flush with the top edge (away from the battery and head); codec, PMIC and passives go on the
    medial (head) face, <= 1.0 mm tall. Charging pads + magnet on the bottom end (case-facing).
    The cable enters the pod's upper anterior face, toward the helix root.
Frames. In-ear unit: origin = canal entrance, X anterior, Y superior, Z lateral (right ear).
Pod: X toward the pinna (anterior), Y along the pod (up), Z lateral (away from the scalp).
Left-ear parts are the right-ear parts mirrored x -> -x.

    python3 -I bte.py        -> STL/STEP shells, parts_*/, board DXFs, geometry.json
"""
import json
import os
import sys

import ezdxf
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
FORM = os.path.normpath(os.path.join(HERE, "..", "v2_form_concepts"))
ERGO = os.path.normpath(os.path.join(HERE, "..", "v2_ergonomic_shell"))
sys.path[:0] = [FORM, ERGO]
import concepts as cc  # noqa: E402
import generate_v2_ergonomic_shell as gen  # noqa: E402
from concepts import Box, Cyl, X_, Y_, Z_, unit  # noqa: E402

GAP = cc.GAP
CABLE_HOLE_D = 1.7                            # 1.5 mm OD harness + 0.2 mm
# Ole Wolff OWR-0860T-16: datasheet size 9.0 x 4.5 mm (dia x H), 16 ohm (mass estimated)
DRV = (9.0, 4.5, 0.6)

# ---------------------------------------------------------------- in-ear unit
INEAR_BOARD = (6.0, 6.0, 0.6)
CABLE_DIR = unit([-0.35, 1.0, 0.25])          # up and back toward the helix root


# Variant A (primary): speaker + mic on a 6 x 6 mm board, 6-wire ~1.5 mm OD cable.
# Variant B (fallback): speaker only, 2-wire ~1.0-1.2 mm OD cable, no board, no mic port.
CABLE_HOLE = dict(A=1.7, B=1.4)


def inear_parts(variant="A"):
    drv = cc.driver(DRV)
    Rh = cc.head_plane_R(cc.OUT)
    back = cc.FRONT - gen.N_IN * DRV[1]
    if variant == "A":
        board = Box("board", back + cc.OUT * (GAP + 0.3), INEAR_BOARD, Rh, 0.03)
        mic = Box("mic", back + cc.OUT * (GAP + 0.6 + cc.MIC[2] / 2), cc.MIC, Rh, 0.02)
        boot_base = back + cc.OUT * 2.3 + Y_ * 3.0
        boot = Cyl("cable_boot", boot_base, CABLE_DIR, 2.4, 5.0, 0.05)
        parts = [drv, board, mic, boot]
        kw = dict(nozzle_B=cc.B, mic=(mic.c, cc.OUT), pads=None)
        blen = 5.0
    else:
        boot_base = back + cc.OUT * 2.1 + Y_ * 3.0
        boot = Cyl("cable_boot", boot_base, CABLE_DIR, 2.0, 4.0, 0.04)
        parts = [drv, boot]
        kw = dict(nozzle_B=cc.B, mic=None, pads=None)
        blen = 4.0
    exit_pt = boot_base + CABLE_DIR * (blen + cc.CLR + cc.WALL)
    return parts, kw, dict(cable_exit=exit_pt, cable_dir=CABLE_DIR, cable_base=boot_base)


# ---------------------------------------------------------------- pod
POD_BOARD = (13.0, 27.0, 0.8)                 # X width, Y length, thickness
MEDIAL_H = 1.0                                # max component height on the head side
CABLE_IN = np.array([POD_BOARD[0] / 2 - 0.4, 4.0, 1.4])
CABLE_IN_DIR = unit([0.55, 1.0, 0.1])         # out of the upper anterior face, up toward the helix root
MOD_X = 0.8                                   # module shifted toward the pinna to free a strip for the mic port
POD_MIC_XY = (-4.9, 7.0)                      # optional pod mic: posterior strip, away from the head and the cable boot
MIC_TUBE_R, MIC_HOLE_D, GASKET_T = 1.2, 1.0, 0.5


def pod_parts():
    W, L, T = POD_BOARD
    pcb = Box("pcb", [0, 0, 0], [W, L, T], np.eye(3), 0.30)
    bottom = Box("bottom_parts", [0, 0, -(T / 2 + MEDIAL_H / 2)], [W - 0.6, L - 0.6, MEDIAL_H], np.eye(3), 0.15)
    mod_h = cc.MODULE[2]
    mod = Box("module", [MOD_X, L / 2 - cc.MODULE[0] / 2, T / 2 + mod_h / 2], [cc.MODULE[1], cc.MODULE[0], mod_h], np.eye(3), 0.4)
    # bottom-port SPH0641 on the head-side face, port up through a board hole into the shell's channel
    pmic = Box("pod_mic", [POD_MIC_XY[0], POD_MIC_XY[1], -(T / 2 + cc.MIC[2] / 2)], [cc.MIC[1], cc.MIC[0], cc.MIC[2]], np.eye(3), 0.02)
    bat_cy = -L / 2 + cc.CP1454[0] / 2
    bat = Cyl("battery", [0, bat_cy, T / 2 + 0.25], Z_, cc.CP1454[0], cc.CP1454[1], cc.CP1454[2])
    end = np.array([0.0, -L / 2 - GAP, -0.2])
    mag = Cyl("magnet", end - Y_ * 0.1, -Y_, cc.MAG[0], cc.MAG[1], cc.MAG[2])
    boot = Cyl("cable_boot", CABLE_IN, CABLE_IN_DIR, 2.4, 3.5, 0.05)
    parts = [pcb, bottom, mod, bat, mag, boot, pmic]
    kw = dict(nozzle_B=None, mic=None, pads=(end - Y_ * 0.1, -Y_, X_))
    return parts, kw, dict(cable_entry=CABLE_IN + CABLE_IN_DIR * (3.5 + cc.CLR + cc.WALL), cable_dir=CABLE_IN_DIR,
                           bat_center_y=bat_cy)


# ---------------------------------------------------------------- shell with a cable hole
def shell_with_hole(parts, kw, hole_base, hole_dir, hole_len=14.0, hole_d=CABLE_HOLE_D, mic_channel=None):
    for shift in (0.0, 0.07, 0.13):
        fd = cc.build_shell(parts, shift=shift, **kw)
        G = np.stack(np.meshgrid(*fd["axes"], indexing="ij"), -1).astype(np.float32)
        fd["field"] = np.maximum(fd["field"], -gen.sd_cyl(G, hole_base, hole_dir, hole_d / 2, hole_len))
        if mic_channel is not None:
            # solid tube from the outer wall down to a gasket seat GASKET_T above the board, kept inside the body,
            # with a MIC_HOLE_D acoustic hole through it
            base = np.asarray(mic_channel, float)
            tube = np.maximum(gen.sd_cyl(G, base, Z_, MIC_TUBE_R, 20.0), fd["body_sd"])
            fd["field"] = np.minimum(fd["field"], tube)
            fd["field"] = np.maximum(fd["field"], -gen.sd_cyl(G, base - Z_ * 0.01, Z_, MIC_HOLE_D / 2, 20.0))
        del G
        mesh = gen.mesh_from_field(fd["field"], fd["axes"])
        if mesh.is_watertight:
            break
    return mesh, fd


def mirror_x(mesh):
    m = mesh.copy()
    m.apply_transform(np.diag([-1.0, 1, 1, 1]))
    m.invert()
    return m


# ---------------------------------------------------------------- board outlines (DXF)
def rounded_rect(msp, w, h, r, layer):
    x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
    msp.add_line((x0 + r, y0), (x1 - r, y0), dxfattribs=dict(layer=layer))
    msp.add_line((x1, y0 + r), (x1, y1 - r), dxfattribs=dict(layer=layer))
    msp.add_line((x1 - r, y1), (x0 + r, y1), dxfattribs=dict(layer=layer))
    msp.add_line((x0, y1 - r), (x0, y0 + r), dxfattribs=dict(layer=layer))
    for (cx, cy, a0) in ((x1 - r, y0 + r, 270), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        msp.add_arc((cx, cy), r, a0, a0 + 90, dxfattribs=dict(layer=layer))


def rect(msp, cx, cy, w, h, layer):
    pts = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2), (cx - w / 2, cy - h / 2)]
    msp.add_lwpolyline(pts, dxfattribs=dict(layer=layer))


def pod_dxf(path, bat_cy):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    for name in ("Edge.Cuts", "KEEPOUT_TOP_BATTERY", "KEEPOUT_TOP_MODULE", "ANTENNA_EDGE", "MIC_PORT_HOLE", "KEEPOUT_TOP_GASKET",
                 "BOTTOM_POD_MIC", "NOTES"):
        doc.layers.add(name)
    msp = doc.modelspace()
    W, L, _ = POD_BOARD
    rounded_rect(msp, W, L, 1.5, "Edge.Cuts")
    msp.add_circle((0, bat_cy), cc.CP1454[0] / 2, dxfattribs=dict(layer="KEEPOUT_TOP_BATTERY"))
    rect(msp, MOD_X, L / 2 - cc.MODULE[0] / 2, cc.MODULE[1], cc.MODULE[0], "KEEPOUT_TOP_MODULE")
    msp.add_circle(POD_MIC_XY, MIC_HOLE_D / 2, dxfattribs=dict(layer="MIC_PORT_HOLE"))
    msp.add_circle(POD_MIC_XY, MIC_TUBE_R + 0.2, dxfattribs=dict(layer="KEEPOUT_TOP_GASKET"))
    rect(msp, POD_MIC_XY[0], POD_MIC_XY[1], cc.MIC[1], cc.MIC[0], "BOTTOM_POD_MIC")
    msp.add_line((-W / 2, L / 2), (W / 2, L / 2), dxfattribs=dict(layer="ANTENNA_EDGE"))
    notes = ["Haven v2 BTE pod board, 13 x 27 mm, origin = board centre, +Y = up (antenna end).",
             "Top (lateral) face: CP1454 in the battery circle (tabs only under it); MDBT53V-1M in its rectangle,",
             "antenna end flush with the top edge; other top parts <= 1.85 mm outside the battery circle.",
             "Bottom (head) face: all other parts, <= 1.0 mm. Charging pads + magnet are in the shell below the bottom edge.",
             "Check the antenna keep-out against Raytac MDBT53V-1M spec Ver.D p.9 during layout.",
             "Optional pod mic (SPH0641, bottom port) on the BOTTOM face under MIC_PORT_HOLE (1.0 mm through-hole);",
             "keep the top face clear inside KEEPOUT_TOP_GASKET (shell tube + 0.5 mm foam gasket seat on the board)."]
    for i, t in enumerate(notes):
        msp.add_text(t, height=0.6, dxfattribs=dict(layer="NOTES")).set_placement((W / 2 + 2, L / 2 - i * 1.2))
    doc.saveas(path)


def inear_dxf(path):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    for name in ("Edge.Cuts", "KEEPOUT_TOP_MIC", "NOTES"):
        doc.layers.add(name)
    msp = doc.modelspace()
    rounded_rect(msp, INEAR_BOARD[0], INEAR_BOARD[1], 0.8, "Edge.Cuts")
    rect(msp, 0, 0, cc.MIC[0], cc.MIC[1], "KEEPOUT_TOP_MIC")
    notes = ["Haven v2 BTE in-ear board, 6 x 6 mm, 0.6 mm thick, origin = centre.",
             "Top (lateral) face: SPH0641LU4H-1, aligned with the shell's mic hole. Confirm the port side in the",
             "Knowles datasheet: if it is bottom-port, add a 0.6-0.8 mm acoustic hole through the board under the port.",
             "Bottom (driver) face: driver solder pads SPK+/SPK-. Edge toward the cable boot: 6 cable pads",
             "(SPK+, SPK-, MIC_VDD, GND, PDM_CLK, PDM_DATA). Component height <= 1.0 mm on the top face."]
    for i, t in enumerate(notes):
        msp.add_text(t, height=0.4, dxfattribs=dict(layer="NOTES")).set_placement((4.0, 3.0 - i * 0.8))
    doc.saveas(path)


# ---------------------------------------------------------------- main
def export_parts(parts, fd, d):
    os.makedirs(d, exist_ok=True)
    cc.export_parts(parts, fd, d)


def report(tag, mesh, fd, parts, tip):
    gp = cc.min_gap(parts, cc.STACKED | {frozenset(p) for p in [("board", "mic"), ("board", "cable_boot"), ("mic", "cable_boot"),
                                                                ("pcb", "bottom_parts"), ("pcb", "module"), ("pcb", "battery"),
                                                                ("bottom_parts", "module"), ("bottom_parts", "battery"),
                                                                ("pcb", "cable_boot"), ("pcb", "pod_mic"), ("bottom_parts", "pod_mic")]})
    rep = dict(bbox_mm=[round(float(x), 2) for x in mesh.extents], watertight=bool(mesh.is_watertight),
               min_part_gap=[round(gp[0], 3), gp[1]], checks=cc.clearances(fd, parts), **cc.mass_props(mesh, parts, tip=tip))
    print(tag, json.dumps(rep), flush=True)
    return rep


def main():
    geo = {}
    for v in ("A", "B"):
        parts, kw, info = inear_parts(v)
        mesh, fd = shell_with_hole(parts, kw, info["cable_base"], info["cable_dir"], hole_d=CABLE_HOLE[v])
        geo[f"inear_{v}"] = dict(report(f"inear_{v}", mesh, fd, parts, True), cable_exit=info["cable_exit"].round(3).tolist(),
                                 cable_dir=info["cable_dir"].round(4).tolist(), cable_hole_d=CABLE_HOLE[v])
        mesh.export(os.path.join(HERE, f"bte_inear_{v}_R.stl")); mirror_x(mesh).export(os.path.join(HERE, f"bte_inear_{v}_L.stl"))
        gen.mesh_to_step(mesh, os.path.join(HERE, f"bte_inear_{v}_R.step")); gen.mesh_to_step(mirror_x(mesh), os.path.join(HERE, f"bte_inear_{v}_L.step"))
        export_parts(parts, fd, os.path.join(HERE, f"parts_inear_{v}"))
    inear_dxf(os.path.join(HERE, "board_inear_outline.dxf"))

    parts, kw, info = pod_parts()
    base = CABLE_IN
    mesh, fd = shell_with_hole(parts, kw, base, CABLE_IN_DIR,
                               mic_channel=[POD_MIC_XY[0], POD_MIC_XY[1], POD_BOARD[2] / 2 + GASKET_T])
    geo["pod"] = dict(report("pod", mesh, fd, parts, False), cable_entry=info["cable_entry"].round(3).tolist(),
                      cable_dir=CABLE_IN_DIR.round(4).tolist(), board_mm=list(POD_BOARD),
                      battery_life=cc.hours(85, 120), pod_mic_xy=list(POD_MIC_XY), module_x=MOD_X)
    mesh.export(os.path.join(HERE, "bte_pod_R.stl")); mirror_x(mesh).export(os.path.join(HERE, "bte_pod_L.stl"))
    gen.mesh_to_step(mesh, os.path.join(HERE, "bte_pod_R.step")); gen.mesh_to_step(mirror_x(mesh), os.path.join(HERE, "bte_pod_L.step"))
    export_parts(parts, fd, os.path.join(HERE, "parts_pod"))
    pod_dxf(os.path.join(HERE, "board_pod_outline.dxf"), info["bat_center_y"])
    json.dump(geo, open(os.path.join(HERE, "geometry.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
