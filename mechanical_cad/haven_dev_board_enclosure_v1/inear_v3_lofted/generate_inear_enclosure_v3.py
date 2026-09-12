import cadquery as cq
import math
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt

# ---- A lofted, gently-curved earbud body ----
# Not a straight-extruded capsule: a rounded "head" (where the electronics
# live) tapering down into a shorter "neck" and canal stalk that leans
# forward -- checked Apple's own public dimensional drawing for AirPods
# Pro Gen 2 for proportion *language* (rounded head, stem leaning relative
# to the head) but built as a distinct shape/size of our own, not a traced
# copy -- that drawing is licensed only for making accessories that fit
# around the real product, not for cloning its form.
#
# Real constraint found while sizing this: the widest single cross-section
# here is ~17x14mm, nowhere near enough for a 29mm-long PCB (that number
# was carried over from the earlier straight-capsule design and never
# rechecked against this shape). The single biggest real component is the
# MDBT53-1M module at 9.3x14.3mm -- a compact ~16x13mm board comfortably
# holds that plus everything else in the BOM (all under 3x3mm, plus small
# passives), so that's what's modeled here instead.

WALL = 1.2

def state(shape, x, y, z):
    classifier = BRepClass3d_SolidClassifier(shape.wrapped)
    classifier.Perform(gp_Pnt(x, y, z), 1e-6)
    return str(classifier.State()).replace("TopAbs_State.TopAbs_", "")

# Stations, top to bottom: (z, half-width-x, half-width-y, center-y-offset)
stations = [
    (17.0, 3.2, 2.7, 0.0),
    (12.0, 10.5, 9.0, 0.0),      # widest point, "head"
    (5.0, 10.3, 8.8, -0.6),
    (-3.0, 8.5, 7.2, -2.0),
    (-9.5, 5.5, 4.8, -4.0),
    (-14.5, 3.0, 2.7, -5.8),     # transition into the nozzle base
]

def lofted_body(stations):
    wp = cq.Workplane("XY")
    z_prev = cy_prev = None
    for i, (z, rx, ry, cy) in enumerate(stations):
        if i == 0:
            wp = wp.workplane(offset=z).center(0, cy).ellipse(rx, ry)
        else:
            wp = wp.workplane(offset=z - z_prev).center(0, cy - cy_prev).ellipse(rx, ry)
        z_prev, cy_prev = z, cy
    return wp.loft(ruled=False)

outer = lofted_body(stations)
inner_stations = [(z, max(rx - WALL, 0.3), max(ry - WALL, 0.3), cy) for (z, rx, ry, cy) in stations[:5]]
inner_stations[0] = (inner_stations[0][0] - 1.5,) + inner_stations[0][1:]
inner = lofted_body(inner_stations)
shell = outer.cut(inner)

# ---- Canal stalk / nozzle + retention barb, off the bottom tip ----
NOZZLE_DIA, NOZZLE_LEN, NOZZLE_TILT = 5.4, 7.0, 20
tip_z, tip_cy = stations[-1][0], stations[-1][3]
nozzle = cq.Workplane("XY").circle(NOZZLE_DIA / 2).extrude(NOZZLE_LEN)
nozzle = nozzle.rotate((0, 0, 0), (1, 0, 0), 180 - NOZZLE_TILT)
nozzle = nozzle.translate((0, tip_cy, tip_z))
nozzle_bore = cq.Workplane("XY").circle(NOZZLE_DIA / 2 - 1.0).extrude(NOZZLE_LEN + 2)
nozzle_bore = nozzle_bore.rotate((0, 0, 0), (1, 0, 0), 180 - NOZZLE_TILT)
nozzle_bore = nozzle_bore.translate((0, tip_cy, tip_z))

barb = cq.Workplane("XY").circle(NOZZLE_DIA / 2 + 0.5).extrude(1.2)
barb = barb.rotate((0, 0, 0), (1, 0, 0), 180 - NOZZLE_TILT)
ang_rad = math.radians(180 - NOZZLE_TILT)
barb_offset = NOZZLE_LEN - 2.3
by = tip_cy - barb_offset * math.sin(ang_rad)
bz = tip_z + barb_offset * math.cos(ang_rad)
barb = barb.translate((0, by, bz))

