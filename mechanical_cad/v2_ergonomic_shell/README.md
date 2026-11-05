# v2 ergonomic shell: in-concha bodies fitted against real ear scans

Paul's feedback on the fit-study bud (`../rev_b_fit_study/`): it reads as a cube and might
fall out. This folder replaces the rounded block with organic bodies built around the same v2
internals, and scores every shape in six scanned human ears instead of by eye.

## Result in one paragraph

**The stacked layout (`v2_stacked`) is the better design and halves the block's tissue
interference** (mean area pressed > 1 mm into skin 323 vs 711 mm²; worst-ear compression
4.5 vs 5.7 mm) at the same contact area and protrusion, and it is 0.5 g lighter.
The lower-profile "nestled" layout looked better on paper (11.6 mm above the canal entrance)
but scored worse in real ears: a 12.1 mm battery beside an 8 mm driver spans ~26 mm, longer
than most cavum conchas (11–22 mm wide in HUTUBS), so the pose search has to tip it out.
**No shape fits every ear yet.** All three still compress skin by 3–5 mm somewhere in the
smaller ears, and protrude 5–11 mm past the tragus. With a Ø12.1 mm battery plus an 8 mm
driver, the parts themselves are the limit; see "What would actually make it smaller".

## Ear data (licence)

HUTUBS HRTF database, TU Berlin: Brinkmann, Dinakaran, Pelzer, Wohlgemuth, Seipel, Voss,
Grosche, Weinzierl (2019), doi:[10.14279/depositonce-8487](https://doi.org/10.14279/depositonce-8487).
**CC BY 4.0** (repository rights field and the dataset's own documentation, both checked
2026-10-29). 58 watertight PLY head meshes (metres). Six right ears were chosen to span the
dataset's cavum concha width (anthropometric measure d3): pp48 (smallest, 11.4 mm), pp81,
pp30, pp3, pp12, pp57 (largest, 21.6 mm). The meshes are **not** stored in this repo;
`extract_ears.py` regenerates the crops from the download. Any figure or model that shows a
scan needs the attribution above.

## Method

- **Canal entrance (E).** The scans close every ear canal at its entrance, as HRTF meshes
  usually do. `extract_ears.py` ray-casts a lateral height map of the pinna, finds basins
  walled in on ≥ 13 of 16 directions within 15 mm (the cavum concha), and takes the deepest
  pixel of the largest basin as E. Tragus height = the most lateral surface 4–14 mm in front
  of E (9.8–17.0 mm above E across the six ears).
- **Canal direction.** No published numeric angle for the canal-entrance axis was found; the
  lateral canal runs "inward, forward, and slightly upward" (Gray's Anatomy). Used: 25°
  forward, 10° up from straight inward (`CANAL_ANT_DEG`, `CANAL_SUP_DEG`). The pose search
  tilts ±15° around this, which also covers per-ear variation.
- **Shell construction** (`generate_v2_ergonomic_shell.py`). The parts' exact signed distance
  fields are offset by clearance + wall, closed morphologically with a 3.5 mm radius (fills
  concavities, so the body is one smooth pebble with no corners), smoothed, and hollowed by a
  uniform 1.1 mm wall. The nozzle (`nozzle.py`: 5.4 mm shaft, 6.2 mm lip, 3.0 mm bore, no
  vent), mic port and charging-pad holes are exact CSG on the same field; marching cubes
  meshes it. Every part keeps ≥ 0.42 mm of air (spec 0.3). Earlier attempts with spine lofts
  produced self-intersecting surfaces for these layouts and were dropped.
- **Layouts.** *Stacked*: driver on the canal axis, battery stacked just outside it (as close
  to the axis as clearance allows, so the centre of mass stays near the axis), board + module
  outermost (best for the antenna, antenna end overhanging the battery by 2.5 mm), mic on a
  short flex at the far end, magnet and two charging pads at the far end. *Nestled*: driver
  faces into the canal, battery beside it in the cavum concha, board spanning both.
- **Fit scoring** (`evaluate_fit.py`). Each shell is seated with its nozzle on the canal axis.
  The search varies roll (±60°), two tilts (±15°) and insertion (±0.75 mm) and keeps the pose
  with the least tissue penetration beyond 0.5 mm of allowed skin compression, then the most
  contact. Nozzle points inside the canal are excluded. Centre of mass uses part masses
  (CP1254 1.7 g, module 0.4 g, driver 0.5 g, tip 0.1 g, board/parts/magnet/mic) plus resin at
  1.2 g/cm³; the moment is gravity (head upright) about the canal entrance.
- **Comparison.** `block_reference.py` maps the fit-study block bud into the same frame (its
  nozzle onto the same axis) and it goes through the identical search.

## Results

| Shape | Bounding box (mm) | Mass | Max compression (mean / worst) | Area > 1 mm (mean / worst) | Contact (mean) | Protrusion (mean / worst) | CoM offset (mean) |
|---|---|---|---|---|---|---|---|
| v2 stacked | 21.6 × 15.8 × 23.3 | 4.63 g | 3.7 / 4.5 mm | 323 / 527 mm² | 562 mm² | +7.8 / +10.6 mm | 4.4 mm |
| v2 stacked + fin | 25.5 × 16.2 × 23.3 | 4.66 g | 3.6 / 4.4 mm | 337 / 517 mm² | 611 mm² | +7.9 / +10.2 mm | 4.2 mm |
| v2 nestled | 16.6 × 26.3 × 16.9 | 4.61 g | 4.2 / 5.7 mm | 451 / 618 mm² | 443 mm² | +7.9 / +12.0 mm | 6.8 mm |
| v2 nestled + fin | 18.9 × 29.1 × 16.9 | 4.63 g | 4.3 / 5.7 mm | 429 / 591 mm² | 442 mm² | +8.0 / +12.2 mm | 6.9 mm |
| block (fit study) | 21.5 × 20.5 × 24.7 | 5.12 g | 4.5 / 5.7 mm | 711 / 897 mm² | 598 mm² | +7.8 / +10.1 mm | 3.5 mm |

Per ear:

| Ear (HUTUBS, right) | Cavum concha W × H (mm) | Tragus above E | Shape | Max skin compression | Area pressed > 1 mm | Contact area | Protrusion past tragus | CoM off canal axis | Gravity moment |
|---|---|---|---|---|---|---|---|---|---|
| pp48 | 11.4 × 16.9 | 11.6 | **v2 stacked** | 4.5 mm | 527 mm² | 608 mm² | +8.8 mm | 3.4 mm | 0.48 N·mm |
| pp48 | 11.4 × 16.9 | 11.6 | v2 nestled | 4.5 mm | 618 mm² | 429 mm² | +8.0 mm | 7.5 mm | 0.37 N·mm |
| pp48 | 11.4 × 16.9 | 11.6 | block (fit study) | 4.0 mm | 689 mm² | 661 mm² | +10.0 mm | 2.2 mm | 0.51 N·mm |
| pp81 | 14.5 × 19.5 | 10.5 | **v2 stacked** | 4.3 mm | 186 mm² | 540 mm² | +10.6 mm | 3.8 mm | 0.52 N·mm |
| pp81 | 14.5 × 19.5 | 10.5 | v2 nestled | 4.5 mm | 387 mm² | 362 mm² | +12.0 mm | 6.4 mm | 0.43 N·mm |
| pp81 | 14.5 × 19.5 | 10.5 | block (fit study) | 5.7 mm | 643 mm² | 588 mm² | +10.1 mm | 2.6 mm | 0.53 N·mm |
| pp30 | 15.9 × 16.9 | 13.4 | **v2 stacked** | 2.8 mm | 186 mm² | 622 mm² | +8.5 mm | 5.5 mm | 0.50 N·mm |
| pp30 | 15.9 × 16.9 | 13.4 | v2 nestled | 4.3 mm | 450 mm² | 480 mm² | +8.7 mm | 6.3 mm | 0.42 N·mm |
| pp30 | 15.9 × 16.9 | 13.4 | block (fit study) | 4.7 mm | 868 mm² | 642 mm² | +8.0 mm | 3.7 mm | 0.50 N·mm |
| pp3 | 17.5 × 16.5 | 13.2 | **v2 stacked** | 3.2 mm | 294 mm² | 519 mm² | +7.7 mm | 5.6 mm | 0.44 N·mm |
| pp3 | 17.5 × 16.5 | 13.2 | v2 nestled | 3.3 mm | 347 mm² | 531 mm² | +7.3 mm | 7.0 mm | 0.39 N·mm |
| pp3 | 17.5 × 16.5 | 13.2 | block (fit study) | 3.4 mm | 531 mm² | 602 mm² | +6.8 mm | 5.4 mm | 0.52 N·mm |
| pp12 | 19.4 × 18.3 | 17.0 | **v2 stacked** | 3.9 mm | 442 mm² | 537 mm² | +4.8 mm | 3.8 mm | 0.52 N·mm |
| pp12 | 19.4 × 18.3 | 17.0 | v2 nestled | 3.0 mm | 337 mm² | 525 mm² | +2.1 mm | 7.3 mm | 0.36 N·mm |
| pp12 | 19.4 × 18.3 | 17.0 | block (fit study) | 4.6 mm | 635 mm² | 569 mm² | +3.6 mm | 6.0 mm | 0.51 N·mm |
| pp57 | 21.6 × 18.7 | 12.9 | **v2 stacked** | 3.4 mm | 304 mm² | 545 mm² | +6.6 mm | 4.4 mm | 0.51 N·mm |
| pp57 | 21.6 × 18.7 | 12.9 | v2 nestled | 5.7 mm | 567 mm² | 333 mm² | +9.1 mm | 6.3 mm | 0.42 N·mm |
| pp57 | 21.6 × 18.7 | 12.9 | block (fit study) | 4.6 mm | 897 mm² | 526 mm² | +8.5 mm | 0.9 mm | 0.52 N·mm |


Fins: the concha-lock fin adds ~50 mm² of contact on the stacked body and doesn't change
interference much. It's a stability feature to judge on a real ear, not in this model.

## Previews

- `preview_v2_stacked_iso.png`, `preview_v2_stacked_fin_iso.png`, `preview_v2_stacked_section.png`
- `preview_v2_nestled_iso.png`, `preview_v2_nestled_section.png`
- `preview_v2_stacked_in_ears.png`, `preview_v2_nestled_in_ears.png`, `preview_block_reference_in_ears.png`
  (seated in pp48 / pp3 / pp57, smallest to largest)

## Files

- `v2_stacked_shell.stl/.step`, `v2_stacked_fin_shell.stl/.step`, `v2_nestled_shell.stl`,
  `v2_nestled_fin_shell.stl`. The STL is the master surface. The STEP (chosen layout only) is
  a faceted solid sewn from a 5k-triangle decimation, for placement and printing services,
  not for further CAD surfacing. `generate_v2_ergonomic_shell.py` re-creates all of them.
- `parts_stacked/`, `parts_nestled/`: part envelopes and charging pads as placed.
- `geometry.json` (sizes, clearances, mass, centre of mass), `fit_results.json` (per-ear scores
  and poses), `layout_cache.json` (chosen layout parameters).
- Scripts: `extract_ears.py`, `generate_v2_ergonomic_shell.py`, `evaluate_fit.py`,
  `block_reference.py`, `render.py`, `write_fit_jobs.py`, `merge_results.py`, `export_explorer.py`.

## Limits of this model

- **Closed canals.** The scans end at the canal entrance, so the real opening (7–9 mm wide)
  is solid in the model. Some of the measured "compression" around the nose is actually the
  canal opening. This affects all shapes equally, so it doesn't change the ranking, but
  absolute numbers are pessimistic near the nozzle.
- **Rigid skin.** Real concha skin and cartilage give more than the 0.5 mm allowed here,
  especially at the antitragus and crus. 3–5 mm compression is still too much, though.
- **One canal angle** with ±15° of search, and six ears. The canal entrance is a
  geometric estimate.
- **Mass properties** use datasheet/estimated part masses; the driver is a representative
  8 mm part, not a chosen one.

## What still needs a real-ear test

Print `v2_stacked_shell.stl` and `v2_stacked_fin_shell.stl` in S/M/L ear tips (one nozzle size,
standard 4.5 mm-bore tips; resin for skin contact, e.g. Formlabs BioMed Clear) and record:
seat depth, pressure points at 15 min / 1 h, retention when chewing and shaking the head,
protrusion (photo), and seal (a low-frequency hearing-test-app check with and without the bud).

## Smaller variant (2026-10-30)

Paul asked to see how much the parts cost in size. `HAVEN_VARIANT=small python3
generate_v2_ergonomic_shell.py stacked` builds the same stacked layout with a VARTA CP0854 cell
(Ø8.0 × 5.4 mm, ~40 mAh, about 5 h loud / 11 h quiet) and a representative 6 mm 16–32 Ω driver
(Ø6.0 × 3.0 mm). Outputs carry a `_small` suffix (`v2_stacked_small_shell.stl/.step`,
`parts_stacked_small/`, `geometry.json` and `fit_results.json` entries); the current design's
files are untouched. Fit search: `python3 evaluate_fit.py <ears dir> v2_stacked_small` (named jobs
are merged into the existing results). Masses are approximate (CP0854 ~1.1 g, 6 mm driver ~0.3 g).

| Variant | Bounding box (mm) | Mass | Worst / mean compression | Mean area > 1 mm | Protrusion pp3 / mean | Battery |
|---|---|---|---|---|---|---|
| Current (CP1254 + 8 mm) | 21.6 × 15.8 × 23.3 | 4.63 g | 4.5 / 3.7 mm | 323 mm² | +7.7 / +7.8 mm | ≈ 8–10 h loud |
| Smaller (CP0854 + 6 mm) | 22.1 × 12.8 × 22.3 | 3.58 g | 4.6 / 3.3 mm | 240 mm² | +7.5 / +5.8 mm | ≈ 5 h loud |

The smaller cell takes 3 mm off the depth and 1 g off the weight, and sits 2 mm lower on average,
but the 13 × 9 mm board now sets the length, so the bud is not shorter, and the smallest ear
(pp48) is still compressed by ~4.6 mm. Paul's decision on 2026-10-30 stands: keep the current
parts; this variant is for comparison in the explorer.

## What would actually make it smaller

The parts set the size. Ranked by effect on fit, all needing a schematic/stock check first:
1. **Smaller battery**: VARTA CP0854 class (Ø8 × 5.4 mm, ~40 mAh) cuts the body footprint
   by a third; runtime drops to roughly 5 h loud / 11 h quiet against the 6 h target.
2. **6 mm driver** instead of 8 mm (saves ~0.6 mm of height and 2 mm of nose width).
3. **Two body sizes** (small/large concha), since HUTUBS concha widths span 11–22 mm.
