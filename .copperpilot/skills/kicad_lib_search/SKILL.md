---
required_inputs: [query, kind, platform, optional project_dir and library path overrides]
artifact_outputs: [structured JSON search results with summary]
---

# Skill: kicad_lib_search

## Objective
Search KiCad symbol, footprint, and 3D model libraries on the user's machine.
Use installed KiCad stock libraries and project-local libraries such as
`${KIPRJMOD}/555_badge.kicad_sym`, `${KIPRJMOD}/*.pretty`, and
`${KIPRJMOD}/libs/3dmodels`.

## Platform defaults (mac)
- Symbols: `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols`
- Footprints: `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints`
- 3D models: `/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels`
- Environment overrides: `KICAD10_SYMBOL_DIR, KICAD10_FOOTPRINT_DIR, KICAD10_3DMODEL_DIR`

## Steps
1. Run `.copperpilot/skills/kicad_lib_search/main.py search` with `--platform mac` and `--project-dir .`.
2. Choose `--kind symbol`, `footprint`, `model`, or `all`.
3. Pass `--query` using symbol names, package names, footprint ids, or model filenames.
4. Read the JSON `summary` and footprint `results[].library_path` / `results[].footprint_id` (or symbol `results[].symbol_id`) values for schematic/PCB work. Pass footprint `library_path` and `footprint_id` directly into `place_pcb_footprint`.
5. Override search roots with `--symbol-dir`, `--footprint-dir`, or `--model-dir` when needed.

Includes project-local `*.kicad_sym`, `*.pretty`, and `libs/3dmodels` under the project directory.


## Examples
- `python .copperpilot/skills/kicad_lib_search/main.py search --platform mac --project-dir . --kind symbol --query "7555" --max-results 10`
- `python .copperpilot/skills/kicad_lib_search/main.py search --platform mac --project-dir . --kind footprint --query "LED_D3.0mm" --max-results 10`
- `python .copperpilot/skills/kicad_lib_search/main.py search --platform mac --project-dir . --kind model --query "BatteryHolder|CAS-120A" --max-results 10`
- `python .copperpilot/skills/kicad_lib_search/main.py search --platform mac --project-dir . --kind all --query "Resistor_THT 0805" --max-results 20`