body = cq.Workplane(obj=shell.val().fuse(nozzle.val()).fuse(barb.val()))
body = body.cut(nozzle_bore)

# ---- Real cuts: generous long tools, verified by scanning across each
#      one for a genuine hole afterward (a fixed-offset assumption doesn't
#      hold on this curved, tapering surface -- learned the hard way on
#      the previous ellipse-capsule attempt). ----
REACH = 25
USB_W, USB_H = 9.2, 3.4
SD_W, SD_H = 12.5, 2.6

usbc_cut = cq.Workplane("XZ").workplane(offset=-REACH).center(0, -3).rect(USB_W, USB_H).extrude(2 * REACH)
body = body.cut(usbc_cut)

sd_cut = cq.Workplane("YZ").workplane(offset=-REACH).center(2, 6).rect(SD_H, SD_W).extrude(2 * REACH)
body = body.cut(sd_cut)

mic_port = cq.Workplane("XZ").workplane(offset=-REACH).center(3, 12).circle(0.5).extrude(2 * REACH)
led_port = cq.Workplane("XZ").workplane(offset=-REACH).center(-4, 9).circle(0.9).extrude(2 * REACH)
body = body.cut(mic_port).cut(led_port)

# Split into two moldable/printable halves along a plane through the
# tube's long (Z) axis, not across it. A Z-height split (tried first) put
# ~99% of the body's volume in one piece and a ~1% sliver in the other --
# this body is a tall, mostly-vertical loft, so cutting *across* its height
# just slices off a tiny end cap, not two comparable halves. Splitting by
# X=0 instead gives left/right pieces that both run the full head-to-nozzle
# length, which is what an actual two-part shell needs.
left_half = body.intersect(cq.Workplane("XY").box(200, 200, 200, centered=(True, True, True)).translate((-100, 0, 0)))
right_half = body.cut(left_half)

# ---- Alignment pegs across the seam ----
# The X=0 split plane only has real touching wall material near the front/
# back edges of each elliptical station (where the ellipse's own boundary
# crosses x=0) -- through the middle of a wide cross-section (e.g. the
# "head" at z~12-17) the two halves face an open hollow cavity across the
# seam, not each other. Confirmed by direct point-classification (not
# assumed): near the top of the head (z=15, ry~5.2 interpolated), solid
# material spans a wide x range at y=+-5.0 (the front/back edges), so two
# pegs there -- one near the front edge, one near the back -- give a real,
# verified two-point registration spanning a wide baseline (resists
# rotation, not just translation).
PEG_R, SOCKET_R = 1.2, 1.6
PEG_SITES = [(5.0, 15.5), (-5.0, 15.5)]  # (y, z)

for peg_y, peg_z in PEG_SITES:
    peg = cq.Workplane("YZ").workplane(offset=-3).center(peg_y, peg_z).circle(PEG_R).extrude(5)
    left_half = left_half.union(peg)

    socket = cq.Workplane("YZ").workplane(offset=-0.5).center(peg_y, peg_z).circle(SOCKET_R).extrude(3)
    right_half = right_half.cut(socket)

# ---- Real internal components: compact board + battery, both in the
#      widest band (z ~ 5 to 12) ----
PCB_L, PCB_W, PCB_T = 16.0, 13.0, 1.0
BATT_DIA, BATT_H = 14.1, 5.4

PCB_Z0 = 3.0
pcb_ref = cq.Workplane("XY").workplane(offset=PCB_Z0).center(0, -1).rect(PCB_L, PCB_W).extrude(PCB_T)
BATT_Z0 = PCB_Z0 + PCB_T + 0.5
batt_ref = cq.Workplane("XY").workplane(offset=BATT_Z0).center(0, -1).circle(BATT_DIA / 2).extrude(BATT_H)

