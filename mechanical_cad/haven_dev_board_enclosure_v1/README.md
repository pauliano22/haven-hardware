# Haven dev board enclosure — v1 concept

A first-draft mechanical envelope for a real product-shaped enclosure around
`haven_dev_board_kicad`'s electronics, generated parametrically with
[CadQuery](https://cadquery.readthedocs.io/) (`generate_enclosure.py` — real
code, not a hand-modeled one-off; re-run it to regenerate or tweak
dimensions).

**This is not the same thing as `mechanical_cad/Enclosure.stp`** (the
existing file in the parent folder). That one was built around the stock
3-board OpenEarable stack (main + flex + debugging boards) — it's missing
the ADAU1860 entirely and includes a pressure/IR-temperature/accelerometer
sensor suite that doesn't exist on the actual routed board. This new folder
is scoped to the real, routed `haven_dev_board_kicad` BOM instead.

## Why this shape and size

Not guessed — derived from real numbers:

| Driver | Real spec | Source |
|---|---|---|
| BLE module | MDBT53-1M, 9.3 × 14.3 × 1.85mm, onboard chip antenna | Raytac datasheet |
| Battery | Varta CP1454 A4X, 14.1mm dia × 5.4mm, 108mAh Li-ion rechargeable | Varta CoinPower datasheet — the same cell the (wrong-board) `Enclosure.stp` had already picked, reused here since it's a real, sensible, off-the-shelf choice |
| microSD slot | TF-06A push-push connector, ~12 × 14mm footprint | HAVEN_BOM.csv (`CARD1`) |
| USB-C | GT-USB-9047A SMD receptacle | HAVEN_BOM.csv (`U12`) |
| Reference silhouette | Modern RIC hearing aid body ≈ 8 × 12 × 30mm (Phonak Audéo Paradise) | web search — but Haven's BOM carries far more (a full BLE SoC, IMU, PMIC, fuel gauge, level shifter, USB-C, microSD) than a sleek consumer RIC does, so this is deliberately chunkier than that reference, closer to a rugged/OTC BTE body |

Resulting body: **40 × 19mm footprint, 12mm thick, ~18mm tall including the
ear hook.** Comparable to a mid-range/rugged BTE hearing aid or hearing-
protection electronics form factor — not the sleekest fashion hearing aid,
because the component count genuinely doesn't allow it yet.

## What's actually in this file

- A rounded-capsule two-piece shell (`_top_shell_v1` / `_bottom_shell_v1`,
  split at the vertical midplane) with 1.2mm walls.
- A behind-the-ear hook, built as a torus arc (analytically smooth, not a
  faceted approximation — see the comments in `generate_enclosure.py` for
  why a naive swept-tube approach didn't work). It's **purely mechanical
  retention** — Haven's actual signal path to the ear runs through a
  separate flex/wire to an in-ear receiver, so the hook has no acoustic
  bore, unlike a real hearing aid's sound-tube hook.
- USB-C cutout, microSD slot cutout, a mic acoustic port, an LED window, and
  a cable exit for the flex/wire to the in-ear receiver+eartip.
- A PCB reference envelope (31 × 13 × 1mm) and the battery envelope, both
  verified — by actual point-in-solid classification against the real
  B-rep, not by eyeballing a render — to fit inside the cavity without
  colliding with the walls or each other.

## A real finding from the fit check, worth knowing before laying out the actual board

The PCB and battery envelopes overlap in footprint (there isn't room to put
them fully side-by-side at this size) and are separated only by stacking in
Z. That means **the real board can't be a plain rectangle** — it needs an
L-shaped or notched outline (or a mounting bracket) to nest around the
battery on the same level, the same way most compact earbuds/hearing aids
handle this. Worth deciding before committing to a board outline, whichever
CAD tool ends up drawing it (Altium or a further KiCad rescale).

## Verified, not assumed

Every cutout and every fit check in this model was confirmed with OCCT's
`BRepClass3d_SolidClassifier` — testing whether specific real-world points
are inside/outside the actual solid — not by eyeballing a rendered preview.
This mattered: an early version's microSD cutout *looked* plausible in a
render but a solid-classification check caught that it had completely
missed the body due to a workplane-normal sign assumption that turned out
to be wrong for that named plane. Re-verify the same way after any
parameter change, especially port positions.

## What this is NOT yet

- **No real ear-fit data.** The hook curvature (5.5mm arc radius) is a
  reasonable generic guess, not fit to any anthropometric ear dataset.
  Real hearing aid manufacturers iterate this against actual ear
  measurements or 3D scans — this hasn't been done here.
- **No snap-fit or screw-boss features** between the top/bottom shells yet
  — right now they're just a flat split, not a manufacturable fastening
  method.
- **No DFM (draft angles, minimum wall thickness for the actual material/
  process) pass** — dimensions assume idealized geometry, not a specific
  injection-molding or SLA process's real constraints.
- **The PCB/battery envelopes are placeholders**, not the actual routed
  board — once a real board outline exists (matching the L-shape/notch
  finding above), re-run the fit check against its real outline, not this
  simple rectangle.

## Files

- `haven_enclosure_assembled_v1.step` — full shell (both halves fused), for
  viewing/reference.
- `haven_enclosure_top_shell_v1.step`, `haven_enclosure_bottom_shell_v1.step`
  — the two actual printable/moldable parts.
- `generate_enclosure.py` — the CadQuery source. All dimensions are named
  constants at the top; re-run after editing to regenerate the STEP files.
- `preview_iso.png`, `preview_internal_fit_check.png` — renders.
