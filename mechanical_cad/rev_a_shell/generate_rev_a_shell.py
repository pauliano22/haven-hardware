"""Rev A front shell: OpenEarable 2.0.1's front shell with a standard ear-tip nozzle.

Run from anywhere: `python generate_rev_a_shell.py`. Writes STEP, STL and PNG
previews next to this file and prints the verification checks.

What changes versus OpenEarable's front shell:
  1. Its oval stem (5.6 x 4.5 mm, oval flared lip, for OpenEarable's own tips)
     is cut off and replaced by a round 5.4 mm nozzle (nozzle.py) on the same
     axis, so standard 4.5 mm-bore tips fit.
  2. The stem's oval channel (5.2 x 3.4 mm) is replaced by a round 3.0 mm bore
     that opens into the existing cavity above the speaker mount.
  3. The rectangular window on top of the head is filled. It is where the
     sensor flex board (PPG, temperature) looked out; Rev A has no flex board.
Everything else (speaker mount seat, battery bay, USB-C opening, speaker
wire channels, back-volume holes) is OpenEarable's geometry, unchanged.
"""
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
from OCP.BRep import BRep_Tool
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace

import nozzle as nz

HERE = os.path.dirname(os.path.abspath(__file__))
OE_DIR = os.path.join(HERE, "..", "OpenEarable-Enclosure-2.0.1")

# ---- Parameters -------------------------------------------------------------
# Rev A board length. The parallel board task decides the final number
# (~28 mm after trimming the flex-connector end of OpenEarable's 32.18 mm board).
BOARD_LENGTH_MM = 28.0
# Extra tilt of the nozzle, in degrees, about the shell's x axis (positive =
# steeper toward +z). Default 0 keeps OpenEarable's stem axis, which is the one
# orientation already worn in real ears; fit testing can change this without
# touching any other geometry.
EXTRA_TILT_DEG = 0.0
MAKE_FIN_VARIANT = True

# ---- Measured OpenEarable geometry (front shell 2.0.1 / mounts 2.0.0) --------
# Stem axis: from the stem end-face normal (-0.003, -0.647, 0.763) and the
# speaker mount ring, which is centred on the same line. AXIS_P0 is a point on
# it at the speaker seat; distances along the axis ("t") are from there.
AXIS_P0 = cq.Vector(8.32, 23.10, 10.29)
AXIS = cq.Vector(0.0, -0.647, 0.763).normalized()
T_SHOULDER = 5.55   # cavity above the speaker mount closes into the stem channel here
T_HEAD_END = 6.15   # head surface ends; beyond this only the old stem remains
T_CUT = 6.3         # old stem removed beyond this...
CUT_R = 4.0         # ...within this radius of the axis (old stem max half-width 3.7)
T_NOZZLE_ROOT = 5.9  # new shaft starts inside the shoulder material so it fuses
T_BORE_START = 5.0   # bore starts inside the speaker-mount cavity
# Sensor-flex window on top of the head (opening at the outer surface), and
# the footprint the closing skin covers (window plus a small margin).
WIN_X = (6.70, 10.00)
WIN_Y = (24.90, 28.80)
RECESS_X = (6.55, 10.15)
RECESS_Y = (24.60, 29.00)
SKIN_T = 1.2
# Second, small top opening (x 7.1-9.6, y 30.2-31.2) is left as is: purpose
# not identified, and it opens into the interior, not the sound path.
# Battery: OpenEarable battery mount footprint along y (14 mm coin cell).
BATTERY_Y = (18.55, 33.75)
OE_BOARD_LENGTH = 32.18
OE_SHELL_Y_MAX = 34.61


def at(t):
    return AXIS_P0 + AXIS * t


def classifier(shape):
    c = BRepClass3d_SolidClassifier(shape.wrapped)

    def state(p):
        c.Perform(gp_Pnt(*cq.Vector(p).toTuple()), 1e-6)
        return str(c.State()).split("_")[-1]
    return state


def tilted_axis():
    return AXIS if EXTRA_TILT_DEG == 0 else _rot_x(AXIS, EXTRA_TILT_DEG)


def _rot_x(v, deg):
    a = np.radians(deg)
    y = v.y * np.cos(a) - v.z * np.sin(a)
    z = v.y * np.sin(a) + v.z * np.cos(a)
    return cq.Vector(v.x, y, z).normalized()


