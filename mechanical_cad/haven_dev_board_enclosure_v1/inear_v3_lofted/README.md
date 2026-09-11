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

## Verification

Same discipline as v2: every port cut is verified by scanning many points
across it for a genuine hole (not trusting one computed coordinate — this
body has no flat faces at fixed offsets, so that would fail the same way
a plain point-check did on v2's curved surface), and the PCB/battery
envelopes are checked point-by-point against the real solid geometry for
collisions. All pass with 0 collisions found.

## Still open

Same caveats as the earlier versions: no real ear-fit/anthropometric data,
no snap-fit/screw-boss features between the shell halves, no DFM pass,
placeholder PCB/battery envelopes (not the real routed board outline —
still needs the L-shaped/notched consideration from the BTE version's
findings once a real board layout exists). Also still open: whether
USB-C/microSD belong on the in-ear piece itself or should move to a
charging case in a later hardware revision (most true wireless earbuds
put them on the case).

## Files

- `haven_enclosure_inear_assembled_v3.step` — full shell, for viewing.
- `haven_enclosure_inear_top_v3.step`, `haven_enclosure_inear_bottom_v3.step`
  — the two actual printable/moldable parts.
- `generate_inear_enclosure_v3.py` — CadQuery source; the `stations` list
  at the top defines the whole silhouette.
- `preview_iso.png`, `preview_internal_fit_check.png` — renders.
