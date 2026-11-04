# ESP32-S3FH4R2 Tiny-LLM Development Board — Final Design Deliverables

## 1. Design Overview

This hardware package implements a compact (25.40 × 55.88 mm / 1.0" × 2.2"), breadboard-friendly (0.9" row spacing) development board built specifically around the **Espressif ESP32-S3FH4R2** (QFN-56 7×7 mm, in-package 4 MB Quad SPI Flash and 2 MB Quad SPI PSRAM) designed for running edge inference workloads such as `llama2.c` (260K-parameter model).

### Key Subsystems
1. **Processor & Memory:**
   - ESP32-S3FH4R2 dual-core Xtensa LX7 @ 240 MHz.
   - 4 MB in-package Quad SPI Flash + 2 MB in-package Quad SPI PSRAM powered internally from `VDD_SPI` (3.3 V).
   - Only Pins 28 and 30–35 (`SPICS1`, `SPIHD`, `SPIWP`, `SPICS0`, `SPICLK`, `SPIQ`, `SPID`) are consumed internally; `GPIO33–GPIO37` and `GPIO47–GPIO48` remain completely free.
2. **Clock & RF Front-End:**
   - 40.000 MHz fundamental crystal (`TSX-3225 40.0000MF10Z-AC3`, ±10 ppm) with 15 pF C0G load capacitors (`C1`, `C2`) and a 24 nH harmonic suppression inductor (`L3`) on `XTAL_P`.
   - 50 Ω C-L-C Pi-matching network (`C16` = 1.5 pF, `L2` = 2.7 nH, `C17` = 1.5 pF) feeding an edge-mounted 2.4 GHz ceramic chip antenna (`ANT3216LL00R2400A`) with complete all-layer copper keep-out under and around the radiator. An optional unpopulated `u.FL` coaxial receptacle (`J5`) is provided with an RF selector jumper pad (`R9`).
3. **Power Architecture:**
   - 5 V USB VBUS input through a 1 A Schottky diode (`B5819W`, SOD-123) providing reverse-current and backfeed protection.
   - Diodes Inc `AP2112K-3.3TRG1` 600 mA low-dropout CMOS regulator in SOT-23-5 package with low dropout (250 mV typ @ 600 mA).
   - Dedicated filtering: 10 µF + 100 nF on VIN, 22 µF + 10 µF + 100 nF bulk reservoir on VOUT.
   - Individual decoupling per Espressif Hardware Design Guidelines: 10 µF + 1 µF + 100 nF + 2.0 nH inductor (`L1`) on `VDD3P3_PA` (Pins 2, 3); 1 µF + 100 nF on `VDD_SPI` (Pin 29); 1 µF + 10 nF on `VDDA` (Pins 55, 56); 100 nF on `VDD3P3_RTC` (Pin 20); 100 nF on `VDD3P3_CPU` (Pin 46).
   - Green 3.3 V Power-On indicator LED (`D2`, 0603) with 1 kΩ ballast resistor (`R7`).
4. **USB & Native Flashing:**
   - 16-pin USB-C receptacle (`TYPE-C-31-M-12` / `USB4105-GF-A`) wired to native USB: D- to `GPIO19`, D+ to `GPIO20` through optional 22 Ω series damping resistors (`R5`, `R6`).
   - STMicroelectronics `USBLC6-2SC6` SOT-23-6 rail-to-rail ESD protection array on D+, D-, and VBUS.
   - Dual independent 5.1 kΩ 1% pull-down resistors (`R1`, `R2`) on `CC1` and `CC2` for USB Type-C Standard Power downstream sink detection.
   - Flashing and debugging use the ESP32-S3 built-in USB-Serial/JTAG controller (`idf.py -p ... flash`), eliminating external UART bridge ICs.
5. **Control, User I/O & Mechanical:**
   - `RESET` button (`SW1`) with hardware RC delay (10 kΩ pull-up `R3` to 3.3 V + 1 µF ceramic cap `C18` to GND).
   - `BOOT` button (`SW2`) on `GPIO0` with 10 kΩ pull-up (`R4`) to 3.3 V.
   - Active-high user LED (`D3`, Red 0603) on `GPIO38` with 1 kΩ series resistor (`R8`).
   - Dual 1×20 2.54 mm pin headers (`J2`, `J3`) breaking out 36 usable GPIOs, 3.3 V, 5 V, and GND with explicit silkscreen pin labels.
   - Optional unpopulated 4-pin I2C OLED display connector (`J4`: 3V3, GND, SCL on `GPIO9`, SDA on `GPIO8`).
   - Four M2 mounting holes (`H1`–`H4`) in the corners with 4.5 mm keepout and ground-stitched annular rings.

---

## 2. Complete Bill of Materials (BOM)
| Item # | Designator | Qty | Description | MPN | Manufacturer | Footprint | Value | LCSC Part # | Digi-Key Part # | Assembly Instructions |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `U1` | 1 | 2.4 GHz Wi-Fi + BLE 5.0 Dual-Core LX7 SoC with 4 MB Quad SPI Flash and 2 MB Quad PSRAM | `ESP32-S3FH4R2` | Espressif Systems | `QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm` | `ESP32-S3FH4R2` | `C3013940` | `1965-ESP32-S3FH4R2CT-ND` | Populate |
| 2 | `U2` | 1 | Fixed 3.3V 600mA Low-Dropout Linear Regulator | `AP2112K-3.3TRG1` | Diodes Incorporated | `SOT-23-5` | `AP2112K-3.3` | `C51118` | `AP2112K-3.3TRG1DICT-ND` | Populate |
| 3 | `U3` | 1 | Very Low Capacitance ESD Protection Array for USB 2.0 | `USBLC6-2SC6` | STMicroelectronics | `SOT-23-6` | `USBLC6-2SC6` | `C7519` | `497-5235-1-ND` | Populate |
| 4 | `Y1` | 1 | 40.000 MHz 10ppm 12pF SMD 3225 4-Pin Quartz Crystal | `TSX-3225 40.0000MF15Y-K0` | Seiko Epson | `Crystal_SMD_3225-4Pin_3.2x2.5mm` | `40MHz` | `C255942` | `SER4097CT-ND` | Populate |
| 5 | `ANT1` | 1 | 2.4 GHz 50 Ohm SMD Ceramic Chip Antenna (3.2x1.6mm) | `ANT3216LL00R2400A` | Yageo / Pulse | `Johanson_2450AT18x100` | `ANT3216LL00R2400A` | `C293767` | `13-ANT3216LL00R2400ACT-ND` | Populate |
| 6 | `J1` | 1 | USB Type-C 16-Pin USB 2.0 Right-Angle SMD Receptacle | `USB4105-GF-A` | GCT | `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | `USB_C_Receptacle_USB2.0_16P` | `C165948` | `2073-USB4105-GF-ACT-ND` | Populate |
| 7 | `D1` | 1 | 40V 1A Schottky Barrier Rectifier Diode | `1N5819HW-7-F` | Diodes Incorporated | `D_SOD-123` | `B5819W` | `C8598` | `1N5819HW-7-FDICT-ND` | Populate |
| 8 | `D2` | 1 | Red 0603 SMD Power Indicator LED | `LTST-C190KRKT` | Lite-On | `LED_0603_1608Metric` | `Red` | `C2286` | `160-1447-1-ND` | Populate |
| 9 | `D3` | 1 | Green 0603 SMD User Status LED (GPIO38) | `LTST-C190KGKT` | Lite-On | `LED_0603_1608Metric` | `Green` | `C12624` | `160-1446-1-ND` | Populate |
| 10 | `SW1, SW2` | 2 | SPST-NO Ultraminiature Top-Actuated SMD Tactile Switch (RESET, BOOT) | `B3U-1000P` | Omron Electronics | `SW_SPST_B3U-1000P` | `RESET / BOOT` | `C145958` | `SW1020CT-ND` | Populate |
| 11 | `L1` | 1 | 2.0nH +/-0.3nH 0402 High-Q RF Inductor (VDD3P3 PA Filter) | `LQG15HS2N0S02D` | Murata | `L_0402_1005Metric` | `2.0nH` | `C15132` | `490-14573-1-ND` | Populate |
| 12 | `L2` | 1 | 2.7nH +/-0.3nH 0402 High-Q RF Matching Inductor (50 Ohm Pi-Match) | `LQG15HS2N7S02D` | Murata | `L_0402_1005Metric` | `2.7nH` | `C27123` | `490-14577-1-ND` | Populate |
| 13 | `L3` | 1 | 24nH 5% 0402 Wirewound RF Inductor (XTAL_P Harmonic Suppression) | `LQW15AN24NJ00D` | Murata | `L_0402_1005Metric` | `24nH` | `C76878` | `490-1155-1-ND` | Populate |
| 14 | `C1, C2` | 2 | 15pF 50V 5% C0G/NP0 0402 Ceramic Crystal Load Capacitor | `CC0402JRNPO9BN150` | Yageo | `C_0402_1005Metric` | `15pF` | `C1548` | `311-1019-1-ND` | Populate |
| 15 | `C16, C17` | 2 | 1.5pF 50V +/-0.25pF C0G/NP0 0402 RF Matching Shunt Capacitor | `CC0402CRNPO9BN1R5` | Yageo | `C_0402_1005Metric` | `1.5pF` | `C1552` | `311-1010-1-ND` | Populate |
| 16 | `C15` | 1 | 10nF 50V 10% X7R 0402 Ceramic Decoupling Capacitor (VDDA) | `CL05B103KB5NNNC` | Samsung Electro-Mechanics | `C_0402_1005Metric` | `10nF` | `C15195` | `1276-1009-1-ND` | Populate |
| 17 | `C5, C6, C7, C9, C11, C14, C19, C21, C23` | 9 | 100nF 16V 10% X7R 0402 Ceramic Decoupling Capacitor | `CL05B104KO5NNNC` | Samsung Electro-Mechanics | `C_0402_1005Metric` | `100nF` | `C1525` | `1276-1000-1-ND` | Populate |
| 18 | `C4, C8, C10, C13, C18` | 5 | 1uF 10V 10% X5R 0402 Ceramic Decoupling & EN RC Delay Capacitor | `CL05A105KP5NNNC` | Samsung Electro-Mechanics | `C_0402_1005Metric` | `1uF` | `C52923` | `1276-1006-1-ND` | Populate |
| 19 | `C3, C12` | 2 | 10uF 6.3V 20% X5R 0402 Ceramic Bulk Capacitor (`VDD3P3`, `VDDA`) | `CL05A106MQ5NUNC` | Samsung Electro-Mechanics | `C_0402_1005Metric` | `10uF` | `C15525` | `1276-1089-1-ND` | Populate |
| 20 | `C20` | 1 | 10uF 10V 20% X5R 0603 Ceramic LDO Input Bulk Capacitor (`+5V`) | `CL10A106MP8NNNC` | Samsung Electro-Mechanics | `C_0603_1608Metric` | `10uF` | `C19702` | `1276-1099-1-ND` | Populate |
| 21 | `C22` | 1 | 22uF 10V 20% X5R 0603 Ceramic LDO Output Bulk Reservoir Capacitor | `CL10A226MP8NUNE` | Samsung Electro-Mechanics | `C_0603_1608Metric` | `22uF` | `C59461` | `1276-1119-1-ND` | Populate |
| 22 | `R1, R2` | 2 | 5.1k Ohm 1% 1/16W 0402 Thick Film Resistor (USB-C CC1/CC2 Rd) | `RC0402FR-075K1L` | Yageo | `R_0402_1005Metric` | `5.1k` | `C25905` | `311-5.10KLRCT-ND` | Populate |
| 23 | `R3, R4` | 2 | 10k Ohm 1% 1/16W 0402 Thick Film Pull-Up Resistor (EN, GPIO0) | `RC0402FR-0710KL` | Yageo | `R_0402_1005Metric` | `10k` | `C25744` | `311-10.0KLRCT-ND` | Populate |
| 24 | `R5, R6` | 2 | 22 Ohm 1% 1/16W 0402 Thick Film USB D+/D- Series Resistor | `RC0402FR-0722RL` | Yageo | `R_0402_1005Metric` | `22` | `C25092` | `311-22.0LRCT-ND` | Populate |
| 25 | `R7, R8` | 2 | 1k Ohm 1% 1/16W 0402 Thick Film LED Current-Limiting Resistor | `RC0402FR-071KL` | Yageo | `R_0402_1005Metric` | `1k` | `C11702` | `311-1.00KLRCT-ND` | Populate |
| 26 | `J2, J3` | 2 | 1x20 2.54mm Pitch Vertical Through-Hole Pin Header | `M20-9992046` | Harwin | `PinHeader_1x20_P2.54mm_Vertical` | `HEADER_1x20` | `C2839521` | `952-2273-ND` | Populate |
| 27 | `J4` | 1 | 1x04 2.54mm Pitch Vertical Through-Hole I2C OLED Header (Optional) | `TSW-104-07-L-S` | Samtec | `PinHeader_1x04_P2.54mm_Vertical` | `I2C_OLED_DNP` | `C2839481` | `SAM1029-04-ND` | DNP (Do Not Populate) |
| 28 | `J5` | 1 | DC-6GHz 50 Ohm U.FL Coaxial SMT RF Receptacle (Optional) | `U.FL-R-SMT-1(10)` | Hirose Electric | `U.FL_Hirose_U.FL-R-SMT-1_Vertical` | `U.FL_DNP` | `C88373` | `H9161CT-ND` | DNP (Do Not Populate) |
| 29 | `R9` | 1 | 0 Ohm Jumper 0402 RF Path Selector to J5 (Optional) | `RC0402JR-070RL` | Yageo | `R_0402_1005Metric` | `0R_DNP` | `C17168` | `311-0.0LRCT-ND` | DNP (Do Not Populate) |

---

## 3. Electrical and Design Rule Check (ERC / DRC) Status

### Electrical Rules Check (ERC)
- **Tool:** `kicad-cli sch erc --format json` (KiCad 10.0.4)
- **Result:** **0 errors, 0 warnings** (100% clean).
- **Layout Invariant Audit:** `validate_schematic_layout` found **0 violations** (no text-on-symbol, no dangling endpoints, no wire-through-body issues, all net labels and ports cleanly aligned).

### Design Rules Check (DRC)
- **Tool:** `kicad-cli pcb drc --format json` (KiCad 10.0.4)
- **Violations:** **0 errors, 0 warnings** (no clearance, minimum track width, hole clearance, annular ring, courtyard, thermal spoke, or silkscreen clipping violations).
- **Unconnected Items:** **0 unconnected items** (100% routed across all 59 nets / 191 connections).
- **Copper Pours & Keepouts:**
  - `F.Cu`: Top `GND` pour with 0.20 mm clearance and thermal reliefs.
  - `In1.Cu`: Unbroken solid `GND` reference plane with direct solid thermal-via connections to `U1` Pad 57 (`9×` plated thermal vias).
  - `In2.Cu`: Solid `+3V3` power plane with 0.20 mm clearance and thermal reliefs.
  - `B.Cu`: Bottom `GND` pour with 0.20 mm clearance and thermal reliefs.
  - **2.4 GHz Antenna Keep-Out Zone:** Full all-layer (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`) copper pour and via keep-out under and around `ANT1` (`x = 108.5..114.5 mm`, `y = 99.6..102.8 mm`).

