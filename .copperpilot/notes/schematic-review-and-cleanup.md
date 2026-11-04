# Senior Schematic Engineering Review & Convention Cleanup: ESP32-S3FH4R2 Tiny-LLM Dev Board (Rev 1.0)

## Summary

The design intent is a compact `25.4 x 55.88 mm` (`1.0" x 2.2"`) development board based on the **Espressif ESP32-S3FH4R2** (QFN-56 7x7 mm with in-package 4 MB Quad SPI Flash and 2 MB Quad SPI PSRAM) for running `llama2.c` (260K-parameter model), powered from a USB 2.0 Type-C receptacle through a 600 mA 3.3 V LDO (`AP2112K-3.3TRG1`), with native USB-Serial/JTAG programming (`GPIO19`/`GPIO20` protected by `USBLC6-2SC6`), a 40 MHz 10 ppm crystal (`Y1`), a 2.4 GHz ceramic chip antenna (`ANT1`) with Pi-matching network and optional `u.FL` (`J5`), `RESET`/`BOOT` tactile switches, a user LED on `GPIO38`, an optional unpopulated I2C display header (`J4`), and dual `1x20` headers spaced 0.9" apart.

Although the pre-cleanup schematic passed KiCad ERC with 0 errors and 0 warnings, our `/schematic-engineer`, `/schematic-reviewer`, and `/schematic-conventions` audit combined with netlist and rendered-sheet inspection uncovered **1 critical electrical error** (reverse-biased 3.3 V power indicator LED `D2`), **1 low/informational interface note** (unpopulated I2C header pull-up strategy), and **5 drafting/convention issues** (a multi-line text string with literal `\n` characters colliding with headers `J2`/`J3`, vertical/overlapping text on rotated passives and switches, split `EN` reset RC components away from `SW1`, cramped 7.62 mm capacitor spacing causing label-to-body overlaps, and unnamed critical USB/RF/crystal nets plus missing dashed module boundary frames).

Count of findings by severity: **1 Critical (Electrical Error)**, **1 High (Drafting Collision)**, **3 Medium (Drafting & Net Naming Conventions)**, **2 Low/Informational (Interface Assumption & Module Framing)**.

---

## Critical and High Findings

```yaml
id: SCH-LED-001
location: Sheet 1, Power Block, D2 (KT-0603R) and R7 (1 kΩ) at [186.69, 48.26]
observation: >
  Power indicator LED D2 is placed at rotation 270 degrees, which places Pin 1 (Cathode K)
  at the top connected to +3V3 [186.69, 44.45] and Pin 2 (Anode A) at the bottom [186.69, 52.07]
  connected through R7 (1 kΩ) to GND.
classification: ERROR
severity: CRITICAL
mechanism: >
  A standard PN junction LED conducts only when forward-biased (Anode positive with respect to
  Cathode by at least V_F ≈ 1.8–2.2 V). With Cathode tied to +3V3 and Anode tied to GND through R7,
  D2 is reverse-biased by 3.3 V (within its 5 V reverse breakdown rating, so undamaged, but non-conducting).
consequence: >
  The 3.3 V power-on indicator LED D2 will never illuminate when the board is powered.
evidence: >
  Tier 3 (Manufacturer datasheet: Hubei KENTO KT-0603R / standard KiCad Device:LED pinout where
  Pin 1 = K and Pin 2 = A); verified in exported netlist (.copperpilot/tmp/netlist-before-cleanup.xml)
  showing +3V3 connected to D2.1 and Net-(D2-A) connecting D2.2 to R7.1.
recommendation: >
  Place R7 (1 kΩ) on the high side (+3V3 to R7.1) and orient D2 at rotation 90 degrees so Pin 2
  (Anode) connects to R7.2 at the top and Pin 1 (Cathode) connects to GND at the bottom, matching
  the topology of the GPIO38 user LED circuit (R8 + D3).
tradeoffs: None.
verification: >
  Export netlist and verify +3V3 -> R7.1, R7.2 -> D2.2 (Anode), and D2.1 (Cathode) -> GND; run ERC.
confidence: high
executable: yes
```

