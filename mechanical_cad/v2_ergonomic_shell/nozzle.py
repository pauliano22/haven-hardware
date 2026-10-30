"""Standard ear-tip nozzle, shared by the Rev A shell and the fit-test prints.

One nozzle size for every body size: ear-canal size is handled by the tip
size (S/M/L), not by the nozzle. Dimensions follow PROJECT_STATUS.md's
2026-10-28 seal spec.
"""
import cadquery as cq

NOZZLE_OD = 5.4     # shaft; fits 4.5 mm-bore tips (SpinFit CP145 / NEO, generic IEM silicone)
NOZZLE_LEN = 5.5    # from the body surface to the tip (spec: 5-6 mm)
LIP_HEIGHT = 0.4    # retaining lip, radial (spec: 0.3-0.5 mm) -> 6.2 mm lip OD
LIP_LEN = 1.2       # axial length of the lip, including its lead-in
LIP_LEADIN = 0.6    # tip-side cone so the tip slides on; the back face stays square to retain it
BORE_D = 3.0        # sound bore; typical IEM nozzle bores are ~2-3.5 mm. Leaves a 1.2 mm wall.


def _plane(origin, axis):
    axis = cq.Vector(axis).normalized()
    ref = cq.Vector(1, 0, 0) if abs(axis.x) < 0.9 else cq.Vector(0, 1, 0)
    x_dir = (ref - axis * ref.dot(axis)).normalized()
    return cq.Plane(origin=cq.Vector(origin).toTuple(), xDir=x_dir.toTuple(), normal=axis.toTuple())


def _cyl(origin, axis, r, length):
    return cq.Workplane(_plane(origin, axis)).circle(r).extrude(length).val()


def _cone(origin, axis, r0, r1, length):
    pl = _plane(origin, axis)
    return cq.Solid.makeCone(r0, r1, length, pnt=pl.origin, dir=pl.zDir)


def nozzle_solid(base, axis, shaft_len, root_len=0.0):
    """Outer nozzle body along `axis`.

    `base` is where the nozzle meets the body surface; the shaft runs
    `shaft_len` from there to the tip. `root_len` extends the shaft backwards
    into the body so the union fuses cleanly.
    """
    axis = cq.Vector(axis).normalized()
    base = cq.Vector(base)
    r = NOZZLE_OD / 2
    root = base - axis * root_len
    tip = base + axis * shaft_len
    shaft = _cyl(root, axis, r, root_len + shaft_len - LIP_LEN)
    lip_start = tip - axis * LIP_LEN
    lip_flat = _cyl(lip_start, axis, r + LIP_HEIGHT, LIP_LEN - LIP_LEADIN)
    lead_in = _cone(tip - axis * LIP_LEADIN, axis, r + LIP_HEIGHT, r + 0.05, LIP_LEADIN)
    return shaft.fuse(lip_flat).fuse(lead_in).clean()


def bore_solid(start, axis, length):
    return _cyl(cq.Vector(start), axis, BORE_D / 2, length)
