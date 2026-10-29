# Rev B fit study: earbud and charging case

A packaging study. It places real part envelopes for Rev B (compact board, charging-case
contacts instead of USB-C) and finds the smallest shell that holds them with the seal spec's
nozzle. It is not a styled product: the shell is a rounded block around the parts. The
v3-style lofted surface (`../haven_dev_board_enclosure_v1/inear_v3_lofted/`) gets applied once
the internals stop moving.

Regenerate everything with `python3 generate_rev_b_fit_study.py` (CadQuery 2.7, about 3 min).
It writes the STEP/STL files, the preview PNGs and `results.md` (every check, pass/fail).

## Result

| Bud | Envelope incl. nozzle (x × y × z, mm) | Bounding box |
|---|---|---|
| Raytac MDBT53V-1M module, 8 mm driver | 16.7 × 18.9 × 23.5 | 7.4 cm³ |
| Raytac MDBT53V-1M module, 6 mm driver | 16.3 × 18.8 × 22.9 | 7.0 cm³ |
| Insight SiP ISP2053-AX module, 8 mm driver | 16.7 × 18.9 × 22.6 | 7.1 cm³ |
| Insight SiP ISP2053-AX module, 6 mm driver | 16.3 × 18.8 × 22.0 | 6.7 cm³ |
| OpenEarable 2.0 front shell (Rev A) | 16.6 × 34.6 × 21.2 | 12.2 cm³ |
| AirPods Pro (2nd gen) bud, Apple spec (includes the stem) | 21.8 × 30.9 × 24.0 | 16.2 cm³ |

- **The bud's head is 16.7 × 18.9 × 17.5 mm (MDBT53V, 8 mm driver), plus a 6 mm nozzle.** Its bounding box is about
  40% smaller than Rev A's shell, mostly because the 32 mm-long board and USB-C are gone.
- **The battery sets the footprint, not the module.** The Ø12.1 mm CP1254 cell is wider than
  either board, so the much smaller ISP2053 module only saves height (~0.9 mm), not footprint.
  Pick the module on supply and RF, not on size.
- **The 6 mm driver saves only 0.6 mm** of height. Keep the 8 mm class unless a real part
  measures worse.
- **Case: 53.5 × 45.5 × 25.5 mm** for two buds, a 502030 LiPo (~250 mAh, flat, behind the buds),
  a 25 × 20 mm case PCB stacked on the battery, USB-C out the back, 2 pogo pins per bud.
  That is 0.5 mm over the 25 mm height target; a 1.2 mm case wall instead of 1.5 mm, or 0.5 mm
  less internal clearance, gets it under.

All checks pass (`results.md`): no part overlaps another, every part is at least 0.3 mm from
the bud's inner wall, the magnet does not penetrate the wall, the nozzle bore is open from the
tip into the speaker cavity, and in the case every bud, pogo pin, the battery and the PCB clear
each other and the case walls.

## Layout (bud frame: +Z points out of the ear, the nozzle points -Z)

Bottom to top: speaker (front facing the nozzle) → 0.3 gap → CP1254 battery → 0.3 gap →
bottom-side parts (codec, PMIC, crystals, passives; 1.0 mm) → 0.8 mm board → module, antenna end
toward +Y. The battery is pushed toward -Y so the module's antenna end overhangs it by 2.5 mm,
keeping the battery can out from under the antenna. The SPH0641 mic stands against the +X wall
next to the board with a Ø0.8 mm port. A Ø3 × 2 mm magnet sits against the -X wall in the
speaker band, flanked by two Ø1.6 mm gold charging pads through that wall. -X is the bud's
smallest dimension, so in the case each bud lies on that face, pads down onto pogo pins.

The nozzle is `nozzle.py` copied from the Rev A shell work (`../rev_a_shell/`, haven-hardware
PR #2): Ø5.4 mm shaft, Ø6.2 mm lip, Ø3.0 mm bore, 5.5 mm long, tilted 15° toward +Y. No vent.

## Speaker decision: dynamic driver, not the Knowles ED-29689 balanced armature

The ADAU1860's headphone output is specified at 16, 24 and 32 Ω loads (about 30–50 mW at
AVDD = 1.8 V, datasheet Rev. B Table 1, p. 8; the repo's power budget uses 1 mW into 32 Ω).
The ED-29689 is 10.2 Ω, below every specified load, so driving it would be off-datasheet
(and it costs ~€26 each). A 16–32 Ω dynamic micro driver sits inside the codec's specified
range and gives more bass in a sealed fit. The 8 mm (Ø8.0 × 3.6) and 6 mm (Ø6.0 × 3.0)
envelopes here are representative TWS driver sizes, **not a specific part**: the catalog
distributors (DigiKey, Mouser, PUI Audio) don't list small 16–32 Ω earbud drivers, so the
real part will likely come from an earbud-driver supplier and must be measured.

## Assumptions to confirm before layout

- **Real part datasheets:** speaker (impedance 16–32 Ω, depth), MDBT53V-1M and ISP2053 land
  patterns and keepouts (the 2.5 mm antenna overhang is a placeholder for the module's actual
  keepout), CP1254 exact version (60–77 mAh, with or without built-in protection).
- **Board thickness 0.8 mm** here vs 1.6 mm on Rev A. OpenEarable's 1.6 mm 6-layer stackup
  would add 0.8 mm of height. JLCPCB builds 6 layers at 0.8 mm, but the stackup and impedance
  need checking.
- **Bottom-side parts fit in 1.0 mm** and on a 9 × 13 (or 9 × 9) board: the nPM1100 (2.1 × 2.1)
  vs the BQ25120A (2.5 × 2.6) charger footprint, the ADAU1860 (3.0 × 2.7), crystals and
  passives. This needs a real placement before it is trusted.
- **Pad wiring:** the pads sit in the speaker band, away from the board. They need a short flex
  or spring contacts up to the board.
- **Magnet strength:** a Ø3 × 2 mm N52 disc per bud plus one under each pocket in the case.
  Check that it holds the bud on the pogo pins (pogo spring force) and that it is far enough
  from the speaker's magnet and the module's antenna.
- **Mic routing:** the mic stands beside the board and needs a flex or a board-edge mount.
- **Case battery:** a 502030 is about 250 mAh, about 1.5 full recharges of two 60–77 mAh buds
  after losses. A 602535-class cell or similar gives about 3 recharges for a few mm more.
- **Hinge:** not modeled. The lid split is a plane at 60% of the case height.

## Files

- `generate_rev_b_fit_study.py` – the parametric model and checks. `nozzle.py` – shared nozzle.
- `bud_mdbt53v.*`, `bud_isp2053.*` – the bud shell (STEP/STL); `*_assembly.*` adds the parts.
- `case_base.*`, `case_lid.*`, `case_assembly.*` – the case concept.
- `preview_bud_<variant>_iso.png` (cutaway), `_exploded.png`, `_section.png`; `preview_case_iso.png`.
- `results.md` – the generated check results and envelopes.
