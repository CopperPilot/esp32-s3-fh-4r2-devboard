# KiCad 10 macOS Library Survey — ESP32-S3FH4R2 Development Board

## 1. Environment & Library Roots
- **Platform:** macOS (`darwin`, `arm64`)
- **KiCad CLI Version:** `10.0.4` (`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`)
- **Stock Symbol Root:** `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols`
- **Stock Footprint Root:** `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints`
- **Stock 3D Model Root (`${KICAD10_3DMODEL_DIR}`):** `/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels`

---

## 2. Component-by-Component Library Mapping Summary

| Component / Function | Symbol `Library:Name` | Symbol Pins | Footprint `Library:Name` | Footprint Pads | 3D Model File (`.step`) | Custom / Adaptation Needed |
|---|---|---|---|---|---|---|
| **ESP32-S3FH4R2 SoC (QFN-56)** | `MCU_Espressif:ESP32-S3` | 57 pins (`1`..`57`; `2/3` and `55/56` stacked) | `Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm` (or `_ThermalVias`) | `'1'`..`'56'` (SMD), `'57'` (EP), plus 9 unnumbered `''` paste pads (or 9 `'57'` thru-hole thermal vias) | `Package_DFN_QFN.3dshapes/QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm.step` (**Verified**) | None. Set symbol `Value` to `ESP32-S3FH4R2`. |
| **USB-C 2.0 16-Pin Receptacle** | `Connector:USB_C_Receptacle_USB2.0_16P` | 17 pins (`A1, A4..A9, A12, B1, B4..B9, B12, SH`; `GND` & `VBUS` stacked, `D+` & `D-` split) | `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` (or `USB_C_Receptacle_HRO_TYPE-C-31-M-12`) | 16 SMD (`A1..A12, B1..B12`), 4 THT shield (`'SH'`), 2 NPTH (`''`) | `Connector_USB.3dshapes/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step` (**Verified**; `HRO_TYPE-C-31-M-12.step` **Missing**) | Prefer `GCT_USB4105-xx-A_16P_TopMnt_Horizontal` for verified 3D model, or assign GCT/Amphenol 3D model if using `HRO_TYPE-C-31-M-12`. |
| **USB ESD Protection (`USBLC6-2SC6`)** | `Power_Protection:USBLC6-2SC6` (extends `USBLC6-2P6`) | 6 pins (`1:I/O1, 2:GND, 3:I/O2, 4:I/O2, 5:VBUS, 6:I/O1`) | `Package_TO_SOT_SMD:SOT-23-6` (default; or `SOT-363_SC-70-6` for `USBLC6-2P6`) | `'1'`..`'6'` (6 SMD pads) | `Package_TO_SOT_SMD.3dshapes/SOT-23-6.step` (**Verified**) | None. Default footprint is pre-assigned. |
| **3.3V LDO Regulator (`AP2112K-3.3`)** | `Regulator_Linear:AP2112K-3.3` (extends `AP2204K-1.5`) | 5 pins (`1:VIN, 2:GND, 3:EN, 4:NC[hidden], 5:VOUT`) | `Package_TO_SOT_SMD:SOT-23-5` | `'1'`..`'5'` (5 SMD pads) | `Package_TO_SOT_SMD.3dshapes/SOT-23-5.step` (**Verified**) | None. Pin 4 (`NC`) is hidden `no_connect` in symbol. |
| **40 MHz 4-Pin SMD Crystal** | `Device:Crystal_GND24` | 4 pins (`1:1, 2:G, 3:3, 4:G[hidden stacked on 2]`) | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` (or `Crystal_SMD_2016-4Pin_2.0x1.6mm` / `Crystal_SMD_2520-4Pin_2.5x2.0mm`) | `'1'`, `'2'`, `'3'`, `'4'` (4 SMD pads) | `Crystal.3dshapes/Crystal_SMD_3225-4Pin_3.2x2.5mm.step` (**Verified**) | None. Pins 2 and 4 are stacked at `(0, -5.08)`. |
| **Tactile Pushbuttons (RESET / BOOT)** | `Switch:SW_Push` | 2 pins (`1:1, 2:2`) | `Button_Switch_SMD:SW_SPST_B3U-1000P` (2 pads) or `Button_Switch_SMD:SW_SPST_PTS810` / `SW_SPST_TL3342` / `SW_Push_1P1T_NO_CK_KMR2` (4 pads: `'1'x2, '2'x2`) | `'1'`, `'2'` (SMD; 1x each or 2x each jumper-paired) | `Button_Switch_SMD.3dshapes/SW_SPST_B3U-1000P.step`, `SW_SPST_PTS810.step`, `SW_SPST_TL3342.step` (**Verified**; `SW_SPST_CK_KXT3.step` **Missing**) | None. Avoid `SW_SPST_CK_KXT3` unless a 3D model is assigned. |
| **Status LED / Addressable RGB LED** | `Device:LED` (or `LED:WS2812B`) | `Device:LED`: 2 pins (`1:K, 2:A`); `LED:WS2812B`: 4 pins (`1:VDD, 2:DOUT, 3:VSS, 4:DIN`) | `LED_SMD:LED_0603_1608Metric` / `LED_0402_1005Metric` / `LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm` | `'1'`, `'2'` (or `'1'`..`'4'` for WS2812B) | `LED_SMD.3dshapes/LED_0603_1608Metric.step`, `LED_0402_1005Metric.step`, `LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm.step` (**Verified**) | None. Note: Pin 1 of `Device:LED` is Cathode (`K`), Pin 2 is Anode (`A`). |
| **Resistors (`R`)** | `Device:R` | 2 pins (`1, 2`) | `Resistor_SMD:R_0402_1005Metric` / `R_0603_1608Metric` / `R_0805_2012Metric` | `'1'`, `'2'` (2 SMD pads) | `Resistor_SMD.3dshapes/R_0402_1005Metric.step`, `R_0603_1608Metric.step`, `R_0805_2012Metric.step` (**Verified**) | None. |
| **Capacitors (`C`)** | `Device:C` | 2 pins (`1, 2`) | `Capacitor_SMD:C_0402_1005Metric` / `C_0603_1608Metric` / `C_0805_2012Metric` / `C_1206_3216Metric` | `'1'`, `'2'` (2 SMD pads) | `Capacitor_SMD.3dshapes/C_0402_1005Metric.step`, `C_0603_1608Metric.step`, `C_0805_2012Metric.step` (**Verified**) | None. |
| **Inductors (`L`, RF/PI matching)** | `Device:L` | 2 pins (`1, 2`) | `Inductor_SMD:L_0402_1005Metric` / `L_0603_1608Metric` | `'1'`, `'2'` (2 SMD pads) | `Inductor_SMD.3dshapes/L_0402_1005Metric.step`, `L_0603_1608Metric.step` (**Verified**) | None. |
| **Schottky Diode (`D_Schottky`)** | `Device:D_Schottky` | 2 pins (`1:K, 2:A`) | `Diode_SMD:D_SOD-123` / `D_SOD-323` / `D_SOD-523` / `D_SMA` | `'1'`, `'2'` (2 SMD pads; Pad 1 = Cathode, Pad 2 = Anode) | `Diode_SMD.3dshapes/D_SOD-123.step`, `D_SOD-323.step`, `D_SOD-523.step`, `D_SMA.step` (**Verified**) | None. Note: Pin 1 is Cathode (`K`), Pin 2 is Anode (`A`). |
| **2.4 GHz Antenna / Coaxial (`Antenna_Chip` / `Antenna_Shield` / `Conn_Coaxial`)** | `Device:Antenna_Chip`, `Device:Antenna_Shield`, `Connector:Conn_Coaxial` | 2 pins (`1, 2`) | `RF_Antenna:Johanson_2450AT18x100` / `Johanson_2450AT43F0100` / `Pulse_W3000` / `Texas_SWRA117D_2.4GHz_Left` / `Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical` | `'1'`, `'2'` (SMD; U.FL has `'1'` signal + `'2'x2` GND shield pads) | `RF_Antenna.3dshapes/Johanson_2450AT18x100.step`, `Pulse_W3000.step`, `Connector_Coaxial.3dshapes/U.FL_Hirose_U.FL-R-SMT-1_Vertical.step` (**Verified**) | For `Device:Antenna_Chip` / `Device:Antenna_Shield`, Pin 1 (`input`) driven via passive matching network may need `set_pin_function` to `passive` to avoid ERC `pin_not_driven`. |
| **Pin Headers / Sockets (`1x20`, `1x19`, `1x04`)** | `Connector_Generic:Conn_01x20`, `Conn_01x19`, `Conn_01x04` (or `Connector:Conn_01x20_Pin`, etc.) | `1`..`20`, `1`..`19`, `1`..`4` (passive) | `Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical`, `PinHeader_1x19_P2.54mm_Vertical`, `PinHeader_1x04_P2.54mm_Vertical` (or `Connector_PinSocket_2.54mm:*`) | `'1'`..`'20'`, `'1'`..`'19'`, `'1'`..`'4'` (thru-hole) | `Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x20_P2.54mm_Vertical.step`, `PinHeader_1x19_P2.54mm_Vertical.step`, `PinHeader_1x04_P2.54mm_Vertical.step` (**Verified**) | None. |
| **M2 Mounting Holes (`2.2mm`)** | `Mechanical:MountingHole` (0 pins) or `Mechanical:MountingHole_Pad` (1 pin: `1`) | `0` pins (or Pin `1` `input` on `MountingHole_Pad`) | `MountingHole:MountingHole_2.2mm_M2` (NPTH) or `MountingHole:MountingHole_2.2mm_M2_Pad` / `MountingHole_2.2mm_M2_Pad_Via` (plated pad `'1'`) | `''` (NPTH) or `'1'` (thru-hole) | None needed (mechanical drill/hole, `exclude_from_pos_files exclude_from_bom`) | If using `Mechanical:MountingHole_Pad` connected to `GND`, Pin 1 is `input` (fine when `GND` has `PWR_FLAG`, or set pin function to `passive`). |

---

## 3. Detailed Pin/Pad and File Path Reference

### 3.1 ESP32-S3FH4R2 (`MCU_Espressif:ESP32-S3`)
- **Symbol Library File:** `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/MCU_Espressif.kicad_sym`
- **Symbol Identifier:** `MCU_Espressif:ESP32-S3`
- **Default Footprint Property:** `Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm`
- **Footprint Files:**
  - `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_DFN_QFN.pretty/QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm.kicad_mod`
  - `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_DFN_QFN.pretty/QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm_ThermalVias.kicad_mod`
- **3D Model File:** `/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels/Package_DFN_QFN.3dshapes/QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm.step` (Exists)
- **Pin-to-Pad Mapping (57 Pins):**
  - `1`: `LNA_IN` (`bidirectional`)
  - `2`: `VDD3P3` (`power_in`, at `-2.54, 38.1, 270`)
  - `3`: `VDD3P3` (`passive`, hidden, stacked with Pin 2 at `-2.54, 38.1, 270`)
  - `4`: `CHIP_PU` (`input`)
  - `5..19`: `GPIO0`..`GPIO14` (`bidirectional`)
  - `20`: `VDD3P3_RTC` (`power_in`, at `0, 38.1, 270`)
  - `21`: `XTAL_32K_P` (`passive`, GPIO15)
  - `22`: `XTAL_32K_N` (`passive`, GPIO16)
  - `23..24`: `GPIO17`..`GPIO18` (`bidirectional`)
  - `25`: `GPIO19/USB_D-` (`bidirectional`)
  - `26`: `GPIO20/USB_D+` (`bidirectional`)
  - `27`: `GPIO21` (`bidirectional`)
  - `28`: `SPICS1` (`bidirectional`, used by internal 2MB PSRAM on ESP32-S3FH4R2)
  - `29`: `VDD_SPI` (`power_in`, at `2.54, 38.1, 270`, 3.3V internal flash/PSRAM rail)
  - `30..35`: `SPIHD`, `SPIWP`, `SPICS0`, `SPICLK`, `SPIQ`, `SPID` (`bidirectional`, used by internal 4MB Flash / 2MB PSRAM on ESP32-S3FH4R2)
  - `36`: `SPICLK_N` (`bidirectional`, GPIO48)
  - `37`: `SPICLK_P` (`bidirectional`, GPIO47)
  - `38..43`: `GPIO33`..`GPIO38` (`bidirectional`)
  - `44`: `MTCK` (`bidirectional`, GPIO39)
  - `45`: `MTDO` (`bidirectional`, GPIO40)
  - `46`: `VDD3P3_CPU` (`power_in`, at `5.08, 38.1, 270`)
  - `47`: `MTDI` (`bidirectional`, GPIO41)
  - `48`: `MTMS` (`bidirectional`, GPIO42)
  - `49`: `U0TXD` (`bidirectional`, GPIO43)
  - `50`: `U0RXD` (`bidirectional`, GPIO44)
  - `51..52`: `GPIO45`..`GPIO46` (`bidirectional`)
  - `53`: `XTAL_N` (`output`)
  - `54`: `XTAL_P` (`input`)
  - `55`: `VDDA` (`power_in`, at `-5.08, 38.1, 270`)
  - `56`: `VDDA` (`passive`, hidden, stacked with Pin 55 at `-5.08, 38.1, 270`)
  - `57`: `GND` (`power_in`, at `0, -38.1, 90`, Exposed Pad)

### 3.2 USB Type-C 16P Receptacle (`Connector:USB_C_Receptacle_USB2.0_16P`)
- **Symbol Library File:** `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Connector.kicad_sym`
- **Footprint Library File (Verified 3D Model):** `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_USB.pretty/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.kicad_mod`
- **Alternate Footprint Library File (No Bundled 3D Model):** `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_USB.pretty/USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod`
- **3D Model File:** `/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels/Connector_USB.3dshapes/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step` (Exists)
- **Pin-to-Pad Mapping (17 Symbol Pins -> 20 Electrical Pads + 2 NPTH):**
  - `A1` (visible) + `A12, B1, B12` (hidden, stacked at `0, -22.86, 90`): `GND` (`passive`) -> SMD pads `A1, A12, B1, B12`
  - `A4` (visible) + `A9, B4, B9` (hidden, stacked at `15.24, 15.24, 180`): `VBUS` (`passive`) -> SMD pads `A4, A9, B4, B9`
  - `A5`: `CC1` (`bidirectional`, at `15.24, 10.16, 180`) -> SMD pad `A5`
  - `B5`: `CC2` (`bidirectional`, at `15.24, 7.62, 180`) -> SMD pad `B5`
  - `A6`: `D+` (`bidirectional`, at `15.24, -2.54, 180`) & `B6`: `D+` (`bidirectional`, at `15.24, -5.08, 180`) -> SMD pads `A6, B6` (separate pins in schematic; tie together)
  - `A7`: `D-` (`bidirectional`, at `15.24, 2.54, 180`) & `B7`: `D-` (`bidirectional`, at `15.24, 0, 180`) -> SMD pads `A7, B7` (separate pins in schematic; tie together)
  - `A8`: `SBU1` (`bidirectional`, at `15.24, -12.7, 180`) -> SMD pad `A8`
  - `B8`: `SBU2` (`bidirectional`, at `15.24, -15.24, 180`) -> SMD pad `B8`
  - `SH`: `SHIELD` (`passive`, at `-7.62, -22.86, 90`) -> 4 THT shield pads numbered `SH`
