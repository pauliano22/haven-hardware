# Haven v2, behind-the-ear (BTE) mechanics

The form factor Paul chose on 2026-11-03: an in-ear unit (speaker, and the mic in variant A) is
joined by a fixed 6-wire cable over the helix root to a pod behind the ear. The pod holds the
battery, radio, codec and charging contacts. The design builds on `../v2_form_concepts`
(`bte_inear` + `bte_pod`) and uses the same shell construction and fit scoring as
`../v2_ergonomic_shell`.

These are concept shells, not production CAD. They are good enough to fix the board outlines and
height limits and to make a first print. Fit has been checked only against rigid ear scans, not
on a real ear.

## Parts

| Part | Size (mm) | Mass | Contents |
|---|---|---|---|
| In-ear unit **A** (mic in ear, primary) | 13.8 × 15.7 × 18.6 | 1.6 g | Ole Wolff OWR-0860T-16 driver (Ø9 × 4.5), 6 × 6 mm 2-layer board. The SPH0641 is bottom-port, so it sits under the board (driver side) and hears through a plated hole in the board that lines up with the shell's mic hole. Cable pads on top, strain-relief boot, 1.7 mm cable hole for the 1.5 mm 6-wire harness |
| In-ear unit **B** (fallback: mic on pod) | 13.7 × 14.9 × 17.0 | 1.5 g | Driver only, 1.4 mm hole for a standard 2-wire receiver cable |
| Pod (L and R mirrored) | 19.5 × 33.2 × 11.4 | 5.4 g | 13 × 27 × 0.8 mm board; VARTA CP1454 and MDBT53V-1M on the lateral face (module antenna flush with the top edge); codec, PMIC and passives on the medial face, ≤ 1.0 mm tall; optional pod mic U14 port; 2 charging pads + magnet on the bottom end |

Every part keeps at least 0.3 mm of air inside its shell. All shells are watertight. For
comparison, an AirPods Pro 2 bud weighs about 5.3 g and sits entirely in the ear. Here the ear
holds only 1.6 g, and most of the mass hangs behind it.

## Fit on six scanned heads (HUTUBS)

The scoring is the same as `v2_ergonomic_shell`: rigid skin, 0.5 mm of allowed compression, and
canal points excluded.

| Head | In-ear A max compression | Area > 1 mm | Protrusion past tragus | Pod max compression | Cable length | Cable clears skin by 1 mm |
|---|---|---|---|---|---|---|
| pp48 | 4.4 mm | 323 mm² | −0.7 mm | 0.50 mm | 57.2 mm | no (0.18) |
| pp81 | 3.8 mm | 199 mm² | +3.4 mm | 0.46 mm | 43.7 mm | yes |
| pp30 | 2.8 mm | 138 mm² | +0.5 mm | 0.45 mm | 43.5 mm | yes |
| pp3 | 3.3 mm | 144 mm² | +1.0 mm | 0.46 mm | 43.3 mm | yes |
| pp12 | 2.2 mm | 137 mm² | −4.6 mm | 0.49 mm | 51.5 mm | no (touches) |
| pp57 | 3.6 mm | 264 mm² | −0.7 mm | 0.47 mm | 47.9 mm | no (touches) |

Variant B (2.2–3.9 mm, 109–286 mm²) scores almost the same as A. Moving the bottom-port mic under
the board made A 1 mm deeper, and its worst-ear compression went from 3.9 to 4.4 mm (pp48). The
mean area barely moved (199 → 201 mm²).

What this means:
- **Pod: fine.** It presses less than 0.5 mm into every head.
- **In-ear unit: better than the earbud shells, but not done.** Area pressed over 1 mm averages
  201 mm², against 323 mm² for the best earbud shell (v2 stacked). The unit sits flush with or
  inside the tragus instead of sticking out about 8 mm. But it still presses 2–4.4 mm at one spot
  in every head. It is a rigid shell in a rigid scan, so the real number is lower: skin gives,
  and a soft tip takes up the canal. Still, the shell needs another pass before people wear it:
  a smaller concha body, or S/M/L sizes the way hearing-aid receivers come in sizes.
- **Cable: 43–57 mm over the helix root.** Make the harness 55 mm from the boot to the pod, or
  offer 45 / 57 mm sizes. Where it "touches", it rests on the skin at the helix root, which is
  how every receiver-in-canal hearing aid sits.

