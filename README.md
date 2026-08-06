# haven-hardware

Hardware design files for Project Haven. All binary CAD/PCB formats
(`.step`, `.stp`, `.stl`, `.epro`, `.xlsx`, `.pdf`, and Altium library files)
are tracked via **Git LFS** — run `git lfs install` once, then clone
normally.

## Layout

- **`openearable_base_pcb/`** — OpenEarable's official PCB exports as
  downloaded from Altium 365: main 2.0, flex 2.0, and a debugging breakout
  1.0. Each folder has schematic/layout PDFs, a BOM, and an `.epro` (Altium
  365 packaged release — open it via Altium 365's viewer or import into
  Altium Designer). No raw `.PcbDoc`/`.SchDoc` source is included upstream.
- **`mechanical_cad/`** — Enclosure CAD. `OpenEarable-Enclosure-2.0.1/` is
  the upstream OpenEarable reference (front/back shells, speaker mount,
  battery mount, `.step` + `.stl`). `Enclosure.stp` is Haven's own enclosure
  design.
- **`haven_dev_board/`** — Haven's own stripped-down custom dev board.
  `component_libraries/` holds Ultra Librarian Altium parts (symbol +
  footprint + 3D model) for the chips it's built around: the ADAU1860 DSP
  and the SPH0645LM4H-B MEMS mic. The board's own Altium project files go
  directly in `haven_dev_board/` once that design exists.

## Why LFS

Every future PCB revision or CAD export is another full binary blob — these
don't diff or merge, so without LFS the repo's `.git` history only grows,
forever, even for teammates who never touch hardware. LFS stores pointers in
git and the actual binaries in a separate store, fetched on demand.
