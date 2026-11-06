"""Haven v2 BTE charging case: base, lid, bottom plate and the case board outline.

Layout (case frame: X across, Y front(-) to back(+), Z up, origin = centre of the floor top):
  - Two pod wells at the back, pods standing upright (pod +Y = case +Z), their thin axis across the
    case. Each well is the pod's own lower envelope dropped straight down, plus CLR, so the pod
    seats on its rounded bottom and its two charge contacts land on two spring pins (5.0 mm apart,
    around a 3 mm magnet) coming up through the floor.
  - A pocket at the front for the two in-ear units (ear tips on); the 55 mm cables loop from the
    pods' top-front cable boots down into it, under the lid.
  - Electronics bay under the floor: case board (USB-C at the back wall) + ~800 mAh LiPo
    (603040 class, 6 x 30 x 40 mm). Closed by a bottom plate.
  - Lid: a cap that slides over the base's upper lip (friction fit; magnets can come later).
Pod contacts are assumed flush with the pod shell (brass pins 1.5 x 3.5 mm; see README).

    python3 case.py   -> case_base.stl, case_lid.stl, case_plate.stl, board_case_outline.dxf, case.json
"""
import json
import os

import ezdxf
import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
VOX = 0.2
CLR = 0.35            # pod-to-well clearance
WALL = 1.8
# Spring pin working height (board top -> pod contact, pin partly compressed). Candidate pin:
# Kinghelm KH-PG2011005-DZ (LCSC C2842935), SMD, 11 mm free, 2 mm base; its stroke isn't
# published on LCSC, so 10.0 assumes ~1 mm of compression. Measure the real pin and change this.
POGO_WORK_H = 10.0
CONTACT_Z = 0.35 + 0.3  # pod contact face above the floor top: CLR + contact column height over the pod's lowest point
BOARD_T = 1.0
FLOOR = 1.6           # floor between the wells and the electronics bay
BAY_H = POGO_WORK_H - CONTACT_Z + BOARD_T - FLOOR   # board lies on the plate; its top is POGO_WORK_H below the contacts
PLATE = 1.4
WELL_DEPTH = 14.0     # how far up the pod the well grips
POD_GAP = 3.0         # wall between the two wells
TRAY = (44.0, 25.5, 12.0)   # in-ear pocket: across, front-back, depth
LID_CLEAR = 3.0       # above the pod tops
LIP = 3.0             # height of the lid's overlap on the base
LID_T = 1.6
LID_FIT = 0.15        # per side, lid over the base lip (friction fit)
POD_MAG = (3.0, 2.0)  # matches the pod's magnet
POGO_PITCH = 5.0
POGO_HOLE = 1.6
USB_C = (9.2, 3.4)    # receptacle opening, w x h
USB_X = -2.0          # matches J1 on the case board (gen_v2_case_pcb.py)
LED_X = -8.8          # charge LED D2 at the board's back edge
LED_HOLE = 1.5


def pod_in_case(mirror):
    m = trimesh.load(os.path.join(HERE, "bte_pod_R.stl"))
    if mirror:
        m.apply_transform(np.diag([-1.0, 1, 1, 1])); m.invert()
    # case X = pod Z (thin), case Y = pod X (toward the pinna -> back of the case), case Z = pod Y (up)
    P = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]])
    m.apply_transform(P)
    return m


def heightmap(m, xs, ys):
    """Lowest pod surface z over each (x, y) column; +inf where the column misses the pod."""
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    o = np.c_[X.ravel(), Y.ravel(), np.full(X.size, m.bounds[0][2] - 5)]
    d = np.tile([0, 0, 1.0], (len(o), 1))
    loc, idx, _ = m.ray.intersects_location(o, d, multiple_hits=False)
    z = np.full(X.size, np.inf)
    z[idx] = loc[:, 2]
    return z.reshape(X.shape)


def rbox(G, c, size, r):
    r = min(r, min(size) / 2 - 1e-3)                 # a radius larger than the half-thickness breaks the SDF
    q = np.abs(G - np.asarray(c)) - (np.asarray(size) / 2 - r)
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(-1), 0) - r


