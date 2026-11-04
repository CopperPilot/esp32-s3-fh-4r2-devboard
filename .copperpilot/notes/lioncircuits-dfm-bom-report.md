# Lion Circuits 4-Layer DFM & Turnkey BOM Verification Report (`ESP32S3FH4R2`)

## 1. Overview & Retrieved Lion Circuits Capabilities

All design rules and component MPNs in `ESP32S3FH4R2.kicad_pro`, `ESP32S3FH4R2.kicad_sch`, and `ESP32S3FH4R2.kicad_pcb` have been updated, re-routed, and verified against Lion Circuits' published 4-layer fabrication and turnkey assembly capabilities (`https://www.lioncircuits.com/pcb-fabrication` and `https://www.lioncircuits.com/pcb-manufacturing-capabilities/pcb-assembly`, retrieved 2026-11-03).

| Parameter | Lion Circuits 4-Layer Standard / MII Limit | Configured Project Rule (`ESP32S3FH4R2`) | Board Actual / Verification Status |
|---|---|---|---|
| Layer Count | 4 Layers (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`) | 4 Layers (`1.6 mm` FR-4, 1 oz outer / 0.5 oz inner) | PASS (`4 layers`) |
| Minimum Trace Width | `6 mil` (`0.1524 mm`) | `0.1524 mm` (`Default` netclass `0.155 mm`, `Power` `0.20 mm`) | PASS (minimum routed track `0.155 mm`) |
| Minimum Trace Spacing / Clearance | `6 mil` (`0.1524 mm`) | `0.1524 mm` (`zone clearance` `0.160 mm`) | PASS (`0` clearance violations) |
| Minimum Mechanical Drill | `0.30 mm` (Standard 4L) / `0.25 mm` (Custom) | `0.30 mm` minimum through-hole & via drill | PASS (all signal/power/thermal vias `0.30 mm` drill; `H1`–`H4` `0.40 mm` / `2.20 mm`) |
| Minimum Annular Ring | `6 mil` (`0.1524 mm`) | `0.1524 mm` | PASS (`0.61 mm` via pad / `0.30 mm` drill = `0.155 mm` annular ring; `U1` EP thermal vias `0.62/0.30 mm` = `0.160 mm`; `H1`–`H4` stitching vias `0.72/0.40 mm` = `0.160 mm`) |
| Minimum Via Diameter | `0.605 mm` (`0.30 mm` + `2 × 0.1524 mm`) | `0.61 mm` | PASS (`0` via/annular violations) |
| Minimum Via Hole-to-Hole Clearance | `10 mil` (`0.254 mm`) | `0.254 mm` | PASS (`0` hole_clearance violations) |
| Copper-to-Edge Clearance | `12 mil` (`0.30 mm`) | `0.30 mm` | PASS (`H1`–`H4` pad `4.20 mm` leaves `0.30 mm` to `Edge.Cuts`; zones inset `>= 0.40 mm`) |
| Silkscreen Line Width / Text Stroke | `6 mil` (`0.1524 mm`) | `0.1524 mm` (actual `0.1525–0.155 mm`) | PASS (`0` text_thickness violations) |
| Silkscreen Text Height | `23 mil` (`0.5842 mm`) | `0.5842 mm` (actual `0.61–1.00 mm`) | PASS (`0` text_height violations) |
| Silkscreen-to-Pad Clearance | `6 mil` (`0.1524 mm`) | `0.1524 mm` | PASS (`0` silk_over_copper / `0` silk_overlap violations) |
| Smallest Passive Package | `0402` (`1005 Metric`) | `0402` (`1005 Metric`) | PASS |

---

## 2. Updated Turnkey BOM with Lion Circuits-Compatible MPNs

All generic or distributor-house part numbers have been replaced in both `ESP32S3FH4R2.kicad_sch` and `ESP32S3FH4R2.kicad_pcb` with globally stocked manufacturer part numbers (DigiKey / Mouser / Element14 / LCSC) supported by Lion Circuits' automated BOM scrubbing and procurement tool:

| References | Qty | Value / Description | Package / Footprint | Manufacturer | MPN | Assembly Status |
|---|---|---|---|---|---|---|
| `U1` | 1 | `ESP32-S3FH4R2` Dual-Core Wi-Fi/BLE SoC (4 MB Flash, 2 MB PSRAM) | `QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm` | Espressif Systems | `ESP32-S3FH4R2` | Populated |
| `U2` | 1 | `AP2112K-3.3` 600 mA Low-Noise LDO Regulator | `SOT-23-5` | Diodes Incorporated | `AP2112K-3.3TRG1` | Populated |
| `U3` | 1 | `USBLC6-2SC6` Low-Capacitance USB 2.0 ESD Protection Array | `SOT-23-6` | STMicroelectronics | `USBLC6-2SC6` | Populated |
| `Y1` | 1 | `40MHz` SMD Crystal (`±10 ppm`, `CL = 12 pF`) | `Crystal_SMD_3225-4Pin_3.2x2.5mm` | Seiko Epson | `TSX-3225 40.0000MF15Y-K0` | Populated |
| `ANT1` | 1 | `2.4 GHz` SMD Chip Antenna | `Johanson_2450AT18x100` (`3.2x1.6mm`) | Pulse Larsen / Yageo | `ANT3216LL00R2400A` | Populated |
| `J1` | 1 | USB Type-C 16-Pin Receptacle | `USB_C_Receptacle_GCT_USB4105` | Global Connector Technology | `USB4105-GF-A` | Populated |
| `D1` | 1 | `40V 1A` Schottky VBUS Protection Diode | `SOD-123` | Diodes Incorporated | `1N5819HW-7-F` | Populated |
| `D2` | 1 | Red Power Indicator LED | `LED_0603_1608Metric` | Lite-On | `LTST-C190KRKT` | Populated |
| `D3` | 1 | Green User Status LED (`GPIO38`) | `LED_0603_1608Metric` | Lite-On | `LTST-C190KGKT` | Populated |
| `SW1`, `SW2` | 2 | Ultraminiature Top-Actuated Tactile Switch (`RESET`, `BOOT`) | `SW_SPST_B3U-1000P` | Omron Electronics | `B3U-1000P` | Populated |
| `L1` | 1 | `2.0nH` High-Q RF Inductor (`VDD3P3` RF filter) | `L_0402_1005Metric` | Murata | `LQG15HS2N0S02D` | Populated |
| `L2` | 1 | `2.7nH` High-Q RF Matching Inductor (`50 Ω` Pi-network) | `L_0402_1005Metric` | Murata | `LQG15HS2N7S02D` | Populated |
| `L3` | 1 | `24nH` Wirewound Inductor (`XTAL_P` harmonic suppression) | `L_0402_1005Metric` | Murata | `LQW15AN24NJ00D` | Populated |
| `C1`, `C2` | 2 | `15pF` `50V` `C0G/NP0` Crystal Load Capacitor | `C_0402_1005Metric` | Yageo | `CC0402JRNPO9BN150` | Populated |
| `C16`, `C17` | 2 | `1.5pF` `50V` `C0G/NP0` RF Matching Shunt Capacitor | `C_0402_1005Metric` | Yageo | `CC0402CRNPO9BN1R5` | Populated |
| `C15` | 1 | `10nF` `50V` `X7R` Decoupling Capacitor | `C_0402_1005Metric` | Samsung Electro-Mechanics | `CL05B103KB5NNNC` | Populated |
| `C5`–`C7`, `C9`, `C11`, `C14`, `C19`, `C21`, `C23` | 9 | `100nF` `16V` `X7R` Decoupling Capacitor | `C_0402_1005Metric` | Samsung Electro-Mechanics | `CL05B104KO5NNNC` | Populated |
| `C4`, `C8`, `C10`, `C13`, `C18` | 5 | `1uF` `10V` `X5R` Decoupling / Reset RC Capacitor | `C_0402_1005Metric` | Samsung Electro-Mechanics | `CL05A105KP5NNNC` | Populated |
| `C3`, `C12` | 2 | `10uF` `6.3V` `20%` `X5R` Bulk Rail Capacitor (`VDD3P3`, `VDDA`) | `C_0402_1005Metric` | Samsung Electro-Mechanics | `CL05A106MQ5NUNC` | Populated (`9,867` in stock) |
| `C20` | 1 | `10uF` `10V` `20%` `X5R` LDO Input Bulk Capacitor (`+5V`) | `C_0603_1608Metric` | Samsung Electro-Mechanics | `CL10A106MP8NNNC` | Populated (`5,663` in stock) |
| `C22` | 1 | `22uF` `10V` `X5R` LDO Output Bulk Capacitor | `C_0603_1608Metric` | Samsung Electro-Mechanics | `CL10A226MP8NUNE` | Populated |
| `R1`, `R2` | 2 | `5.1k` `1%` USB-C `CC1`/`CC2` Rd Pull-Down Resistor | `R_0402_1005Metric` | Yageo | `RC0402FR-075K1L` | Populated |
| `R3`, `R4` | 2 | `10k` `1%` Pull-Up Resistor (`EN`, `GPIO0`) | `R_0402_1005Metric` | Yageo | `RC0402FR-0710KL` | Populated |
| `R5`, `R6` | 2 | `22` `1%` USB `D+`/`D-` Series Damping Resistor | `R_0402_1005Metric` | Yageo | `RC0402FR-0722RL` | Populated |
| `R7`, `R8` | 2 | `1k` `1%` LED Current-Limiting Resistor | `R_0402_1005Metric` | Yageo | `RC0402FR-071KL` | Populated |
| `J2`, `J3` | 2 | `1x20` `2.54 mm` Through-Hole Pin Header | `PinHeader_1x20_P2.54mm_Vertical` | Harwin | `M20-9992046` | Populated |
| `J4` | 1 | `1x04` `2.54 mm` I2C OLED Header | `PinHeader_1x04_P2.54mm_Vertical` | Samtec | `TSW-104-07-L-S` | DNP |
| `J5` | 1 | U.FL Coaxial RF Connector | `U.FL_Hirose_U.FL-R-SMT-1_Vertical` | Hirose Electric | `U.FL-R-SMT-1(10)` | DNP |
| `R9` | 1 | `0R` RF Path Diversion Jumper to `J5` | `R_0402_1005Metric` | Yageo | `RC0402JR-070RL` | DNP |

---

## 3. Verification Summary

- **Schematic ERC (`kicad-cli sch erc`)**: `0` errors, `0` warnings, `0` total violations.
- **Schematic Layout Audit (`validate_schematic_layout`)**: `0` violations.
- **PCB DRC (`kicad-cli pcb drc`)**: `0` errors, `0` warnings, `0` total violations, `0` unconnected items (`unconnected_items: []`).
- **Identity & Attribution Gate**: `0` forbidden branding, logos, or provenance strings in delivered artifacts.
