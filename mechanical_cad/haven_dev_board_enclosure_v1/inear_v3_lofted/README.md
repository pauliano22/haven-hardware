# Organic lofted shape (v3)

Supersedes `inear_v2/` as the current direction, per feedback that v2's
straight elliptical capsule "doesn't look great" for something meant to
read as a real earbud. v2 kept for reference, not deleted.

## Shape

Built with `cq.Workplane.loft()` across six elliptical stations (see
`stations` in `generate_inear_enclosure_v3.py`) instead of a single
straight-extruded ellipse: a rounded, dome-topped "head" (where the
electronics live) that tapers down through a narrowing "neck" into a
canal stalk, with each station's center offset slightly further in one
direction than the last — that's what gives the body its forward lean,
rather than running as a straight vertical column.

Checked Apple's own public dimensional drawing for AirPods Pro (2nd
generation) — available at developer.apple.com/accessories/
dimensional-drawings/ for accessory makers — for proportion *language*
(a rounded head, a stem/neck that leans relative to it, roughly how much
taller the head-to-tip run is than the head is wide). That drawing is
licensed only for making accessories that fit around the real product,
not for cloning its form, so this shape's actual dimensions, curvature,
and proportions are our own, not traced from it.

## A real sizing correction this pass caught

The widest single cross-section on this new lofted body is only
~17 × 14mm. v2's PCB placeholder was 29mm long — sized for the old
straight-capsule shape and never rechecked here — and would not fit
anywhere on this body at all. The real limiting component is the
MDBT53-1M module (9.3 × 14.3mm, the single biggest part in the BOM);
everything else is under 3 × 3mm plus small passives. A compact
**16 × 13mm** board holds all of it, and that's what's modeled and
fit-checked in this version instead. Worth keeping in mind for whoever
lays out the real board: it needs to be genuinely compact, not just
"smaller than the case."

## Bug found and fixed: the two-part split was bogus

The original shell split (`top_half` = everything above `z=-20`,
`bottom_half` = the remainder) was carried over from the earlier BTE
enclosure, where a horizontal split made sense for that shape's
orientation. It doesn't for this one: this body is a tall, mostly-vertical
loft (head at z≈17 down to the nozzle base at z≈-14.5), so a Z-height cut
put **99% of the volume in "top" and the leftover 1% sliver in "bottom"**
(1820 mm³ vs 19 mm³, confirmed by importing both STEPs and comparing
`.Volume()` directly — not something a render alone would necessarily
flag, since "top" alone silhouettes like a complete shell). Not a
two-part enclosure by any usable definition.

Fixed by splitting through the tube's long axis instead — an `X=0` plane,
giving left/right halves that both run the full head-to-nozzle length.
Re-verified by volume: **917.4 mm³ vs 921.6 mm³ (1.00x ratio)**. All the
existing port/PCB/battery checks were re-run against the corrected split
and still pass. Files renamed `..._left_v3.step` / `..._right_v3.step` to
describe what they actually are now, replacing the old (deleted)
`..._top_v3.step` / `..._bottom_v3.step`.

## Verification

Same discipline as v2: every port cut is verified by scanning many points
across it for a genuine hole (not trusting one computed coordinate — this
body has no flat faces at fixed offsets, so that would fail the same way
a plain point-check did on v2's curved surface), and the PCB/battery
envelopes are checked point-by-point against the real solid geometry for
collisions. All pass with 0 collisions found.

## Alignment pegs across the seam

Added two locating pegs (1.2mm radius, 1.6mm-radius clearance socket) to
register the left/right halves during assembly. Finding worth recording:
the X=0 split plane only has real touching wall material near the front/
back edges of a given cross-section — through the middle of a wide
station (e.g. the head, z~12-17) the two halves face an open hollow
cavity across the seam, not each other, since the split cuts through the
ellipse's interior, not its wall. Confirmed by direct point-classification
(scanning along x at fixed y/z), not assumed. The pegs sit near the top of
the head (z≈15.5) at the ellipse's front and back edges (y≈±5.0), where a
scan confirmed solid material spans the seam — a wide baseline that
resists rotation, not just translation, between the two halves. Each site
is verified for peg presence, socket clearance, and that the socket
doesn't cut past the original wall's outer surface.

## Still open

Same caveats as the earlier versions: no real ear-fit/anthropometric data,
no DFM pass,
placeholder PCB/battery envelopes (not the real routed board outline —
still needs the L-shaped/notched consideration from the BTE version's
findings once a real board layout exists). Also still open: whether
USB-C/microSD belong on the in-ear piece itself or should move to a
charging case in a later hardware revision (most true wireless earbuds
put them on the case).

## Files

- `haven_enclosure_inear_assembled_v3.step` — full shell, for viewing.
- `haven_enclosure_inear_left_v3.step`, `haven_enclosure_inear_right_v3.step`
  — the two actual printable/moldable parts.
- `generate_inear_enclosure_v3.py` — CadQuery source; the `stations` list
  at the top defines the whole silhouette.
- `preview_iso.png`, `preview_internal_fit_check.png` — renders.
