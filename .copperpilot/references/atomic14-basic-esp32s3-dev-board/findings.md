# Reference Findings: atomic14-basic-esp32s3-dev-board

- **Repository URL:** https://github.com/atomic14/basic-esp32s3-dev-board
- **Git Commit Revision:** `7b4804ac3e3b1a7c06fe8769bbc428b05883af2c`
- **License:** `MIT`
- **Detected KiCad Version:** `9.0 (20250114 sch / 20241229 pcb)`
- **Target KiCad Version:** `10.0 (20260306 sch / 20260206 pcb)`
- **Match Classification:** `adapted_partial_reference`
- **Identity Disposition:** `sanitized`

## Verified Files & Post-Upgrade SHA-256 Hashes
- `LICENSE` (1065 bytes) — `sha256:d5516e60aa03d8e971017892ec7159fc17969c6a9de651f3310d5415cfdff0c3`
- `dev-board.kicad_pcb` (288476 bytes) — `sha256:cf66e0a80a17d96ee631fafea9cbbe57c2cc73816e4111856b500b127ab55b38`
- `dev-board.kicad_pro` (15696 bytes) — `sha256:12a9576d7b8cf4df3cacdd705a87ef7dc8546208eefa44bc0eac2ae2b9620556`
- `dev-board.kicad_sch` (156933 bytes) — `sha256:9c0017907d70788a289010c438fd596307e202f980da91c2d56dd2a4bf5e15a7`

## Reusable Blocks
- USB-C 16P receptacle with 5.1k CC1/CC2 pull-downs
- EN (10k pull-up + 1uF capacitor + RESET switch) and GPIO0 (BOOT switch) circuit
- Power indicator LED + user GPIO LED
- Dual 1x20 2.54mm breadboard header breakout topology

## Gaps & Required Adaptations
- Uses ESP32-S3-WROOM-1 module instead of bare ESP32-S3FH4R2 QFN-56 IC
- Omits 40 MHz crystal + load capacitors, bare-chip per-pin decoupling, and discrete 2.4 GHz RF pi-matching network + antenna
- Uses LD1117S33 instead of AP2112K-3.3SOT-23-5 and omits USBLC6-2SC6 ESD array