## Board outlines (for layout)

- `board_pod_outline.dxf` is 13 × 27 mm. Layers: `Edge.Cuts`, `KEEPOUT_TOP_BATTERY` (CP1454
  footprint), `KEEPOUT_TOP_MODULE`, `ANTENNA_EDGE` (top edge, module antenna flush),
  `MIC_PORT_HOLE` + `KEEPOUT_TOP_GASKET` (pod mic U14 port), and `NOTES`. Bottom (medial) side
  parts: ≤ 1.0 mm tall.
- `board_inear_outline.dxf` is 6 × 6 mm, 2-layer. Layers: `BOTTOM_MIC` (SPH0641 on the driver
  side), `MIC_PORT_HOLE` (0.7 mm, board centre) and `KEEPOUT_TOP_GASKET`. Laid out in
  haven-dev-board-kicad PR #18.

## Files

- `bte_inear_A_{L,R}`, `bte_inear_B_{L,R}`, `bte_pod_{L,R}` `.stl` / `.step`. The STL is the
  master. The STEP is a faceted solid for print services.
- `parts_*/`: placed part solids plus `parts.json`, for layout cross-checks.
- `geometry.json`: sizes, clearances, mass, centre of mass, cable exit/entry points.
- `fit_bte.json` / `fit_bte.log`: per-head poses and scores, with the cable path.
- `preview_fit_pp*.png`, `preview_shells_iso.png`: each head's fit (outside, behind, below) and iso views of the shells.

Regenerate:
```
python3 bte.py                                   # shells, parts, DXFs, geometry.json
python3 fit_bte.py ~/.cache/hutubs/ears_bte      # fit (slow, ~1 h)
python3 refit_inear_A.py ~/.cache/hutubs/ears_bte # re-score unit A only
python3 cable_route.py ~/.cache/hutubs/ears_bte  # cable routes into fit_bte.json
python3 render_bte.py ~/.cache/hutubs/ears_bte   # renders
```
Use plain `python3`, not `python3 -I`. trimesh is in the user site-packages.

Ear/head scans: HUTUBS HRTF database, TU Berlin (Brinkmann et al. 2019), CC BY 4.0,
doi:10.14279/depositonce-8487.

## In-ear reshape + comfort sleeves (2026-11-05)

**Why:** the in-ear unit pressed 2.2–4.4 mm into all six scanned ears. Slices at canal height
showed the cause: the 9 mm driver's housing sat centred on the canal and hung ~6 mm below it, into
the intertragic notch and the lower rim of the canal opening.

**Sweep** (`fit` on the six HUTUBS ears, pose search allowing up to 3 mm pull-out), body moved
perpendicular to the canal axis, nozzle fixed:

| Body offset | Mean worst press | Mean area > 1 mm |
|---|---|---|
| none | 3.17 mm | 159 mm² |
| back 2 | 3.15 | 144 |
| up 2 | 2.33 | 80 |
| up 2 + back 1.5 | 2.22 | 77 |
| up 2 + forward 1.5 | 2.27 | 79 |
| **up 3** | **2.03** | **63** |

Most best poses also pulled the unit 3 mm out, so `bte.py` now moves the body **3 mm up and 3 mm
out** and the nozzle grows **5.5 → 8.5 mm** (ear-tip depth unchanged). 3 mm is the most the 3 mm
bore can move off the 9 mm driver and still face it; the bore now meets the driver face at its
edge, through the 0.4 mm front gap (normal for offset-nozzle IEMs; check the sound by ear).

**Result** (`refit_inear_A.py`, full pose search, unit A):

| Ear | Before: worst / area | After: worst / area |
|---|---|---|
| pp48 | 4.4 / 323 | 2.9 / 160 |
| pp81 | 3.8 / 199 | 2.5 / 54 |
| pp30 | 2.8 / 138 | 1.5 / 13 |
| pp3 | 3.3 / 144 | 0.8 / 0 |
| pp12 | 2.2 / 137 | 1.3 / 7 |
| pp57 | 3.6 / 264 | 1.8 / 44 |
| mean | 3.35 / 201 | **1.77 / 46** |