```yaml
id: SCH-CONV-001
location: Sheet 1, MCU Annotation Text (uuid 10000000-0000-4000-8000-000000000503) at [205.74, 86.36]
observation: >
  The annotation string above U1 contains unescaped literal 'n' characters instead of line breaks
  ("...PSRAM)nPins 28, 30-35...nStrapping:...") and extends horizontally from x = 205.74 mm to
  x = 395 mm, cutting directly across headers J2 (x = 317.5 mm) and J3 (x = 368.3 mm).
classification: CONVENTION
severity: HIGH
mechanism: >
  This is a drafting defect, not an electrical error; the circuit netlist is unaffected, but the
  text collides visually with pins 8–9 and net labels (GPIO16, GPIO17, GPIO40, GPIO39) on J2 and J3,
  obscuring pin numbers and net names on the printed/rendered schematic.
consequence: >
  Human readers reviewing or debugging J2/J3 header connections can misread pin numbers 8 and 9.
evidence: >
  Tier 12/13 (schematic-conventions Section 5 & Section 9; verified visually in
  .copperpilot/tmp/schematic-before-cleanup.png).
recommendation: >
  Split the note into separate concise sheet-level text lines inside the MCU functional block frame
  so no text crosses J2 or J3.
tradeoffs: None.
verification: >
  Export SVG/PNG via kicad-cli and visually confirm zero text overlap with J2, J3, or U1.
confidence: high
executable: yes
```

---

## Medium Findings (Conventions & Readability)

```yaml
id: SCH-CONV-002
location: Sheet 1, Reset Circuit (R3, C18 at [137.16, 128.27..140.97] vs SW1 at [63.5, 234.95])
observation: >
  The CHIP_PU (EN) pull-up resistor R3 (10 kΩ) and RC delay capacitor C18 (1 uF) are placed in
  the middle-left decoupling area, whereas the manual RESET tactile button SW1 on the same EN net
  is placed 100 mm away in the bottom-left block. Meanwhile, the BOOT button SW2 and its pull-up R4
  are grouped together in the bottom-left block.
classification: CONVENTION
severity: MEDIUM
mechanism: >
  This is a drafting convention, not an electrical error; the circuit works as drawn. However,
  splitting the passive RC network (R3, C18) from the reset switch (SW1) forces the reader to hunt
  across two separate sections of the schematic to verify that EN has a pull-up and debounce/delay cap.
consequence: >
  Slower design review and inconsistent visual structure between the adjacent RESET and BOOT circuits.
evidence: >
  Tier 12 (schematic-conventions Section 3 'Functional grouping' and Section 7 'Repeated circuits').
recommendation: >
  Move R3 (10 kΩ pull-up to +3V3) and C18 (1 uF capacitor to GND) into the RESET & BOOT functional
  block directly alongside SW1 (RESET), mirroring the layout of R4 + SW2 (BOOT).
tradeoffs: None; netlist connectivity on net EN is preserved identically.
verification: >
  Diff exported netlist before and after; confirm net EN still connects U1.4, J2.2, R3.2, C18.1, and SW1.2.
confidence: high
executable: yes
```

```yaml
id: SCH-CONV-003
location: >
  Sheet 1, Rotated symbols R1, R2, R5, R6, L1, L2, L3, R9, SW1, SW2 and tightly spaced capacitor banks
  C19–C22 and C3–C15
observation: >
  (1) Symbols placed at 90-degree rotation with property angle 0 render with vertical text in KiCad,
  causing Reference and Value labels on SW1 ('RESWS1ET'), SW2 ('BOSWO2T'), R1/R2 ('5.1kR25.1k'),
  R5/R6 ('22R622'), and R9 ('0R_DRN9P') to overlap each other.
  (2) R1 and R2 (CC1/CC2 5.1 kΩ pull-downs) are drawn horizontally with sideways GND symbols (#PWR03,
  #PWR04 at rotation 90).
  (3) Parallel decoupling capacitors C20/C19, C22/C21, C3–C5, C8–C9, and C7/C10–C15 are spaced 7.62 mm
  apart, causing each capacitor's right-justified Reference/Value text to overlap the adjacent capacitor's symbol body.
classification: CONVENTION
severity: MEDIUM
mechanism: >
  This is a drafting convention, not an electrical error. Orienting pull-down resistors R1/R2 vertically
  with GND pointing down matches top-to-bottom current flow, and increasing parallel capacitor pitch from
  7.62 mm to 11.43–12.70 mm (with horizontal property poses) eliminates all text-to-body and text-to-text collisions.
consequence: >
  Overlapping component designators and values make BOM cross-checking on the schematic sheet error-prone.
evidence: >
  Tier 12/13 (schematic-conventions Section 2 'Power flow' and Section 5 'Connectivity'; verified in
  .copperpilot/tmp/schematic-before-cleanup.png).
recommendation: >
  Orient R1 and R2 vertically (rotation 0) with downward-pointing GND symbols; set horizontal property
  poses on all 90-degree symbols (SW1, SW2, R5, R6, L1, L2, L3, R9, D2, D3); and widen parallel capacitor
  spacing so every Reference and Value sits in clear white space.
tradeoffs: Uses more horizontal sheet width within the A3 border.
verification: >
  Run validate_schematic_layout, run_erc, and visually inspect the exported PNG.
confidence: high
executable: yes
```

