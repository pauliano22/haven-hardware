# Rev A front shell: OpenEarable's shell with a standard ear-tip nozzle

Rev A is OpenEarable main 2.0 at its native size with unused parts removed
(see `PROJECT_STATUS.md` in haven-workspace, 2026-10-28). This folder is its
front shell: OpenEarable 2.0.1's front shell (`../OpenEarable-Enclosure-2.0.1/`)
with three changes. OpenEarable's back shell, speaker mount and battery mount
are used unchanged.

| File | What |
|---|---|
| `generate_rev_a_shell.py` | Generator plus verification checks. Run `python generate_rev_a_shell.py`. |
| `nozzle.py` | The nozzle, shared with the S/M/L fit-test prints. |
| `rev_a_front_shell.step` / `.stl` | The shell to print. |
| `rev_a_front_shell_fin.step` / `.stl` | Same, plus an experimental stabilizing fin on the back of the head (placement is a first guess; try it on an ear before trusting it). |
| `preview_rev_a_nozzle_section.png` | Section through the nozzle, original shell in gray. |
| `preview_rev_a_front_shell_iso.png`, `preview_rev_a_front_shell_fin_iso.png` | 3D views. |

## The three changes

1. **Round nozzle replaces OpenEarable's oval stem.** OpenEarable's stem is an
   oval about 5.6 x 4.5 mm with an oval flared lip, made for its own tips.
   The new nozzle sits on the same axis: 5.4 mm shaft, 6.2 mm retaining lip
   (0.4 mm high, square back face, 0.6 mm lead-in so tips slide on), 5.5 mm
   long from the head. It fits tips with a 4.5 mm bore (SpinFit CP145,
   SpinFit NEO, most generic silicone IEM tips, foam tips of that bore).
2. **Round 3.0 mm sound bore replaces the oval 5.2 x 3.4 mm channel.** Typical
   in-ear-monitor nozzle bores are about 2 to 3.5 mm; 3.0 mm leaves a 1.2 mm
   wall. The bore opens into the cavity above the speaker mount, as the old
   channel did.
3. **Sensor window closed.** The rectangular window on top of the head is
   where OpenEarable's sensor flex board (PPG, temperature) looked out. Rev A
   has no flex board, so the window gets a 1.2 mm skin. The skin is the
   head's own dome surface extended across the hole, so it sits flush.

### Nozzle angle

The nozzle keeps OpenEarable's stem axis, 40 degrees off the shell's face
normal, because that is the orientation already worn in real ears.
`EXTRA_TILT_DEG` in the generator tilts it further if fit tests say so
(10 to 20 degrees is the usual range for in-ear nozzles); nothing else needs
to change.

### Shell length

`BOARD_LENGTH_MM` is a parameter (default 28, the trimmed Rev A board), but
it doesn't shorten the shell. The 14 mm coin cell's bay runs to y = 33.75 mm,
past the end of a 28 mm board, so the battery sets the shell's 34.6 mm
length. A shorter shell needs a smaller battery, which is Rev B work. The
generator flags it if the board ever becomes longer than the battery bay.

## Sealing: what the shell does and doesn't do

There is no vent anywhere in the sound path: canal, nozzle bore, cavity,
speaker front. The other openings in the shell (USB-C, the speaker-wire
channels, two 1 mm holes at the back of the head, a small 2.5 x 1 mm slot on
top) open into the interior, not the sound path, so they only matter if
sound leaks around the speaker.

**One real risk is left for assembly.** The speaker mount is a separate part
that clips into the head. Between the mount's outer rim and the shell wall
there is a gap of roughly 0.2 to 0.35 mm (measured from the CAD). If sound
leaks through that gap, the canal connects to the interior and through it
to the openings above, which is the leak that costs low-frequency
attenuation. A printed collar can't close it: the cavity above the mount is
only about 0.6 mm taller than the mount's clips. So **seal the mount's rim
with a thin bead of silicone (RTV) or UV-cure adhesive when assembling**,
then check the seal (below).

## Printing

- Skin contact means a biocompatible resin: Formlabs BioMed Clear is
  marketed for earmolds and IEMs and rated for long-term skin contact. It is
  only biocompatible if washed and post-cured per the resin's instructions.
- Cornell RPL's free printing is for engineering project teams and MAE
  classes. A personal project may need the Phillips Hall Maker Club or a
  print service.
- Print the nozzle along its axis if the printer allows, so the lip comes
  out round.

## Check the nozzle before freezing it

The 5.4 mm shaft is chosen from published tip specs, not measured tips.
Before printing more than one shell:

1. Buy one tip variety pack with 4.5 mm-bore tips: silicone single, double
   and triple flange plus foam, S/M/L (about $15 to $30).
2. Print one shell, or just the S fit-test print, which has the same nozzle.
3. Check every tip goes on with a firm push, stays on when pulled, and
   doesn't spin loose. If tips are loose, raise `NOZZLE_OD` by 0.1 to 0.2 mm
   in `nozzle.py` (both this shell and the fit tests pick it up). If they
   won't go on, lower it.

## Checking the seal once it's assembled

With foam tips: a listening test, then a hearing-test app at 250 and 500 Hz
with and without the earpiece in. Good foam-plug-class seals block about
20 to 40 dB; a much smaller difference at 250 Hz means a leak (tip size,
insertion depth, or the speaker-mount rim above).