Trade-off: it sticks out ~2–3 mm more (protrusion past the tragus now −1.5 to 5.8 mm). The mass
centre moved off the canal axis (moment 0.05 → ~0.1 N·mm, still negligible). Unit A is now
14.7 × 15.7 × 21.7 mm, 1.67 g. Cable routes: 34–51 mm, so the 55 mm harness still fits.

**Comfort sleeves** (`sleeves.py` → `sleeve_{M,L}_{L,R}.stl`, `sleeves.json`): S = bare shell;
M / L = a 0.8 / 1.5 mm soft band over the concha part of the body (faceplate and nozzle bare).
Scored as if rigid, both make the press **worse** on all six scanned ears (mean worst 1.77 → 2.55
(M) → 3.32 mm (L)): all six are "S" ears. The sleeves are for ears larger than any in this small
dataset, where the bare body would sit loose, and to put silicone rather than resin on the skin.
Real silicone gives under load, so the rigid score overstates them. Print M/L in flexible resin
for the real-ear test; the seal is still the standard S/M/L ear tip.

**Speaker size** (2026-11-06): `HAVEN_DRIVER=8.0x3.9 HAVEN_OUT=<dir> python3 bte.py` rebuilds for
another driver (BODY_UP clamps to driver radius − 1.5). An 8 × 3.9 mm driver fits better: mean worst
1.53 mm / area 31 mm² vs 1.76 / 46 for the 9 mm (pp48 2.7/114, pp81 1.8/39, pp30 1.1/3, pp3 0.9/0,
pp12 0.9/0, pp57 1.8/28). Plan: generic 8 mm TWS drivers first, OWR-0860T-16 as backup.

## Charging case (2026-11-05)

`case.py` → `case_base.stl`, `case_lid.stl`, `case_plate.stl`, `board_case_outline.dxf`, `case.json`;
`render_case.py` → `preview_case.png`. Schematic: haven-dev-board-kicad `kicad_v2_case/`.

- **48.6 × 50.6 × 49.9 mm** closed. Base, lid (friction fit over a 3 mm lip, 0.15 mm per side) and
  a 1.4 mm bottom plate. All three meshes are watertight.
- **Pod wells:** each pod stands upright, and its well is the pod's own lower envelope dropped
  straight down plus 0.35 mm, 14 mm deep. The pod rests on its lowest point, which is its charge
  end. Pods vs base: no intrusion (closest 0.16–0.19 mm).
- **Contacts:** two Ø1.6 mm spring-pin holes per pod through the floor, **5.0 mm apart** around a
  3 × 2 mm magnet pocket under the floor (it pulls on the pod's own magnet). Positions are in
  `case.json` → `contacts` and on the DXF's POGO layer.
  **Pod contact pins should be lengthened to 3.5 mm (Ø1.5 brass) so they sit flush with the pod
  shell.** As modelled they are 1.2 mm, recessed 2.3 mm inside the shell, which a short spring
  pin can't reach.
- **In-ear pocket** at the front, 44 × 25.5 × 12 mm: both in-ear units stand nozzle-up with tips on
  and clear the base by ~0.3 mm (checked with signed distance, not shown in the render). Their
  tops are at 22.6 mm; the lid's inside is at 36.6 mm, which leaves room for the cable loops.
- **Electronics bay** under the floor, 8 mm tall: the case board (1.0 mm) lies on the bottom plate as
  a 44 × 15.5 mm strip at the back, under the pods. USB-C sits on its back edge, at x = −2 mm in the
  back-wall opening; the charge LED shines through a Ø1.5 mm hole in the back wall. The 603040 LiPo
  (6 × 30 × 40 mm) lies sideways in front of it.
- **Spring pins:** candidate Kinghelm KH-PG2011005-DZ (LCSC C2842935): SMD, 11 mm free length, 2 mm
  base. The board's top sits `POGO_WORK_H` = 10.0 mm below the (flush) pod contacts, i.e. ~1 mm of
  compression. Its stroke isn't published on LCSC: measure a real pin, set `POGO_WORK_H` in
  `case.py` and rerun it (the bay height follows).
- Not done: the lid has no magnets or hinge yet (friction fit only), there are no cable-loop
  guides. The case board is laid out (haven-dev-board-kicad `kicad_v2_case/`).