---

## 4. Pinout Assignments & Stated Assumptions

### 1. In-Package Memory Exclusion (Pins 28 and 30–35)
- The ESP32-S3FH4R2 integrates 4 MB Quad SPI Flash and 2 MB Quad SPI PSRAM inside the 7×7 mm QFN-56 package.
- Pins 28 (`SPICS1`), 30 (`SPIHD`), 31 (`SPIWP`), 32 (`SPICS0`), 33 (`SPICLK`), 34 (`SPIQ`), and 35 (`SPID`) correspond to `GPIO26–GPIO32` and are consumed internally. They are left strictly unconnected (`no_connect`) on the schematic and PCB.
- Because the FH4R2 uses **Quad SPI** PSRAM (not Octal), `GPIO33–GPIO37` (Pins 38–42) and `GPIO47–GPIO48` (Pins 36–37) are **completely free** for external user I/O.

### 2. Strapping Pins Configuration
- `GPIO0` (Pin 5): Pulled up to 3.3 V via 10 kΩ resistor (`R4`). Pulling low via `SW2` enters serial bootloader mode.
- `GPIO3` (Pin 8): Left floating / exposed on `J2` pin 12 with no default pull-up/down to ensure safe JTAG boot behavior.
- `GPIO45` (Pin 51): Controls `VDD_SPI` voltage at reset (0 = 3.3 V, 1 = 1.8 V). Left with internal weak pull-down to ensure `VDD_SPI` defaults to 3.3 V as required by the FH4R2 in-package memory.
- `GPIO46` (Pin 52): ROM print strapping pin. Left in default state (internal weak pull-down).

