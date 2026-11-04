# Manufacturing Export Package (`ESP32S3FH4R2`)

## 1. Quick-Upload File Index

| Upload Purpose | Primary File Path | Alternate / Variant Path | Notes |
|---|---|---|---|
| **Gerber + Excellon Drill ZIP (Standard & Lion Circuits)** | `ESP32S3FH4R2-gerbers.zip` | `fab/ESP32S3FH4R2-gerbers.zip` | Flat 14-file archive (4 copper layers, top/bottom mask, paste, silkscreen, outline, PTH/NPTH `.drl`, `.gbrjob`); passes `lioncircuits-order preflight` with `0` errors and `0` warnings |
| **Gerber + Drill + Drill Maps ZIP** | `fab/ESP32S3FH4R2-gerbers-with-drill-maps.zip` | `fab/gerbers/` | Includes all 14 Gerber/Excellon files plus Gerber X2 (`-drl_map.gbr`) and PDF (`-drl_map.pdf`) drill map files |
| **PTH / NPTH Drill Map Files (Gerber X2 & PDF)** | `fab/gerbers/ESP32S3FH4R2-PTH-drl_map.gbr`, `fab/gerbers/ESP32S3FH4R2-NPTH-drl_map.gbr` | `fab/gerbers/ESP32S3FH4R2-PTH-drl_map.pdf`, `fab/gerbers/ESP32S3FH4R2-NPTH-drl_map.pdf` | Plated and non-plated drill map files in both Gerber X2 and PDF formats |
| **XY / CPL Component Placement Map (CSV)** | `ESP32S3FH4R2-CPL-XY.csv` | `fab/ESP32S3FH4R2-cpl-lioncircuits.csv`, `fab/ESP32S3FH4R2-cpl-populated-only.csv` | Pick-and-place centroid coordinates (`mm`), layer (`Top`), and rotation (`deg`) |
| **Bill of Materials (BOM CSV)** | `ESP32S3FH4R2-BOM.csv` | `fab/ESP32S3FH4R2-bom-lioncircuits.csv`, `fab/ESP32S3FH4R2-bom-populated-only.csv` | Mapped for Lion Circuits, JLCPCB, and turnkey PCBA with MPN, Manufacturer, Footprint, Value, LCSC Part #, Digi-Key Part #, and Assembly Instructions |

---

## 2. Exported Gerber, Drill, and Drill Map Files (`fab/gerbers/`)

| File Name | Layer / Function | Format | Size (Bytes) |
|---|---|---|---|
| `ESP32S3FH4R2-F_Cu.gtl` | Top Copper (`F.Cu`) | Gerber | 178,729 |
| `ESP32S3FH4R2-In1_Cu.g1` | Inner Layer 1 (`In1.Cu` — Solid `GND` Plane) | Gerber | 114,788 |
| `ESP32S3FH4R2-In2_Cu.g2` | Inner Layer 2 (`In2.Cu` — `+3V3` Plane) | Gerber | 127,618 |
| `ESP32S3FH4R2-B_Cu.gbl` | Bottom Copper (`B.Cu`) | Gerber | 90,664 |
| `ESP32S3FH4R2-F_Mask.gts` | Top Solder Mask (`F.Mask`) | Gerber | 10,980 |
| `ESP32S3FH4R2-B_Mask.gbs` | Bottom Solder Mask (`B.Mask`) | Gerber | 2,162 |
| `ESP32S3FH4R2-F_Paste.gtp` | Top Solder Paste (`F.Paste`) | Gerber | 9,784 |
| `ESP32S3FH4R2-B_Paste.gbp` | Bottom Solder Paste (`B.Paste`) | Gerber | 492 |
| `ESP32S3FH4R2-F_Silkscreen.gto` | Top Silkscreen (`F.SilkS`) | Gerber | 81,104 |
| `ESP32S3FH4R2-B_Silkscreen.gbo` | Bottom Silkscreen (`B.SilkS`) | Gerber | 13,465 |
| `ESP32S3FH4R2-Edge_Cuts.gm1` | Board Outline (`Edge.Cuts`, `27.0 × 56.2 mm`) | Gerber | 884 |
| `ESP32S3FH4R2-PTH.drl` | Plated Through Holes (`PTH`) | Excellon (mm) | 2,683 |
| `ESP32S3FH4R2-NPTH.drl` | Non-Plated Through Holes (`NPTH`) | Excellon (mm) | 482 |
| `ESP32S3FH4R2-PTH-drl_map.gbr` | Plated Through-Hole Drill Map | Gerber X2 | 76,997 |
| `ESP32S3FH4R2-NPTH-drl_map.gbr` | Non-Plated Through-Hole Drill Map | Gerber X2 | 43,207 |
| `ESP32S3FH4R2-PTH-drl_map.pdf` | Plated Through-Hole Drill Map | PDF | 19,615 |
| `ESP32S3FH4R2-NPTH-drl_map.pdf` | Non-Plated Through-Hole Drill Map | PDF | 13,066 |
| `ESP32S3FH4R2-job.gbrjob` | Gerber Job Metadata (`4 layers`, `1.6 mm`, `ENIG`) | JSON (`.gbrjob`) | 3,742 |

---

## 3. Bill of Materials (`ESP32S3FH4R2-BOM.csv` / `fab/ESP32S3FH4R2-bom-lioncircuits.csv`)

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
