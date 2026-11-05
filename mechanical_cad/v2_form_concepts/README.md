# v2 form-factor concepts: same parts, different shapes

Paul asked whether the v2 "stacked" pebble (`../v2_ergonomic_shell/`) is really ergonomic, and
what an AirPods-style or other shape would look like. **The parts are fixed** (his choices):
CP1254-or-better battery life, an 8 mm 16–32 Ω dynamic driver, MDBT53V-1M, ADAU1860, SPH0641
outer mic, the `nozzle.py` nozzle, two charging pads + magnet. Only the shape changes. Every
concept is scored in the same six scanned ears with the same pose search and metrics as the
ergonomic study.

## Result in one paragraph

**Among the earbud-shaped options, the current stacked pebble is still the best fit.** An
AirPods-style stem doesn't help with these parts: with the battery in the stem the bud gets
heavy (6.9 g) and levers itself out of the ear (about twice the stacked bud's tipping moment);
with the battery kept in the head (AirPods Pro's split) it sits about 1 mm flatter on average
but presses a little more and weighs 0.5 g more. The "bean" (battery beside the driver) is the
nestled layout already scored, and it fits worse. **The behind-the-ear concept is in a different
league for the ear itself** (about a third of the skin pressure, flush below the tragus, almost
no tipping force) and has the most battery, but it isn't an earbud: a pod behind the ear and a
thin cable, which affects glasses, helmets, sleeping, the case and the look Paul wants before
showing it to people. **No concept reduces battery life**: every one is at least the CP1254.

## Concepts

| Concept | Where the parts go | Battery | Battery life (loud / quiet) |
|---|---|---|---|
| **Stacked pebble (current)** | `../v2_ergonomic_shell`: driver on the canal axis, CP1254 just outside it, board + module outermost | VARTA CP1254, 60–77 mAh | 6.4–8.2 h / 13.7–17.6 h |
| **Stem, cell in the stem** (`stem_cyl`) | Head: driver + v2 board (module outward) + mic. Stem: one cylindrical cell, pads + magnet at the tip | GP Batteries GP1018L10, Ø10.5 × 18 mm, 100 mAh min / 105 typ | 10.7–11.2 h / 22.9–24.0 h |
| **Stem, CP1254 in the head** (`stem_head_cell`) | Head: driver + CP1254 + codec board + mic. Stem: module + power board, antenna at the stem's outer end, pads at the tip | VARTA CP1254 | 6.4–8.2 h / 13.7–17.6 h (same as now) |
| **Bean + wing** | The ergonomic study's nestled layout (CP1254 beside the 8 mm driver, board on top) with the concha wing; reused, not regenerated | VARTA CP1254 | same as now |
| **Behind-the-ear, receiver in canal** (`bte_inear` + `bte_pod`) | In-ear unit: driver + mic on a small flex + cable boss. Pod: CP1454 + v2 board + pads + magnet | VARTA CP1454, 85–120 mAh | 9.1–12.8 h / 19.4–27.4 h |

Battery life = capacity × 80 % usable ÷ hear-through current (~7.5 mA loud, ~3.5 mA quiet, from
`POWER_BUDGET.md`). **A stem needs a cylindrical cell.** The only small cylindrical Li-ion with
a public datasheet that beats the CP1254's capacity was the GP1018L10 (3.7 V, 100 mAh min,
Ø10.5 × 18 mm with sleeve). Slimmer TWS "pin" cells (Ø6–8 mm) are used in commercial earbuds, but no
datasheet or small-quantity source turned up for one with at least 60 mAh. That is why this
stem is thick (about Ø13.5 mm outside).

## Fit in six scanned ears (HUTUBS, right ears pp48, pp81, pp30, pp3, pp12, pp57)

Mean / worst across the six ears. Compression = deepest point pressed into skin (rigid-skin
model, 0.5 mm allowed); area = skin pressed more than 1 mm; protrusion = how far it stands out
past the tragus; moment = gravity's pull about the canal entrance (lower = less tendency to work
loose).

| Concept | Size (bounding box, mm) | Mass | Max compression | Area pressed > 1 mm | Contact | Protrusion | CoM off canal axis | Tipping moment |
|---|---|---|---|---|---|---|---|---|
| **Stacked pebble (current)** | 21.6 × 15.8 × 23.3 | 4.63 g | 3.7 / 4.5 mm | **323** / 527 mm² | 562 mm² | +7.8 / +10.6 mm | 4.4 mm | 0.49 N·mm |
| Stem, cell in the stem | 19.8 × 34.6 × 22.4 | 6.92 g | 4.1 / 4.4 mm | 465 / 602 mm² | 527 mm² | +9.7 / +18.5 mm | 9.5 mm | **0.91 N·mm** |
| Stem, CP1254 in the head | 19.4 × 33.0 × 22.3 | 5.13 g | 3.9 / 4.7 mm | 411 / 507 mm² | 561 mm² | **+6.7** / +13.3 mm | 2.9 mm | 0.59 N·mm |
| Bean + wing (nestled + fin) | 18.9 × 29.1 × 16.9 | 4.63 g | 4.3 / 5.7 mm | 429 / 591 mm² | 442 mm² | +8.0 / +12.2 mm | 6.9 mm | 0.40 N·mm |
| BTE in-ear unit | 12.5 × 15.5 × 15.9 | 1.37 g | **2.7** / 3.2 mm | **122** / 211 mm² | 267 mm² | **−2.4** / −0.5 mm | 1.6 mm | **0.06 N·mm** |
| Block (old fit study) | 21.5 × 20.5 × 24.7 | 5.12 g | 4.5 / 5.7 mm | 711 / 897 mm² | 598 mm² | +7.8 / +10.1 mm | 3.5 mm | 0.52 N·mm |