OUT = "/tmp/claude-1000/-home-paul22iac/de6df91d-5626-4f43-95cb-adf67fb0294d/scratchpad"
body.val().exportStep(f"{OUT}/haven_enclosure_inear_v3.step")
left_half.val().exportStep(f"{OUT}/haven_enclosure_inear_left_v3.step")
right_half.val().exportStep(f"{OUT}/haven_enclosure_inear_right_v3.step")

print("--- shell split sanity check (both halves should be comparable, not a sliver) ---")
lv, rv = left_half.val().Volume(), right_half.val().Volume()
print(f"left volume: {lv:.1f} mm3, right volume: {rv:.1f} mm3, ratio: {max(lv,rv)/min(lv,rv):.2f}x")

print("--- alignment peg verification ---")
left_shape, right_shape = left_half.val(), right_half.val()
for peg_y, peg_z in PEG_SITES:
    peg_present = state(left_shape, 1.0, peg_y, peg_z) == "IN"
    socket_clear = state(right_shape, 1.0, peg_y, peg_z) == "OUT"
    # peg tip (x=2) must not poke past right_half's real outer surface --
    # compare against the pre-peg body at a point just past the socket's
    # far end (x=2.7, inside the socket radius) to confirm we're still
    # inside material that existed before this feature was added.
    within_original_material = state(body.val(), 2.7, peg_y, peg_z) == "IN"
    print(f"  site (y={peg_y}, z={peg_z}): peg={'PASS' if peg_present else 'FAIL'}, "
          f"socket clearance={'PASS' if socket_clear else 'FAIL'}, "
          f"stays within original wall={'PASS' if within_original_material else 'FAIL'}")

bb = body.val().BoundingBox()
print("bbox:", round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1))

shape = body.val()

def scan(label, fixed, axis, lo=-13, hi=13, step=0.5):
    found_out = False
    v = lo
    while v <= hi:
        pt = dict(fixed)
        pt[axis] = v
        if state(shape, pt['x'], pt['y'], pt['z']) == 'OUT':
            found_out = True
        v += step
    print(f"{label}: {'PASS' if found_out else 'FAIL'}")

print("--- cutout verification (scan for a genuine hole) ---")
scan("USB-C", {'x': 0, 'y': 0, 'z': -3}, 'y')
scan("microSD", {'x': 0, 'y': 2, 'z': 6}, 'x')
scan("mic port", {'x': 3, 'y': 0, 'z': 12}, 'y')
scan("LED port", {'x': -4, 'y': 0, 'z': 9}, 'y')

print("--- nozzle bore check (scan along its axis) ---")
found = False
for t in [i * 0.5 for i in range(20)]:
    y = tip_cy - t * math.sin(ang_rad)
    z = tip_z + t * math.cos(ang_rad)
    if state(shape, 0, y, z) == 'OUT':
        found = True
print("nozzle bore:", "PASS" if found else "FAIL")

print("--- PCB fit check ---")
bad = 0
for dx in (-PCB_L / 2, PCB_L / 2):
    for dy in (-1 - PCB_W / 2, -1 + PCB_W / 2):
        for z in (PCB_Z0, PCB_Z0 + PCB_T):
            if state(shape, dx, dy, z) != "OUT":
                print("PCB COLLISION", dx, dy, z); bad += 1
print("PCB collisions:", bad)

print("--- battery fit check ---")
bad = 0
for ang in range(0, 360, 30):
    x = (BATT_DIA / 2) * math.cos(math.radians(ang))
    y = -1 + (BATT_DIA / 2) * math.sin(math.radians(ang))
    for z in (BATT_Z0, BATT_Z0 + BATT_H):
        if state(shape, x, y, z) != "OUT":
            print("BATTERY COLLISION", round(x, 2), round(y, 2), z); bad += 1
print("battery collisions:", bad)
print(f"PCB z: {PCB_Z0}-{PCB_Z0+PCB_T}, battery z: {BATT_Z0}-{BATT_Z0+BATT_H}, station-11(z=12) top of head")
