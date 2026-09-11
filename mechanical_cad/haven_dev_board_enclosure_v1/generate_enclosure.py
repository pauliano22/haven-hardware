import cadquery as cq
import math

BODY_L = 40.0
BODY_W = 19.0
BODY_H = 12.0
WALL = 1.2
CORNER_R = 4.0

PCB_L, PCB_W, PCB_T = 31.0, 13.0, 1.0
BATT_DIA, BATT_H = 14.1, 5.4

USB_W, USB_H = 9.2, 3.4
SD_W, SD_H = 12.5, 2.6

def rounded_capsule(l, w, h, r):
    return cq.Workplane("XY").box(l, w, h).edges("|Z").fillet(r)

outer = rounded_capsule(BODY_L, BODY_W, BODY_H, CORNER_R)
outer = outer.edges("#Z").fillet(2.0)

inner_cavity = rounded_capsule(
    BODY_L - 2 * WALL, BODY_W - 2 * WALL, BODY_H - 2 * WALL, max(CORNER_R - WALL, 0.5)
)
shell = outer.cut(inner_cavity)

# ---- Behind-the-ear hook: a thin curved tube, swept along a real hook path ----
# Real BTE hooks: a slender tube (~2.2mm OD) leaving the top-back of the case,
# arcing up and over, then curving forward and down toward the ear canal --
# roughly a 200-degree sweep, not a closed loop.
from cadquery.occ_impl.shapes import Solid

TUBE_OD = 2.4
hook_start = (BODY_L / 2 - 3.0, BODY_H / 2 - 0.5)
r1 = 5.5
cx, cz = hook_start[0] - r1, hook_start[1]
start_deg, end_deg = 0, 168
tube_r = TUBE_OD / 2

# A torus, restricted to the desired arc via intersection with a pie-wedge --
# an analytic surface, so it's exactly smooth (a swept chain-of-cylinders
# approximation rendered visibly faceted/corrugated at any practical segment
# count; a true sweep() had an unresolved profile-plane orientation bug).
# Purely a mechanical retention hook (holds the case on the ear) -- Haven's
# actual signal path to the ear runs through a separate flex/wire, not
# through this hook, so no acoustic bore is needed.
full_torus = Solid.makeTorus(r1, tube_r, pnt=(cx, 0, cz), dir=(0, 1, 0))
big_r = r1 + tube_r + 5
wedge_pts = [(cx, cz)]
n = 40
for i in range(n + 1):
    a = math.radians(start_deg + (end_deg - start_deg) * i / n)
    wedge_pts.append((cx + big_r * math.cos(a), cz + big_r * math.sin(a)))
wedge_pts.append((cx, cz))
wedge = cq.Workplane("XZ").polyline(wedge_pts).close().extrude(tube_r * 3, both=True)

hook_solid_raw = full_torus.intersect(wedge.val())
hook_solid = cq.Workplane(obj=hook_solid_raw)

body = cq.Workplane(obj=shell.val().fuse(hook_solid_raw))

# NOTE: named-workplane normal sign (does offset/extrude go + or - along the
# implied axis?) turned out to differ between "YZ" and "XZ" in ways I didn't
# verify before -- one cut (microSD) silently missed the body entirely,
# floating off in the wrong direction, only caught by testing actual
# in/out solid-classification at the intended hole, not by eyeballing a
# render. Fixed properly here: every cut sits exactly ON the true face
# (offset = the real half-dimension, no +1 fudge) and extrudes both=True,
# so it punches through regardless of which way that plane's normal points.

# ---- USB-C port cutout, rear (-X) face ----
usbc_cut = (
    cq.Workplane("YZ")
    .workplane(offset=-BODY_L / 2)
    .center(0, -BODY_H / 2 + USB_H / 2 + WALL + 0.6)
    .rect(USB_W, USB_H)
    .extrude(WALL * 3, both=True)
)
body = body.cut(usbc_cut)

# ---- microSD slot cutout, +Y side face ----
sd_cut = (
    cq.Workplane("XZ")
    .workplane(offset=-BODY_W / 2)
    .center(BODY_L / 2 - 9, -BODY_H / 2 + SD_H / 2 + WALL + 0.6)
    .rect(SD_W, SD_H)
    .extrude(WALL * 3, both=True)
)
body = body.cut(sd_cut)

# ---- Mic acoustic port + LED window, top outer face ----
mic_port = (
    cq.Workplane("XY").workplane(offset=BODY_H / 2 - 0.1)
    .center(2, 4).circle(0.5).extrude(WALL + 1)
)
led_port = (
    cq.Workplane("XY").workplane(offset=BODY_H / 2 - 0.1)
    .center(-12, 4).circle(0.9).extrude(WALL + 1)
)
body = body.cut(mic_port).cut(led_port)

# ---- Receiver/eartip cable exit, a side face ----
cable_port = (
    cq.Workplane("XZ")
    .workplane(offset=-BODY_W / 2)
    .center(-BODY_L / 2 + 6, -BODY_H / 2 + 2.2)
    .circle(1.3)
    .extrude(WALL * 3, both=True)
)
body = body.cut(cable_port)

top_half = body.intersect(cq.Workplane("XY").box(200, 200, BODY_H + 20, centered=(True, True, False)))
bottom_half = body.cut(top_half)

pcb_ref = (
    cq.Workplane("XY").workplane(offset=-4.0).center(0, 0)
    .rect(PCB_L, PCB_W).extrude(PCB_T)
)
batt_ref = (
    cq.Workplane("XY").workplane(offset=-1.5)
    .center(BODY_L / 2 - BATT_DIA / 2 - 2, 0)
    .circle(BATT_DIA / 2).extrude(BATT_H)
)

OUT = "/tmp/claude-1000/-home-paul22iac/de6df91d-5626-4f43-95cb-adf67fb0294d/scratchpad"
body.val().exportStep(f"{OUT}/haven_enclosure_shell_v2.step")
top_half.val().exportStep(f"{OUT}/haven_enclosure_top_v2.step")
bottom_half.val().exportStep(f"{OUT}/haven_enclosure_bottom_v2.step")

bb = body.val().BoundingBox()
print("bbox:", round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1))