Notes on the stems: in three ears (pp81, pp30, pp3) the best pose for the cell-in-stem bud
swings the stem forward and out instead of down (its lowest point is only ~9 mm below the canal
entrance, and it stands out up to 18.5 mm), because hanging straight down it presses into the
antitragus. In the other ears it hangs 23–27 mm below the canal entrance.

**Behind-the-ear pod** (CP1454 pod, 17.8 × 33.4 × 9.2 mm, 4.77 g): `pod_fit.py` tried to seat it
in the groove behind each pinna, but **that check is not reliable**. The scan crops stop about
40 mm behind the ear and ±55 mm vertically, so in some ears (pp48, pp57 in the render) the pod
came to rest at the crop's cut edge instead of on real scalp. Its numbers in `fit_bte_pod.json`
(117–247 mm² contact, 0–28 % hidden behind the pinna from the side) are recorded but shouldn't
be quoted. What is solid: a 33 × 18 × 9 mm pod behind the ear is the size of a typical
behind-the-ear hearing aid, so expect it to be visible. Checking it properly needs uncropped
head meshes (the full HUTUBS heads are available) and a model of the cable over the ear.
The in-ear unit carries the outer mic, which
is the better place for hear-through: a mic at the canal entrance keeps the pinna's natural
direction cues; one on the pod above the ear loses them.

## Practical trade-offs

| | Stacked (current) | Stem (cell in stem) | Stem (CP1254 in head) | Bean + wing | Behind-the-ear |
|---|---|---|---|---|---|
| Hours of wear | Good; presses in small ears | Heavier, levers out | Like current | Worse fit | Best for the ear; pod rests on the head |
| Sleeping on that side | Poor (sticks out ~8 mm) | Poor | Poor | Poor | In-ear unit is flush; pod would press |
| Helmets, hats, glasses | Fine | Stem can catch | Stem can catch | Fine | Conflicts with glasses arms and some helmets |
| Stability running / chewing | OK, wing optional | Worst (weight on a lever) | OK | OK | Very stable (cable + pod anchor it) |
| Case | Simple, two pockets | Tall slots for stems | Tall slots for stems | Simple | Bigger case; cable has to be stowed |
| Manufacturing | One shell, one board | Head + stem + flex; cylindrical cell | Head + stem, two boards + flex | One shell, one board | Two shells, cable assembly, strain relief |
| Radio (BLE) | Module outermost: good | Module in head: OK | Antenna at the stem end: best | Module on top: good | Antenna behind the ear: OK; head shadows the far side |
| Looks like an earbud | Yes | Yes (AirPods-like) | Yes (AirPods-like) | Yes | No (hearing-aid look) |

## Recommendation

Keep the **stacked pebble** as the v2 shape. If the AirPods look matters, the only stem worth
trying is **CP1254 in the head with a short module stem**: it stands out about 1 mm less on
average and puts the antenna in the best place, but presses somewhat more (411 vs 323 mm² pressed
on average), weighs 0.5 g more and needs two boards instead of one. Don't put the battery in the stem. If comfort for long shifts matters more than
looking like an earbud, the **behind-the-ear** design is clearly the most comfortable in the
ear and has the longest battery life. That's a product decision, not an engineering one.
Whatever is chosen, the real test is still a print in a real ear (S/M/L tips).

## Ear data (licence) and limits

HUTUBS HRTF database, TU Berlin: Brinkmann, Dinakaran, Pelzer, Wohlgemuth, Seipel, Voss,
Grosche, Weinzierl (2019), doi:[10.14279/depositonce-8487](https://doi.org/10.14279/depositonce-8487).
**CC BY 4.0.** The meshes are not stored in this repo (see `../v2_ergonomic_shell/extract_ears.py`).
Any image or model showing them needs this attribution.

Limits, in addition to the ergonomic study's (closed canals overstate compression near the
nozzle for every shape; rigid skin; one canal angle with ±15° search; six ears):
- The stem's swing is limited to the same roll ±60° / tilt ±15° search as the pebble; a real
  stem would also be shaped (curved) to clear the antitragus.
- The pod check ran on cropped ear scans and is not reliable (see above); it also doesn't model
  glasses or the cable route. Pod mass rests on the head, so no tipping moment is given for it.
- Part masses: GP1018L10 3.5 g and CP1454 2.5 g are estimates (no mass in the snippets found).
- The cable boss in the in-ear unit sits 0.2 mm from the driver (it's shell plastic, not a part).

## Files

- `concepts.py` builds every shell and part (`python3 concepts.py [stem_cyl] [stem_head_cell] [bte]`).
- `run_fit.py <ears dir> <tag> [crop]` scores a shell in the six ears (`fit_<tag>.json`);
  `pod_fit.py <ears dir>` seats the pod (`fit_bte_pod.json`).
- `render_export.py <ears dir> <export dir>` writes the previews below and the explorer exports
  (GLB + part positions for each concept seated in ear pp3; the GLBs embed the CC BY attribution).
- Shells: `stem_cyl_shell.stl`, `stem_head_cell_shell.stl`, `bte_inear_shell.stl`,
  `bte_pod_shell.stl`; parts in `parts_<tag>/` with `parts.json`. `geometry.json` has sizes,
  clearances (every part ≥ 0.4 mm of air), mass, centre of mass and battery life.
- Previews: `preview_<tag>_iso.png`, `preview_<tag>_section.png`, `preview_<tag>_in_ears.png`
  (pp48 / pp3 / pp57; the BTE render's pod placement is not reliable). Bean + wing previews are in `../v2_ergonomic_shell/preview_v2_nestled_*`.
