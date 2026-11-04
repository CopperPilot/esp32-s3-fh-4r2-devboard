# jlcpcb-order: site reference

## Generic browser tools
- `snapshot [--scope CSS] [--grep RX] [--interactive-only]` gives an accessibility
  tree with refs like `e42`. Then `click --ref e42`, `fill --ref e42 --value V`,
  `hover --ref e42` (reveals tooltips).
- Address elements by `--role button --name "Next" --exact`, `--text`,
  `--selector`. Add `--url-match jlcdfm` or `--tab N` to target another tab
  (`tabs` lists them).
- `text [--selector]`, `tables [--selector]`, `observe`, `screenshot [--selector|--clip x,y,w,h|--full-page]`,
  `wait --text T | --idle`, `press Escape`, `scroll`, `upload --file F [--selector input]`,
  `reload`, `goto URL`, `eval "() => ..."` (read-only unless `--allow-mutation`).
- Refs go stale after re-render. Take a fresh `snapshot`.


## Site knowledge (gotchas)
- Quote page: upload shows "Uploading your files… N%", then "Processing Gerber files…",
  then "Detected …". Option rows can change: Delivery Format=Panel renames
  "PCB Qty" to "Panel Qty", and ENIG adds "Gold Thickness". Re-read after setting.
- PCB Qty is a fixed list (5, 10, 15, 20, 25, 30, …); custom values are not allowed (the error lists allowed values).
- Economic PCBA: top OR bottom only, limited advanced options. Standard PCBA:
  both sides, $25/side setup, adds edge rails (board becomes 110×100 for 100×100).
  Parts flagged "Standard Only" are deselected on Economic.
- Assembly Side=Top Side silently excludes bottom-side parts from the BOM review
  (header counts drop). If the CPL has bottom parts, choose "Both Sides" (Standard)
  or confirm with the user that those parts are DNP / hand-soldered.
- JLCDFM statistics are (danger, warning, good). The Details dialog has
  per-layer lists. `board_xy_mm` is in Gerber coordinates (lower-left aux
  origin for this project), and the skill converts it to KiCad.
- DFM viewer and Gerber viewer open new tabs. "Initializing DFM Viewer…" can
  hang. Use `reload --url-match jlcdfm` and rerun.
- Placement preview: the pink dot is the footprint pin 1, and polarity marks are +/−.
  The page warns: "preview for reference only; final placement is checked by DFM after ordering."
- Cart groups PCB + PCBA as one item with one remove icon.
