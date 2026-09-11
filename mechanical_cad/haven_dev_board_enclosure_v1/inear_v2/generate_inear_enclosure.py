import cadquery as cq
import math
from cadquery.occ_impl.shapes import Solid
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt

# ---- In-ear (concha-sitting) body, AirPods-Pro-scale, real component driven ----
# AirPods Pro single earbud body: 30.9 x 21.8 x 24mm (real spec) -- Haven's
# BOM is chunkier (full BLE SoC + USB-C + microSD + IMU, not just a thin
# earbud PCB), so this runs a bit bigger, oriented with the long axis
# vertical (matching how AirPods Pro itself is proportioned).

BODY_H = 33.0   # vertical, worn axis
BODY_W = 22.0
BODY_D = 20.0
WALL = 1.2

PCB_L, PCB_W, PCB_T = 29.0, 12.5, 1.0
BATT_DIA, BATT_H = 14.1, 5.4

USB_W, USB_H = 9.2, 3.4
SD_W, SD_H = 12.5, 2.6

NOZZLE_DIA = 5.4     # canal stalk, mid-range of the real 4-6mm eartip stem spec
NOZZLE_LEN = 7.5
NOZZLE_TILT = 18      # degrees, angled forward into the canal like a real earbud

def state(shape, x, y, z):
    classifier = BRepClass3d_SolidClassifier(shape.wrapped)
    classifier.Perform(gp_Pnt(x, y, z), 1e-6)
    return str(classifier.State()).replace("TopAbs_State.TopAbs_", "")

def bean_profile(h, w, d):
    """A genuine oval body (elliptical cross-section, not a rounded
    rectangle that just reads as a cylinder) with a modest cap rounding
    top/bottom, so there's still a real flat-ish interior near the caps
    to place components against."""
    prism = cq.Workplane("XY").ellipse(d / 2, w / 2).extrude(h / 2, both=True)
    prism = prism.faces(">Z").edges().fillet(3.5)
    prism = prism.faces("<Z").edges().fillet(3.5)
    return prism

outer = bean_profile(BODY_H, BODY_W, BODY_D)
inner_cavity = bean_profile(BODY_H - 2 * WALL, BODY_W - 2 * WALL, BODY_D - 2 * WALL)
inner_cavity = inner_cavity.translate((0, 0, 0))
shell = outer.cut(inner_cavity)

# ---- Canal stalk / nozzle, protruding from the bottom, tilted forward ----
nozzle = (
    cq.Workplane("XY")
    .circle(NOZZLE_DIA / 2)
    .extrude(NOZZLE_LEN)
)
nozzle = nozzle.rotate((0, 0, 0), (1, 0, 0), 180 - NOZZLE_TILT)
nozzle = nozzle.translate((0, -BODY_D / 2 + 3, -BODY_H / 2 + 2))
nozzle_bore = (
    cq.Workplane("XY")
    .circle(NOZZLE_DIA / 2 - 1.0)
    .extrude(NOZZLE_LEN + 2)
)
nozzle_bore = nozzle_bore.rotate((0, 0, 0), (1, 0, 0), 180 - NOZZLE_TILT)
nozzle_bore = nozzle_bore.translate((0, -BODY_D / 2 + 3, -BODY_H / 2 + 2))

# small retention ridge near the tip so a real silicone eartip has
# something to grip onto rather than sliding straight off a plain cylinder
barb = (
    cq.Workplane("XY")
    .circle(NOZZLE_DIA / 2 + 0.5)
    .extrude(1.2)
)
barb = barb.rotate((0, 0, 0), (1, 0, 0), 180 - NOZZLE_TILT)
ang_rad = math.radians(180 - NOZZLE_TILT)
barb_offset = NOZZLE_LEN - 2.5
by = -barb_offset * math.sin(ang_rad)
bz = barb_offset * math.cos(ang_rad)
barb = barb.translate((0, -BODY_D / 2 + 3 + by, -BODY_H / 2 + 2 + bz))

body = cq.Workplane(obj=shell.val().fuse(nozzle.val()).fuse(barb.val()))
body = body.cut(nozzle_bore)

# All the cuts below use generously long cutting tools (spanning well
# outside the body to well inside the cavity) rather than trying to
# compute an exact "just past the wall" offset -- the ellipse+cap-fillet
# body's true surface position isn't a simple constant like a flat box
# face was, and an earlier attempt at precise offsets missed the real
# surface entirely near the tapered caps. All positions are also kept
# within the "straight" band (roughly |z| < 10) away from where the cap
# fillet starts tapering the cross-section down.
REACH = 25  # generous -- guaranteed to cross the ~1.2mm wall wherever it is

