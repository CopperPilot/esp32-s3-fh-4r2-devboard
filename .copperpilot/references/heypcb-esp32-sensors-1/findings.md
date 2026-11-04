# Reference Findings: heypcb-esp32-sensors-1

- **Repository URL:** https://github.com/HeyPCB/esp32-sensors-1
- **Git Commit Revision:** `57a2122a19ac1aa9c092e43fb5b123c461508752`
- **License:** `CERN-OHL-S-2.0`
- **Detected KiCad Version:** `10.0 (20260306 sch / 20260206 pcb)`
- **Target KiCad Version:** `10.0 (20260306 sch / 20260206 pcb)`
- **Match Classification:** `adapted_partial_reference`
- **Identity Disposition:** `rejected_for_direct_copy_look_only`

## Verified Files & Post-Upgrade SHA-256 Hashes
- `LICENSE` (13419 bytes) — `sha256:253ad3f89603e728abfa60c36fbcaf8225cf55c1eab12725f19fb3d74d647f3a`
- `boards/lmt87/kicad/esp32_lmt87.kicad_pcb` (282936 bytes) — `sha256:0a08aa2b14b09fb1a0131fed25c84f02f84dda5114ed197a81b6e965b8a5d2dc`
- `boards/lmt87/kicad/esp32_lmt87.kicad_pro` (10458 bytes) — `sha256:f541e4d58c8cfaa905c73bf4506d9898b74cd12bf35ef6f7278a26ec66e0937b`
- `boards/lmt87/kicad/esp32_lmt87.kicad_sch` (137150 bytes) — `sha256:63e2b941588212c4dba56ef1e734f775f4bafa7d93eab1fcaf7c124c3d747053`

## Reusable Blocks
- Reference topology verification (look-only due to CERN-OHL-S-2.0) for USB-C 16P + USBLC6-2SC6 ESD protection + AP2112K-3.3 LDO + ESP32-S3 native USB D+/D-

## Gaps & Required Adaptations
- Strongly reciprocal CERN-OHL-S-2.0 license forbids direct file/subcircuit copying into non-CERN-OHL deliverables; used strictly as look-only verification alongside ST/Diodes/Espressif datasheets
- Uses ESP32-S3-WROOM-1 module rather than bare ESP32-S3FH4R2 QFN-56