def window_fill(front):
    """A 1.2 mm skin that closes the sensor recess flush with the head's dome.

    The window is a stepped recess cut through the dome's B-spline surface.
    That surface, untrimmed, still spans the opening (checked: within 0.02 mm
    of the surrounding dome), so the skin is the untrimmed dome thickened
    inward by WALL and clipped to the recess footprint. A skin, not a solid
    plug, because the speaker mount's upper edge reaches y~25.3, z~15.8, right
    under the recess's front end.
    """
    dome = [f for f in front.Faces() if f.geomType() == "BSPLINE"
            and (lambda b: b.xmin < 1.0 and b.xmax > 15.5 and 22.0 < b.ymin < 22.5 and 29.8 < b.ymax < 30.2)(f.BoundingBox())]
    assert len(dome) == 1, "dome face not found; OpenEarable STEP changed?"
    surf = BRep_Tool.Surface_s(dome[0].wrapped)
    full = cq.Face(BRepBuilderAPI_MakeFace(surf, 1e-6).Face())
    skin = full.thicken(SKIN_T)
    probe = cq.Vector(sum(WIN_X) / 2, sum(WIN_Y) / 2, 16.0 - 0.6)  # just under the dome
    if classifier(skin)(probe) != "IN":
        skin = full.thicken(-SKIN_T)
    x0, x1 = RECESS_X
    y0, y1 = RECESS_Y
    prism = cq.Workplane("XY").box(x1 - x0, y1 - y0, 30, centered=False).translate((x0, y0, 0)).val()
    return skin.intersect(prism)


def concha_fin():
    """Experimental stabilizer: a thin rounded tab on the back of the head.

    Placement is a first guess (opposite the nozzle, upper back edge of the
    head) and must be confirmed on a real ear before it means anything.
    """
    fin = (cq.Workplane("YZ").workplane(offset=8.33 - 0.8)
           .moveTo(31.0, 9.0).lineTo(36.5, 12.5).threePointArc((36.9, 13.9), (35.8, 14.6))
           .lineTo(30.0, 12.0).close().extrude(1.6))
    return fin.edges("|X").fillet(0.3).val()


def build(with_fin=False):
    front = cq.importers.importStep(os.path.join(OE_DIR, "OpenEarable-front-2.0.1.step")).val()
    axis = tilted_axis()
    stem_cutter = nz._cyl(at(T_CUT), AXIS, CUT_R, 12.0)
    body = front.cut(stem_cutter)
    body = body.fuse(window_fill(front))
    base = at(T_HEAD_END)
    shaft_len = nz.NOZZLE_LEN
    noz = nz.nozzle_solid(base, axis, shaft_len, root_len=T_HEAD_END - T_NOZZLE_ROOT)
    body = body.fuse(noz)
    if with_fin:
        body = body.fuse(concha_fin())
    bore_start = at(T_BORE_START)
    bore_len = (T_HEAD_END - T_BORE_START) + shaft_len + 1.0
    body = body.cut(nz.bore_solid(bore_start, axis, bore_len)).clean()
    tip = base + axis * shaft_len
    return front, body, dict(axis=axis, base=base, tip=tip)