```yaml
id: SCH-CONV-004
location: Sheet 1, Internal nets in USB, Crystal, RF, and LED subcircuits
observation: >
  Ten internal signal nets currently rely on auto-generated netlister names: Net-(J1-CC1), Net-(J1-CC2),
  Net-(J1-D--PadA7), Net-(J1-D+-PadA6), Net-(R5-Pad1), Net-(R6-Pad1), Net-(U1-XTAL_P), Net-(C1-Pad1),
  Net-(U1-XTAL_N), Net-(U1-LNA_IN), Net-(ANT1-FEED), and Net-(J5-In).
classification: CONVENTION
severity: MEDIUM
mechanism: >
  Semantic net names allow layout engineers and PCB design rules to identify differential pairs
  (USB_CON_DM/USB_CON_DP, USB_D-/USB_D+), 50 Ω RF traces (RF_LNA_IN, RF_ANT_FEED, RF_UFL), and
  high-frequency crystal nodes (XTAL_P, XTAL_IN, XTAL_N) without deciphering auto-generated pad names.
consequence: >
  Without explicit net names, PCB net-class assignment and layout inspection must target unstable
  auto-generated net names.
evidence: >
  Tier 12 (schematic-conventions Section 6 'Net names').
recommendation: >
  Add explicit local net labels: USB_CC1, USB_CC2, USB_CON_DM, USB_CON_DP, USB_ESD_DM, USB_ESD_DP,
  XTAL_P, XTAL_IN, XTAL_N, RF_LNA_IN, RF_ANT_FEED, and RF_UFL.
tradeoffs: Renames anonymous nets in the exported netlist (PCB is currently unrouted with 0 footprints).
verification: >
  Export netlist and confirm all 12 signal nets carry their semantic names and identical pin membership.
confidence: high
executable: yes
```

---

## Low and Informational Findings

```yaml
id: SCH-CONV-005
location: Sheet 1, All 6 Functional Blocks
observation: >
  The schematic has bold section titles for its six functional blocks, but lacks dashed module boundary
  rectangles framing each block.
classification: CONVENTION
severity: LOW
mechanism: >
  Dashed module frames visually separate power, decoupling, MCU, RF/clock, user I/O, and breakout headers
  on a dense single-sheet A3 schematic.
consequence: >
  Visual boundaries between adjacent blocks are less immediately obvious at full-sheet zoom.
evidence: >
  Tier 12 (schematic-conventions Section 3 'Functional grouping').
recommendation: >
  Add dashed schematic rectangles (draw_schematic_rectangle with stroke_type='dash') around each of the
  six functional blocks with non-colliding section headers above each frame.
tradeoffs: None.
verification: >
  Run validate_schematic_layout (verifying zero frame-stroke collisions) and inspect rendered PNG.
confidence: high
executable: yes
```

