# Fit-test prints (empty shells - no electronics)

Purpose: find out by trying it in an ear, not by guessing, whether the v3
outer shape is comfortable and stable, BEFORE anyone designs a final board
around it. Three scales of the v3 body, all with the **same nozzle**:

| File | Body scale | Size (mm) | Nozzle |
|---|---|---|---|
| haven_fit_test_S.stl | 0.9 | 19.5 x 18.1 x 34.5 | 5.4 mm, 6.2 mm lip |
| haven_fit_test_M.stl | 1.0 | 21.6 x 19.6 x 37.6 | 5.4 mm, 6.2 mm lip |
| haven_fit_test_L.stl | 1.1 | 23.8 x 21.1 x 40.8 | 5.4 mm, 6.2 mm lip |

Regenerate with `python generate_fit_test_prints.py` (writes the STLs and
`preview_fit_test_SML.png`).

**Changed 2026-10-28:** the first set (Sep 18) scaled the whole part, so the
nozzle went 4.9 / 5.4 / 5.9 mm. Ear-canal size is handled by the ear tip's
size, not the nozzle's, so every body now takes the same 5.4 mm nozzle
(`../../rev_a_shell/nozzle.py`) and the same tip family. Bodies are now plain
hollow mocks (1.2 mm wall, no electronics cut-outs); the nozzle bore opens into
the hollow so resin can drain.

## How to print
Resin (SLA) gives a smooth, comfortable surface; FDM works if sanded. Cornell
RPL's free printing is for project teams and MAE classes, so a personal
project may need the Phillips Hall Maker Club or a print service instead
(see `../../rev_a_shell/README.md`).
Put a soft silicone or foam ear tip on the nozzle; never push a hard nozzle
into the canal. This is a fit mock, not a functional or acoustic prototype.

## What to record (each size, each ear if possible)
- Does it stay in with head movement / chewing / jogging?
- Pressure points (concha, tragus, antitragus, canal entrance)?
- Comfort at 15 min and 1 hour.
- Does the head protrude much? (Photo from front and side.)
- Which tip size (S/M/L) seals, and does the tip stay on the nozzle?

## Reference numbers this was checked against
Ear-canal length ~31 mm avg; entrance ~6-9 mm wide x 8.5-12.5 mm tall;
narrowest point (isthmus) ~5.7 mm wide x ~9 mm tall; housings that fit inside
the concha are ~11-16 mm wide; concha-back-wall to canal ~15-20 mm.
Sources: CT ear-canal geometry study (PMC10219681), Hearing Health &
Technology Matters concha/canal series. The v3 head (~21 x 18 mm) is larger
than the concha cavity, so it sits partly outside the ear - expected, but the
fit test is what says whether it is acceptable.

## What sets the minimum size (why this may not shrink much yet)
- Radio module MDBT53: 9.3 x 14.3 mm (largest part).
- Battery in the model: 14.1 mm coin cell. A smaller pouch cell or a bare
  nRF5340 chip (custom RF design) are the real routes to a smaller head -
  both are later-revision work, after the dev board proves the chips work.