def verify(front, body, info):
    st = classifier(body)
    st0 = classifier(front)
    axis, base, tip = info["axis"], info["base"], info["tip"]
    results = []

    def check(name, ok, detail=""):
        results.append((name, ok, detail))

    # bore: open from inside the speaker cavity to past the tip, every 0.25 mm
    pts = [at(T_BORE_START - 0.6) + axis * s for s in np.arange(0, (tip - at(T_BORE_START - 0.6)).Length + 0.5, 0.25)]
    closed = [round((p - AXIS_P0).dot(axis), 2) for p in pts if st(p) != "OUT"]
    check("bore open from speaker cavity to tip", not closed, f"blocked at t={closed[:5]}" if closed else "")
    # cavity above the speaker mount is still the original cavity (bore opens into it)
    check("bore opens into the cavity above the speaker mount", st(at(4.6)) == "OUT")
    # nozzle wall present all round, 1.2 mm
    u = cq.Vector(1, 0, 0)
    v = axis.cross(u).normalized()
    bad = []
    for s in np.arange(0.3, nz.NOZZLE_LEN - nz.LIP_LEN, 0.5):
        for ang in np.linspace(0, 2 * np.pi, 8, endpoint=False):
            d = u * np.cos(ang) + v * np.sin(ang)
            r_mid = (nz.BORE_D / 2 + nz.NOZZLE_OD / 2) / 2
            if st(base + axis * s + d * r_mid) != "IN":
                bad.append(round(s, 1))
    check("nozzle wall solid all round (1.2 mm)", not bad, f"gaps at s={sorted(set(bad))[:6]}" if bad else "")
    # lip present, and stops above the shaft
    lip_mid = tip - axis * (nz.LIP_LEN - nz.LIP_LEADIN) / 2
    check("retaining lip present (6.2 mm OD)", st(lip_mid + u * (nz.NOZZLE_OD / 2 + nz.LIP_HEIGHT * 0.5)) == "IN")
    check("shaft behind the lip is 5.4 mm (tip seats there)",
          st(tip - axis * (nz.LIP_LEN + 0.6) + u * (nz.NOZZLE_OD / 2 + 0.15)) == "OUT")
    # old oval stem gone (its widest point was 3.7 mm off-axis at t~9.5)
    check("old oval stem removed", st(at(9.5) + u * 3.4) == "OUT" and st0(at(9.5) + u * 3.4) == "IN")
    # sensor window closed, flush: just under the dome is solid, just above is air
    dome_z = _dome_heights(front)
    flush_bad, closed_bad = [], []
    for x in np.linspace(WIN_X[0] + 0.2, WIN_X[1] - 0.2, 5):
        for y in np.linspace(WIN_Y[0] + 0.2, WIN_Y[1] - 0.2, 5):
            z = dome_z(x, y)
            if st(cq.Vector(x, y, z - 0.4)) != "IN" or st0(cq.Vector(x, y, z - 0.4)) != "OUT":
                closed_bad.append((round(x, 1), round(y, 1)))
            if st(cq.Vector(x, y, z + 0.1)) != "OUT":
                flush_bad.append((round(x, 1), round(y, 1)))
    check("sensor-flex window closed", not closed_bad, f"open at {closed_bad[:4]}" if closed_bad else "")
    check("closing skin flush with the dome (nothing proud by >0.1 mm)", not flush_bad,
          f"proud at {flush_bad[:4]}" if flush_bad else "")
    # speaker mount must not collide with anything added
    mount = _load_stl(os.path.join(OE_DIR, "OpenEarable-speaker-mount-2.0.0.stl")).reshape(-1, 3)
    mount = np.unique(np.round(mount, 2), axis=0)
    # only points that could reach added material: near the skin or past the shoulder
    t_m = (mount - np.array(AXIS_P0.toTuple())) @ np.array(axis.toTuple())
    mount = mount[(mount[:, 1] > 24.0) | (t_m > 4.5)]
    new_hits = [p for p in mount if st(cq.Vector(*p)) == "IN" and st0(cq.Vector(*p)) != "IN"]
    check("no new collision with the speaker mount", not new_hits,
          f"{len(new_hits)} mount points inside added material" if new_hits else f"{len(mount)} mount points checked")
    # unchanged elsewhere: speaker seat, battery bay, USB-C opening
    check("speaker mount seat unchanged", st(at(3.5) + u * 5.6) == st0(at(3.5) + u * 5.6) == "IN")
    check("USB-C opening unchanged", st(cq.Vector(8.3, 0.2, 1.5)) == st0(cq.Vector(8.3, 0.2, 1.5)))
    # board length: what limits the shell length
    board_end = 1.33 + BOARD_LENGTH_MM
    limit = max(board_end, BATTERY_Y[1])
    check("shell length (battery-limited)", True,
          f"board {BOARD_LENGTH_MM} mm ends at y={board_end:.1f}; battery bay ends at y={BATTERY_Y[1]}; "
          f"shell stays {OE_SHELL_Y_MAX} mm long" + ("" if board_end < BATTERY_Y[1] else " -- board now longer than battery bay, extend shell!"))
    return results, limit


def _dome_heights(front):
    dome = [f for f in front.Faces() if f.geomType() == "BSPLINE"
            and (lambda b: b.xmin < 1.0 and b.xmax > 15.5 and 22.0 < b.ymin < 22.5 and 29.8 < b.ymax < 30.2)(f.BoundingBox())][0]
    from OCP.GeomAPI import GeomAPI_IntCS
    from OCP.Geom import Geom_Line
    surf = BRep_Tool.Surface_s(dome.wrapped)

    def z_at(x, y):
        """Height of the (untrimmed) dome surface along the vertical line at x, y."""
        inter = GeomAPI_IntCS(Geom_Line(gp_Pnt(x, y, 0), gp_Dir(0, 0, 1)), surf)
        zs = [inter.Point(i + 1).Z() for i in range(inter.NbPoints())]
        return max(zs)
    return z_at