```yaml
id: SCH-I2C-001
location: Sheet 1, J4 (I2C_OLED_DNP) on nets I2C_SCL (GPIO9) and I2C_SDA (GPIO8)
observation: >
  Unpopulated 4-pin I2C display header J4 connects I2C_SCL (GPIO9) and I2C_SDA (GPIO8) directly to U1
  and left breakout header J2 without dedicated onboard pull-up resistors to +3V3.
classification: ASSUMPTION
severity: INFORMATIONAL
mechanism: >
  I2C is an open-drain bus requiring pull-up resistors (typically 2.2 kΩ–4.7 kΩ per NXP UM10204 for
  400 kHz Fast-mode). Because J4 is an optional unpopulated (DNP) footprint and GPIO8/GPIO9 are also
  broken out to J2 for general-purpose I/O, omitting populated pull-ups avoids permanently loading
  GPIO8/GPIO9, under the standard assumption that commercial 4-pin SSD1306 I2C OLED modules include
  onboard 4.7 kΩ pull-ups.
consequence: >
  If a bare I2C slave without onboard pull-ups is attached to J4, external 4.7 kΩ pull-ups to +3V3
  must be provided on the breadboard or module.
evidence: >
  Tier 6/7 (NXP UM10204 I2C-bus specification; Espressif ESP32-S3 Datasheet v2.2).
recommendation: >
  Document this assumption explicitly in the schematic annotation next to J4 ("Assumes OLED module has
  onboard 4.7k pull-ups; GPIO8/9 also on J2").
tradeoffs: Avoids adding unrequested BOM parts while making bring-up expectations explicit on the drawing.
verification: >
  Verify annotation visibility next to J4 on the exported schematic PNG.
confidence: high
executable: yes
```

---

## Omission Sweep Summary (`/schematic-engineer` & `/schematic-reviewer`)

- **Supply decoupling:** Every `ESP32-S3FH4R2` supply domain is decoupled per Espressif Hardware Design Guidelines: `VDD3P3` (Pins 2, 3) via Pi-filter `C3` (10 uF) + `C4` (1 uF) + `C5` (100 nF) -> `L1` (2.0 nH) -> `C6` (100 nF); `VDD3P3_RTC` (Pin 20) via `C7` (100 nF); `VDD_SPI` (Pin 29, 3.3 V internal Flash/PSRAM rail) via `C8` (1 uF) + `C9` (100 nF); `VDD3P3_CPU` (Pin 46) via `C10` (1 uF) + `C11` (100 nF); `VDDA` (Pins 55, 56) via `C12` (10 uF) + `C13` (1 uF) + `C14` (100 nF) + `C15` (10 nF).
- **Exposed pad:** `U1` Pin 57 (`GND` center pad) is connected to `GND`.
- **In-package Quad Flash & PSRAM pins:** Pins 28 and 30–35 (`SPICS1`, `SPIHD`, `SPIWP`, `SPICS0`, `SPICLK`, `SPIQ`, `SPID`) are marked with explicit `no_connect` flags and are not routed externally.
- **Strapping pins:** `GPIO0` has a 10 kΩ pull-up (`R4`) to `+3V3` and `BOOT` switch (`SW2`) to `GND`; `GPIO3` is floating by default; `GPIO45` (internal WPD, selects 3.3 V `VDD_SPI`) and `GPIO46` (internal WPD) have no external pull-ups that could corrupt boot.
- **Reset supervisor/RC:** `CHIP_PU` (`EN`, Pin 4) has a 10 kΩ pull-up (`R3`) to `+3V3`, a 1 uF delay/debounce capacitor (`C18`, $\tau = 10\text{ ms}$) to `GND`, and a `RESET` switch (`SW1`) to `GND`.
- **USB-C & ESD protection:** Independent 5.1 kΩ Rd pull-downs (`R1`, `R2`) on `CC1` (`A5`) and `CC2` (`B5`); `A6`/`B6` (`D+`) and `A7`/`B7` (`D-`) tied across both receptacle rows; `USBLC6-2SC6` (`U3`) rail-to-rail ESD protection on `D+`, `D-`, and `VBUS` with 100 nF local bypass (`C23`); 22 Ω series damping resistors (`R5`, `R6`) to `GPIO19`/`GPIO20`.
- **LDO stability & thermal check:** `AP2112K-3.3TRG1` (`U2`) has 10 uF + 100 nF input capacitance (`C20`, `C19`) downstream of Schottky barrier diode `D1` (`B5819W`), `EN` tied to `VIN` (`+5V`), and 22 uF + 100 nF output capacitance (`C22`, `C21`). At typical dual-core 240 MHz + Wi-Fi load (~250 mA) and $V_{\text{IN}} = 4.65\text{ V}$ after `D1`, $P_{\text{LDO}} \approx (4.65 - 3.3) \times 0.25\text{ A} = 0.34\text{ W}$, within SOT-23-5 thermal limits on a 4-layer board with solid internal `GND` and `+3V3` planes.