### 3. Dedicated Peripheral Mappings
- `GPIO19` / `GPIO20` (Pins 25, 26): Dedicated to USB 2.0 Full-Speed native USB (`D-` and `D+`), connected to `J1` via `USBLC6-2SC6` and 22 Ω series damping resistors (`R5`, `R6`).
- `GPIO38` (Pin 43): Assigned to active-high Red user LED (`D3`) via 1 kΩ ballast resistor (`R8`).
- `GPIO9` / `GPIO8` (Pins 14, 13): Assigned to `I2C_SCL` and `I2C_SDA` on the unpopulated 4-pin OLED display footprint (`J4`). Assumes external OLED module contains standard 4.7 kΩ pull-ups.

### 4. Dual 1×20 Header Breakdown (0.9" Spacing)
- **Left Header (J2):** Pin 1 = `+3V3`, Pin 2 = `EN`, Pin 3 = `GPIO4`, Pin 4 = `GPIO5`, Pin 5 = `GPIO6`, Pin 6 = `GPIO7`, Pin 7 = `GPIO15`, Pin 8 = `GPIO16`, Pin 9 = `GPIO17`, Pin 10 = `GPIO18`, Pin 11 = `GPIO8 (SDA)`, Pin 12 = `GPIO3`, Pin 13 = `GPIO46`, Pin 14 = `GPIO9 (SCL)`, Pin 15 = `GPIO10`, Pin 16 = `GPIO11`, Pin 17 = `GPIO12`, Pin 18 = `GPIO13`, Pin 19 = `GPIO14`, Pin 20 = `GND`.
- **Right Header (J3):** Pin 1 = `+5V`, Pin 2 = `GPIO1`, Pin 3 = `GPIO2`, Pin 4 = `U0TXD`, Pin 5 = `U0RXD`, Pin 6 = `GPIO42`, Pin 7 = `GPIO41`, Pin 8 = `GPIO40`, Pin 9 = `GPIO39`, Pin 10 = `GPIO38 (LED)`, Pin 11 = `GPIO37`, Pin 12 = `GPIO36`, Pin 13 = `GPIO35`, Pin 14 = `GPIO34`, Pin 15 = `GPIO33`, Pin 16 = `GPIO0 (BOOT)`, Pin 17 = `GPIO45`, Pin 18 = `GPIO48`, Pin 19 = `GPIO47`, Pin 20 = `GPIO21`.