def _load_stl(path):
    d = open(path, "rb").read()
    n = np.frombuffer(d[80:84], "<u4")[0]
    a = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return a["v"].astype(float)


def render_iso(shape, path, title):
    verts, tris = shape.tessellate(0.04, 0.3)
    V = np.array([v.toTuple() for v in verts]); T = np.array(tris)
    views = [(25, -60), (10, 180), (0, 90)]
    fig = plt.figure(figsize=(13, 4.6))
    for i, (el, az) in enumerate(views):
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(V[T], facecolor="#c9d3d8", edgecolor="#4b5560", linewidths=0.04))
        mn, mx = V.min(0), V.max(0); c = (mn + mx) / 2; r = (mx - mn).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.view_init(el, az); ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    fig.suptitle(title, fontsize=10); fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def render_section(front, body, info, path):
    x0 = AXIS_P0.x
    fig, ax = plt.subplots(figsize=(8.5, 7))
    for shape, col, lw, lab in ((front, "#b0b7bf", 0.8, "OpenEarable original"), (body, "k", 1.1, "Rev A")):
        sec = BRepAlgoAPI_Section(shape.wrapped, gp_Pln(gp_Pnt(x0, 0, 0), gp_Dir(1, 0, 0))); sec.Build()
        first = True
        for e in cq.Shape.cast(sec.Shape()).Edges():
            P = np.array([e.positionAt(s).toTuple() for s in np.linspace(0, 1, 30)])
            ax.plot(P[:, 1], P[:, 2], color=col, lw=lw, label=lab if first else None); first = False
    a, t = info["axis"], info["tip"]
    p0 = at(T_BORE_START - 0.6)
    ax.plot([p0.y, t.y + a.y * 1.5], [p0.z, t.z + a.z * 1.5], "r--", lw=0.8, label="nozzle axis")
    ax.annotate("Ø5.4 shaft, Ø6.2 lip\nØ3.0 bore", (t.y, t.z), (t.y - 9, t.z + 1.5),
                arrowprops=dict(arrowstyle="->", lw=0.7), fontsize=8)
    ax.annotate("sensor window closed\n(1.2 mm skin, flush)", (sum(WIN_Y) / 2, 16.4), (26, 20.5), arrowprops=dict(arrowstyle="->", lw=0.7), fontsize=8)
    ax.annotate("speaker mount sits here;\nseal its rim at assembly", (21.5, 12.6), (24.5, 4.5),
                arrowprops=dict(arrowstyle="->", lw=0.7), fontsize=8)
    ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.legend(fontsize=8, loc="lower left")
    ax.set_xlabel("y (mm)"); ax.set_ylabel("z (mm)"); ax.set_xlim(8, 36); ax.set_ylim(-2, 24)
    ax.set_title(f"Section through the nozzle axis (x = {x0} mm)")
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)


def main():
    variants = [("rev_a_front_shell", False)] + ([("rev_a_front_shell_fin", True)] if MAKE_FIN_VARIANT else [])
    for name, fin in variants:
        front, body, info = build(with_fin=fin)
        results, _ = verify(front, body, info)
        print(f"== {name}  volume {body.Volume():.1f} mm3 (OpenEarable {front.Volume():.1f})")
        for n, ok, d in results:
            print(f"  [{'PASS' if ok else 'FAIL'}] {n}" + (f"  ({d})" if d else ""))
        body.exportStep(os.path.join(HERE, f"{name}.step"))
        cq.exporters.export(cq.Workplane(obj=body), os.path.join(HERE, f"{name}.stl"), tolerance=0.01, angularTolerance=0.1)
        render_iso(body, os.path.join(HERE, f"preview_{name}_iso.png"), name.replace("_", " "))
        if not fin:
            render_section(front, body, info, os.path.join(HERE, "preview_rev_a_nozzle_section.png"))
        bb = body.BoundingBox()
        print(f"  bbox {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm; tip at ({info['tip'].x:.2f}, {info['tip'].y:.2f}, {info['tip'].z:.2f})")


if __name__ == "__main__":
    main()
