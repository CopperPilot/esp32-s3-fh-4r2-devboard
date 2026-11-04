# ESP32S3FH4R2 Tiny-LLM Development Board — Project Index

## Overview
Compact 25.4 × 55.88 mm (1.0" × 2.2") breadboard-friendly development board built around the **Espressif `ESP32-S3FH4R2`** (QFN-56 7×7 mm, 4 MB in-package Quad SPI flash, 2 MB in-package Quad SPI PSRAM) for running `llama2.c` (260K-parameter LLM).

## Key Project Artifacts
- **Final Design Deliverables, BOM & ERC/DRC Summary:** [`.copperpilot/notes/final-design-deliverables.md`](./notes/final-design-deliverables.md)
- **Implementation Plan:** [`.copperpilot/plans/esp32s3fh4r2-llm-dev-board.plan.md`](./plans/esp32s3fh4r2-llm-dev-board.plan.md) (`completed`)
- **Plans Index:** [`.copperpilot/PLANS.md`](./PLANS.md)
- **Hardware Reference & Pinout Verification:** [`.copperpilot/notes/esp32s3fh4r2-hardware-reference.md`](./notes/esp32s3fh4r2-hardware-reference.md)
- **Verified LCSC & Digi-Key BOM Sourcing:** [`.copperpilot/notes/esp32s3fh4r2-bom-sourcing.md`](./notes/esp32s3fh4r2-bom-sourcing.md)
- **KiCad 10 macOS Library Survey:** [`.copperpilot/notes/kicad10-library-survey.md`](./notes/kicad10-library-survey.md)
- **Design Oracle & Provenance:** [`.copperpilot/oracle/design-oracle.json`](./oracle/design-oracle.json), [`.copperpilot/oracle/provenance.jsonl`](./oracle/provenance.jsonl), [`.copperpilot/oracle/gates.json`](./oracle/gates.json)
- **Generated Concept Diagrams:**
  - [`.copperpilot/generated/schematic-usb-power.png`](./generated/schematic-usb-power.png)
  - [`.copperpilot/generated/schematic-mcu-rf-clock.png`](./generated/schematic-mcu-rf-clock.png)
- **Cloned & Inspected Reference Projects:**
  - [`.copperpilot/references/atomic14-basic-esp32s3-dev-board/findings.md`](./references/atomic14-basic-esp32s3-dev-board/findings.md) (MIT, upgraded in-place to KiCad 10.0.4)
  - [`.copperpilot/references/heypcb-esp32-sensors-1/findings.md`](./references/heypcb-esp32-sensors-1/findings.md) (CERN-OHL-S-2.0, look-only topology check)
  - [`.copperpilot/references/marouane-esp32-c3-dev-board/findings.md`](./references/marouane-esp32-c3-dev-board/findings.md) (Look-only topology check)
