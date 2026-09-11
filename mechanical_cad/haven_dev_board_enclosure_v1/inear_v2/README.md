# In-ear pivot (v2)

Supersedes the behind-the-ear (BTE) design in the parent folder as the
current direction, per an explicit request to make the enclosure actually
sit in the ear rather than hang behind it. The BTE version is kept as-is
for reference, not deleted.

## Shape

A genuinely oval body (elliptical cross-section via `cq.Workplane.ellipse`,
not a rounded rectangle that just reads as a cylinder from most angles),
sized in the same family as a single AirPods Pro earbud body (30.9 × 21.8 ×
24mm, real spec) — this design runs to 20 × 23 × 33mm, similar volume,
because Haven's BOM carries more electronics (full BLE SoC, IMU, PMIC, fuel
gauge, level shifter, USB-C, microSD) than a sleek consumer earbud does.

A canal stalk (5.4mm diameter, mid-range of the real 4–6mm eartip-stem
spec found via web search) protrudes from the bottom, tilted 18° forward,
with a small retention barb near the tip so a standard silicone eartip has
something to grip rather than sliding off a plain cylinder. No BTE hook —
this design relies on the eartip's fit and grip to stay in, like a real
earbud or a modern RIC hearing aid.

## A real modeling lesson from this pivot

The BTE version's ports were positioned by computing an offset from a flat
box face (`BODY_W/2 - port_size/2 - wall`, etc.) — that works cleanly for
a box, but this body's outer surface is an ellipse with a filleted cap, so
the true surface position isn't a fixed offset; it varies with height and
tapers hard near the caps. An early attempt reused the box-style offset
math and several ports missed the body entirely (their location, per the
same formula, was floating past a corner that no longer existed in the new
shape). Fixed by verifying with a *scan* — testing many points across a
range for each cut, confirming a hole genuinely exists somewhere on that
line — rather than trusting a single computed point. Every port and the
nozzle bore are verified this way now (see the `scan()` helper and the
per-feature checks at the bottom of `generate_inear_enclosure.py`).

## Real, unusual-for-a-tiny-earbud detail worth a conscious decision

Most true wireless earbuds keep USB-C and any storage slot on the charging
*case*, not the earbud itself (the earbud usually only has charging
contacts). This design puts a real USB-C receptacle and a full microSD
slot directly on the in-ear body, because that's what the actual routed
`haven_dev_board_kicad` BOM has. It fits here — verified, not assumed —
but it's worth deciding consciously whether a later hardware revision
should move user-accessible USB-C/microSD to a case instead.

## Still open (same caveats as the BTE version)

No real ear-fit/anthropometric data behind the body or canal-stalk
dimensions, no snap-fit/screw-boss features between the two shell halves,
no DFM pass, and the PCB/battery envelopes are still placeholders (not the
actual routed board outline — see the BTE README for the L-shape/notch
finding, which applies here too).

## Files

- `haven_enclosure_inear_assembled_v2.step` — full shell, for viewing.
- `haven_enclosure_inear_top_v2.step`, `haven_enclosure_inear_bottom_v2.step`
  — the two actual printable/moldable parts.
- `generate_inear_enclosure.py` — CadQuery source, all dimensions as named
  constants at the top.
- `preview_iso.png`, `preview_internal_fit_check.png` — renders.