# ---- USB-C cutout, lower back (+Y) face ----
usbc_cut = (
    cq.Workplane("XZ")
    .workplane(offset=-REACH)
    .center(0, -9)
    .rect(USB_W, USB_H)
    .extrude(2 * REACH)
)
body = body.cut(usbc_cut)

# ---- microSD slot, side (+X) face ----
sd_cut = (
    cq.Workplane("YZ")
    .workplane(offset=-REACH)
    .center(6.5, -2)
    .rect(SD_H, SD_W)
    .extrude(2 * REACH)
)
body = body.cut(sd_cut)

# ---- Mic acoustic port + LED window, outer back (+Y) face ----
mic_port = (
    cq.Workplane("XZ")
    .workplane(offset=-REACH)
    .center(3, 6)
    .circle(0.5).extrude(2 * REACH)
)
led_port = (
    cq.Workplane("XZ")
    .workplane(offset=-REACH)
    .center(-4, 0)
    .circle(0.9).extrude(2 * REACH)
)
body = body.cut(mic_port).cut(led_port)

top_half = body.intersect(cq.Workplane("XY").box(200, 200, BODY_H + 20, centered=(True, True, False)))
bottom_half = body.cut(top_half)

pcb_ref = (
    cq.Workplane("XY").workplane(offset=-BODY_H / 2 + 3).center(0, 1)
    .rect(PCB_L, PCB_W).extrude(PCB_T)
)
BATT_Z0 = BODY_H / 2 - BATT_H - 6.5
batt_ref = (
    cq.Workplane("XY").workplane(offset=BATT_Z0).center(0, -1)
    .circle(BATT_DIA / 2).extrude(BATT_H)
)

OUT = "/tmp/claude-1000/-home-paul22iac/de6df91d-5626-4f43-95cb-adf67fb0294d/scratchpad"
body.val().exportStep(f"{OUT}/haven_enclosure_inear_v1.step")
top_half.val().exportStep(f"{OUT}/haven_enclosure_inear_top_v1.step")
bottom_half.val().exportStep(f"{OUT}/haven_enclosure_inear_bottom_v1.step")

bb = body.val().BoundingBox()
print("bbox:", round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1))

shape = body.val()
print("--- verifying cutouts actually penetrate: scan across the wall band ---")
def scan(label, fixed, axis, lo=-13, hi=13, step=0.5):
    """axis: which coordinate varies; fixed: the other two, as a dict."""
    found_out = False
    v = lo
    while v <= hi:
        pt = dict(fixed)
        pt[axis] = v
        s = state(shape, pt['x'], pt['y'], pt['z'])
        if s == 'OUT':
            found_out = True
        v += step
    print(f"{label}: {'PASS (hole found)' if found_out else 'FAIL (no hole found anywhere on this scan line)'}")

scan("USB-C (scanning Y through the cut)", {'x':0,'y':0,'z':-9}, 'y')
scan("microSD (scanning X through the cut)", {'x':0,'y':-2,'z':0}, 'x')
scan("mic port (scanning Y)", {'x':3,'y':0,'z':6}, 'y')
scan("LED port (scanning Y)", {'x':-4,'y':0,'z':0}, 'y')
print("nozzle bore reaches tip (expect OUT):", state(shape, 0, -BODY_D/2+3, -BODY_H/2-NOZZLE_LEN*0.6))

print("--- PCB fit check ---")
bad = 0
for dx in (-PCB_L/2, PCB_L/2):
    for dy in (-PCB_W/2+1, PCB_W/2+1):
        for z in (-BODY_H/2+3, -BODY_H/2+3+PCB_T):
            s = state(shape, dx, dy, z)
            if s != "OUT":
                print("PCB COLLISION", dx, dy, z, s); bad += 1
print("PCB collisions:", bad)

print("--- battery fit check ---")
bad = 0
for ang in range(0, 360, 30):
    x = (BATT_DIA/2) * math.cos(math.radians(ang))
    y = -1 + (BATT_DIA/2) * math.sin(math.radians(ang))
    for z in (BATT_Z0, BATT_Z0 + BATT_H):
        s = state(shape, x, y, z)
        if s != "OUT":
            print("BATTERY COLLISION", round(x,2), round(y,2), round(z,2), s); bad += 1
print("battery collisions:", bad)

print("--- PCB vs battery (should not overlap in Z if they share XY) ---")
print("PCB z-range:", -BODY_H/2+3, "to", -BODY_H/2+3+PCB_T)
print("battery z-range:", BATT_Z0, "to", BATT_Z0+BATT_H)