def cyl_z(G, c, r, z0, z1):
    d = np.hypot(G[..., 0] - c[0], G[..., 1] - c[1]) - r
    return np.maximum(d, np.maximum(z0 - G[..., 2], G[..., 2] - z1))


def mesh(field, axes):
    v, f, _, _ = measure.marching_cubes(field, 0.0, spacing=(VOX, VOX, VOX))
    v += [a[0] for a in axes]
    m = trimesh.Trimesh(v, f, process=True)
    if m.volume < 0:
        m.invert()
    return m


def main():
    pods = []
    for side, mirror in (("R", False), ("L", True)):
        m = pod_in_case(mirror)
        pods.append((side, m))
    w = pods[0][1].extents                       # across, front-back, height
    # place: pods side by side at the back, bottoms on z = 0 (floor top), contacts centred over x
    xoff = {"R": (w[0] + POD_GAP) / 2, "L": -(w[0] + POD_GAP) / 2}
    inner_y = w[1] + TRAY[1] + 2.0
    y_pods = inner_y / 2 - w[1] / 2 - 0.5
    placed = {}
    for side, m in pods:
        c = m.bounds.mean(0)
        t = np.array([xoff[side] - c[0], y_pods - c[1], -m.bounds[0][2] + CLR])
        m.apply_transform(trimesh.transformations.translation_matrix(t))
        placed[side] = m
    trimesh.util.concatenate([m.simplify_quadric_decimation(face_count=40000) for m in placed.values()]).export(
        os.path.join(HERE, "case_preview_pods.stl"))                  # preview only
    inner_x = max(2 * w[0] + POD_GAP + 1.0, TRAY[0] + 1.0, 32.0)
    pod_top = max(m.bounds[1][2] for m in placed.values())
    outer = np.array([inner_x + 2 * WALL, inner_y + 2 * WALL])
    z_bot = -(FLOOR + BAY_H + PLATE)
    base_top = WELL_DEPTH + 2.0                   # base rim height above the floor
    lid_top = pod_top + LID_CLEAR + LID_T

    lo = np.array([-outer[0] / 2 - 2, -outer[1] / 2 - 2, z_bot - 2])
    hi = np.array([outer[0] / 2 + 2, outer[1] / 2 + 2, lid_top + 2])
    # offset the grid off round numbers so flat faces never sit exactly on a voxel plane
    axes = [np.arange(lo[i] + 0.0371, hi[i] + VOX, VOX) for i in range(3)]
    G = np.stack(np.meshgrid(*axes, indexing="ij"), -1).astype(np.float32)

    # ---- base: solid block from the plate's top up to base_top; its top LIP mm are inset by the
    # lid wall + LID_FIT so the lid slides over them (friction fit)
    low_h = (base_top - LIP) - (z_bot + PLATE)
    base = rbox(G, [0, 0, z_bot + PLATE + low_h / 2], [outer[0], outer[1], low_h], 3.0)
    ins = 2 * (LID_T + LID_FIT)
    upper = rbox(G, [0, 0, base_top - LIP / 2 - 0.25], [outer[0] - ins, outer[1] - ins, LIP + 0.5], 3.0 - LID_T)
    base = np.minimum(base, upper)

    # pod wells: drop each pod's lower envelope straight down
    xs, ys = axes[0], axes[1]
    for side, m in placed.items():
        hz = heightmap(m, xs, ys)
        foot = np.isfinite(hz)
        dist_out = ndimage.distance_transform_edt(~foot) * VOX
        hz_f = np.where(foot, hz, 1e3)
        hz_d = ndimage.grey_erosion(hz_f, size=(int(2 * CLR / VOX) + 3,) * 2)   # lowest nearby surface
        well = np.maximum(dist_out[:, :, None] - CLR, (hz_d[:, :, None] - CLR) - G[..., 2])
        well = np.minimum(well, 50.0)
        well = np.maximum(well, G[..., 2] - (base_top + 1))          # open to the top
        base = np.maximum(base, -well)
    # in-ear tray at the front
    ty = -inner_y / 2 + TRAY[1] / 2
    base = np.maximum(base, -rbox(G, [0, ty, base_top - TRAY[2] / 2 + 1], [TRAY[0], TRAY[1], TRAY[2] + 2], 4.0))
    # electronics bay under the floor (open at the bottom, closed by the plate)
    bay = rbox(G, [0, 0, -FLOOR - BAY_H / 2 - 0.5], [inner_x, inner_y, BAY_H + 1.0], 1.5)
    base = np.maximum(base, -bay)
    # pogo holes + pod magnet pockets (from below, under each pod's contacts)
    contacts = {}
    # contact columns: lowest point of each pod lies between its contacts (measured), so take the
    # pod's lowest vertex as the magnet centre and +-2.5 mm along the case Y axis (pod X) for the pins
    pins = []
    for side, m in placed.items():
        v = m.vertices[m.vertices[:, 2].argmin()]
        mc = np.array([v[0], v[1]])
        contacts[side] = dict(magnet=mc.round(3).tolist(),
                              vbus=(mc + [0, -POGO_PITCH / 2]).round(3).tolist() if side == "R" else (mc + [0, POGO_PITCH / 2]).round(3).tolist(),
                              gnd=(mc + [0, POGO_PITCH / 2]).round(3).tolist() if side == "R" else (mc + [0, -POGO_PITCH / 2]).round(3).tolist())
        for k in ("vbus", "gnd"):
            base = np.maximum(base, -cyl_z(G, contacts[side][k], POGO_HOLE / 2, -FLOOR - 1, 2.0))
            pins.append(contacts[side][k])
        base = np.maximum(base, -cyl_z(G, mc, POD_MAG[0] / 2 + 0.1, -FLOOR - 1, -FLOOR + POD_MAG[1] + 0.1))
    # USB-C opening in the back wall, at bay height
    usb_z = z_bot + PLATE + BOARD_T + 1.6       # board on the plate; receptacle centre 1.6 above its top
    base = np.maximum(base, -rbox(G, [USB_X, outer[1] / 2, usb_z], [USB_C[0], 2 * WALL + 2, USB_C[1]], 1.2))
    # light hole for the charge LED (0603 on the board top, at the back edge)
    led_z = z_bot + PLATE + BOARD_T + 0.3
    d = np.hypot(G[..., 0] - LED_X, G[..., 2] - led_z) - LED_HOLE / 2
    base = np.maximum(base, -np.maximum(d, np.abs(G[..., 1] - outer[1] / 2) - (WALL + 1.0)))
    # ---- lid: cap from base_top - LIP up to lid_top
    lid_h = lid_top - (base_top - LIP)
    lid = rbox(G, [0, 0, base_top - LIP + lid_h / 2], [outer[0], outer[1], lid_h], 3.0)
    lid = np.maximum(lid, -rbox(G, [0, 0, base_top - LIP + (lid_h - LID_T) / 2 - 0.5],
                                [outer[0] - 2 * LID_T, outer[1] - 2 * LID_T, lid_h - LID_T + 1.0], 2.0))

    # ---- bottom plate
    plate = rbox(G, [0, 0, z_bot + PLATE / 2], [outer[0], outer[1], PLATE], 3.0)

    out = {}
    for name, fld in (("case_base", base), ("case_lid", lid), ("case_plate", plate)):
        msh = mesh(fld, axes)
        msh.export(os.path.join(HERE, f"{name}.stl"))
        parts = msh.split(only_watertight=False)
        msh = max(parts, key=lambda q: len(q.faces))                 # drop any stray specks
        for n in (150000, 200000, 250000, 300000):                   # keep the LFS files small
            if len(msh.faces) <= n:
                break
            d = msh.simplify_quadric_decimation(face_count=n)
            d.merge_vertices(); trimesh.repair.fill_holes(d); d.remove_unreferenced_vertices()
            if d.is_watertight:                                      # first watertight decimation wins
                msh = d
                break
        msh.export(os.path.join(HERE, f"{name}.stl"))
        out[name] = dict(n_specks_dropped=len(parts) - 1, bbox_mm=msh.extents.round(2).tolist(), watertight=bool(msh.is_watertight),
                         volume_cm3=round(msh.volume / 1000, 2))
    del G

    # interference check: pods vs base
    for side, m in placed.items():
        bm = trimesh.load(os.path.join(HERE, "case_base.stl"))
        pts = m.sample(4000)
        sd = trimesh.proximity.signed_distance(bm, pts)            # + inside the base
        out[f"pod_{side}_max_intrusion_mm"] = round(float(sd.max()), 3)

    # ---- board outline DXF (case frame XY, board under the floor)
    doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM
    for n in ("Edge.Cuts", "POGO", "POD_MAGNET", "USB_C", "BATTERY", "NOTES"):
        doc.layers.add(n)
    msp = doc.modelspace()
    bw, bl = inner_x - 1.0, 15.5                                   # strip under the pods, back of the bay
    by = inner_y / 2 - bl / 2 - 0.5
    pts = [(-bw / 2, by - bl / 2), (bw / 2, by - bl / 2), (bw / 2, by + bl / 2), (-bw / 2, by + bl / 2), (-bw / 2, by - bl / 2)]
    msp.add_lwpolyline(pts, dxfattribs=dict(layer="Edge.Cuts"))
    for side in ("L", "R"):
        for k in ("vbus", "gnd"):
            msp.add_circle(tuple(contacts[side][k]), 1.0, dxfattribs=dict(layer="POGO"))
            msp.add_text(f"{side}_{k.upper()}", height=0.6, dxfattribs=dict(layer="NOTES")).set_placement(
                (contacts[side][k][0] + 1.2, contacts[side][k][1]))
        msp.add_circle(tuple(contacts[side]["magnet"]), POD_MAG[0] / 2 + 0.1, dxfattribs=dict(layer="POD_MAGNET"))
    msp.add_lwpolyline([(-USB_C[0] / 2 - 0.3, by + bl / 2 - 7.3), (USB_C[0] / 2 + 0.3, by + bl / 2 - 7.3),
                        (USB_C[0] / 2 + 0.3, by + bl / 2), (-USB_C[0] / 2 - 0.3, by + bl / 2)], dxfattribs=dict(layer="USB_C"))
    # 603040 cell turned sideways: 40 mm across, 30 mm front-back, in front of the board strip
    b0 = -inner_y / 2 + 0.3
    assert b0 + 30.0 <= by - bl / 2 - 0.3, "battery does not fit in front of the board"
    for side in ("L", "R"):                                   # every spring pin >= 2 mm inside the board
        for k in ("vbus", "gnd"):
            yk = contacts[side][k][1]
            assert by - bl / 2 + 2.0 <= yk <= by + bl / 2 - 2.0, (side, k, yk)
    msp.add_lwpolyline([(-20, b0), (20, b0), (20, b0 + 30), (-20, b0 + 30), (-20, b0)], dxfattribs=dict(layer="BATTERY"))
    notes = ["Haven v2 case board, case frame (X across, Y back = +), board under the floor at the back of the bay.",
             "Spring pins on the TOP face at POGO circles, pointing up through the floor; pod magnets sit in the floor",
             "above POD_MAGNET (keep it free of tall parts). USB-C on the top face at the back edge, mouth flush with it.",
             "LiPo 603040 (6 x 30 x 40) lies in BATTERY, turned sideways, on the bay floor (bottom plate)."]
    for i, t in enumerate(notes):
        msp.add_text(t, height=0.7, dxfattribs=dict(layer="NOTES")).set_placement((bw / 2 + 3, by + bl / 2 - i * 1.4))
    doc.saveas(os.path.join(HERE, "board_case_outline.dxf"))

    out.update(outer_mm=[round(float(outer[0]), 1), round(float(outer[1]), 1), round(float(lid_top - z_bot), 1)],
               board_mm=[round(bw, 1), bl], board_center_y=round(by, 2), floor_top_z=0.0, bay=[inner_x, inner_y, BAY_H],
               contacts=contacts, usb_c_center=[USB_X, round(usb_z, 2)], led_hole=[LED_X, round(led_z, 2)], board_top_z=round(z_bot + PLATE + BOARD_T, 2), pogo_work_h=POGO_WORK_H,
               pod_top_z=round(float(pod_top), 2), base_top_z=base_top,
               tray_center_y=round(float(ty), 2), tray_floor_z=round(base_top - TRAY[2], 2), lid_inner_top_z=round(lid_top - LID_T, 2))
    json.dump(out, open(os.path.join(HERE, "case.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
