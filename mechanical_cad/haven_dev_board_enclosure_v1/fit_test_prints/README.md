# Fit-test prints (empty shells - no electronics)

Purpose: find out by trying it in an ear, not by guessing, whether the v3
outer shape is comfortable and stable, BEFORE anyone designs a final board
around it. Three uniform scales of the same v3 shape:

| File | Size (mm) | Nozzle |
|---|---|---|
| haven_fit_test_S.stl | 19.7 x 18.1 x 35.2 | 4.9 mm |
| haven_fit_test_M.stl | 21.9 x 20.1 x 39.1 | 5.4 mm |
| haven_fit_test_L.stl | 24.0 x 22.1 x 43.0 | 5.9 mm |

## How to print
Cornell RPL offers free 3D printing (see HARDWARE_COST_ALTERNATIVES.md).
Resin (SLA) gives a smooth, comfortable surface; FDM works if sanded.
Add a soft silicone/foam ear tip on the nozzle - do not push a hard nozzle
into the canal. This is a fit mock, not a functional or acoustic prototype.

## What to record (each size, each ear if possible)
- Does it stay in with head movement / chewing / jogging?
- Pressure points (concha, tragus, antitragus, canal entrance)?
- Comfort at 15 min and 1 hour.
- Does the head protrude much? (Photo from front and side.)
- Nozzle: too tight, too loose?

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
