# ESP32-S3FH4R2 BOM Sourcing & Datasheet Circuit Reference

## 1. Verified BOM & Distributor Cross-Reference Table

All LCSC / JLCPCB part numbers (`C-numbers`), library classifications (`Basic` vs `Extended`), and stock counts below were verified against the live JLCPCB SMT / LCSC catalog.

| Ref Category | MPN | Manufacturer | Package | LCSC Part # | Digi-Key Part # / Alternate | JLCPCB Status (Stock) | Key Electrical Specs & Circuit Role |
|---|---|---|---|---|---|---|---|
| **U1 (SoC)** | `ESP32-S3FH4R2` | Espressif Systems | QFN-56-1EP (7x7 mm, P0.4 mm, EP 4x4 mm) | `C3013940` | `1965-ESP32-S3FH4R2CT-ND` (`ESP32-S3FH4R2`) | Extended (2,641) | Dual-core XTensa LX7 240 MHz, 2.4 GHz Wi-Fi + BLE 5.0, in-package 4 MB Quad Flash + 2 MB Quad PSRAM (`VDD_SPI` = 3.3 V), 3.0–3.6 V supply |
| **Y1 (40 MHz Crystal — Primary 12 pF)** | `X1E0000210179` (`TSX-3225 40.0000MF10Z-AC3`) | Seiko Epson | SMD3225-4P (3.2x2.5 mm) | `C255942` | `SER4097CT-ND` (`X1E000021017900`) / `535-9657-1-ND` (`ABM8-40.000MHZ-B2-T`) | Extended (1,281) | 40.000 MHz fundamental, `CL = 12 pF`, `±10 ppm` tolerance, `±20 ppm` stability, `ESR <= 40 Ω`, `-40°C to +85°C`; use `C1 = C2 = 15 pF to 18 pF` |
| **Y1 (40 MHz Crystal — High-Stock 15 pF)** | `X322540MPB4SI` | YXC (Yangxing Tech) | SMD3225-4P (3.2x2.5 mm) | `C9010` | `535-10256-1-ND` (`ABM8-40.000MHZ-B4Y-T`, 15–18 pF alt) | Extended (66,781) | 40.000 MHz fundamental, `CL = 15 pF`, `±10 ppm` tolerance, `ESR <= 40 Ω`, `-40°C to +85°C`; use `C1 = C2 = 22 pF` (or `18 pF` with ~6 pF stray) |
| **Y1 (40 MHz Crystal — 12 pF Alt)** | `TX322540M4FBCE2T` | Yajingxin | SMD3225-4P (3.2x2.5 mm) | `C5186937` | `ECS-400-12-33-CKM-TR` (12 pF 10 ppm alt) | Extended (7,145) | 40.000 MHz fundamental, `CL = 12 pF`, `±10 ppm` tolerance, `ESR <= 30 Ω`, `-40°C to +85°C`; use `C1 = C2 = 15 pF to 18 pF` |
| **Y1 (40 MHz Crystal — 10 pF Alt)** | `X322540MMB4SI` | YXC (Yangxing Tech) | SMD3225-4P (3.2x2.5 mm) | `C5210647` | `535-14925-1-ND` (`ABM8W-40.0000MHZ-4-B1U-T3`) | Extended (2,993) | 40.000 MHz fundamental, `CL = 10 pF`, `±10 ppm` tolerance, `ESR <= 40 Ω`, `-40°C to +85°C`; use `C1 = C2 = 12 pF to 15 pF` |
| **U2 (3.3 V LDO)** | `AP2112K-3.3TRG1` | Diodes Incorporated | SOT-23-5 (SOT-25-5) | `C51118` | `AP2112K-3.3TRG1DICT-ND` | Extended (8,145) | 3.3 V fixed CMOS LDO, 600 mA continuous, `V_IN = 2.5 V to 6.0 V`, `V_DO = 250 mV @ 600 mA`, `I_Q = 55 µA`, `PSRR = 65 dB`; stable with `>= 1.0 µF` X5R/X7R ceramic on IN and OUT |
| **U3 (USB ESD Array)** | `USBLC6-2SC6` | STMicroelectronics | SOT-23-6L | `C7519` (Alt: Tech Public `C2827654`) | `497-5235-1-ND` | Extended (43,593) | Low-capacitance USB 2.0 ESD array (`C_line = 2.5 pF typ / 3.5 pF max`), `V_BR >= 6 V` on VBUS & I/O rail, `V_CL = 17 V @ I_PP = 5 A`, IEC 61000-4-2 ±15 kV air / ±8 kV contact |
| **J1 (USB-C 16-Pin)** | `TYPE-C-31-M-12` | Korean Hroparts Elec (HRO) | USB-C-16P SMD Right-Angle | `C165948` (Alt: Shou Han `C2765186`) | `2073-USB4105-GF-ACT-ND` (`GCT USB4105-GF-A`) / `102-UJC-HP-3-SMT-TRCT-ND` | Extended (196,421) | 16-pin USB 2.0 Type-C receptacle (VBUS, GND, CC1, CC2, D+1/D+2, D-1/D-2, SBU1, SBU2 + 4 THT/SMD shield tabs), 20 V / 5 A rated, 10,000 mating cycles |
| **D1 (VBUS Schottky)** | `B5819W SL` | JSCJ (Changjiang Elec) | SOD-123 | `C8598` (SOD-323 `1N5819WS`: `C191023`) | `B5819W-7-FDICT-ND` (`Diodes Inc B5819W-7-F`) | **Basic** (971,056) | 40 V, 1 A Schottky barrier diode, `V_F <= 0.60 V @ 1 A` (~0.38 V @ 200 mA), reverse current protection between USB VBUS and 5 V rail |
| **ANT1 (2.4 GHz Chip Antenna — In Stock)** | `ANT3216LL00R2400A` | Yageo (Alt: Pulse `C22423581`) | 1206 (3.2x1.6x1.2 mm) | `C293767` | `13-ANT3216LL00R2400ACT-ND` (`Yageo ANT3216LL00R2400A`) | Extended (35,996) | 2.4–2.5 GHz multilayer ceramic chip antenna (160 MHz BW), `50 Ω` nominal, peak gain up to 5.05 dBi (board-dependent), 1 W max power |
| **ANT1 (2.4 GHz Chip Antenna — Alt)** | `2450AT18A100E` | Johanson Technology | 1206 (3.2x1.6x1.3 mm) | `C89334` *(0 stock on JLC)* | `712-1005-1-ND` (`2450AT18A100E`) | Extended (0 — OOS) | 2400–2500 MHz ceramic chip antenna, `0.5 dBi` peak gain, `50 Ω`, 2 W max. *Note: Out of stock on JLCPCB; use `C293767` (`ANT3216LL00R2400A`) for JLCPCB PCBA* |
| **J2 (u.FL RF Connector)** | `U.FL-R-SMT-1(80)` / `U.FL-R-SMT-1(10)` | Hirose Electric (HRS) | SMD 2.6x2.6x1.25 mm | `C88374` (`(80)` reel) / `C88373` (`(10)` reel) | `H9161CT-ND` (`U.FL-R-SMT-1(10)`) | Extended (362,030 for `C88374`) | DC–6 GHz ultra-miniature `50 Ω` coaxial receptacle (IPEX MHF1 compatible), VSWR <= 1.3; `(80)` and `(10)` share identical footprint (`2.6x2.6 mm`) |
| **SW1, SW2 (Tactile Switch — Basic 5.1x5.1 mm)** | `B3U-1000P` | XKB Connection | SMD-4P (5.1x5.1x1.5 mm) | `C318884` | `450-1804-1-ND` (`TE FSM4JSMATR`) / `Omron B3U-1000P` | **Basic** (1,066,650) | SPST-NO low-profile SMD tactile switch, 160 gf (1.6 N), 12 VDC / 50 mA, 100k cycles; zero JLCPCB extended-part feeder fee |
| **SW1, SW2 (Tactile Switch — Compact 3x4 mm)** | `TS-1088R-02026` (Alt: `TS-1185-C-A-B-B`) | XUNPU (Alt: XKB `C465999`) | SMD-4P (4.0x3.0x2.0 mm) | `C455280` (LCSC alt: `C720477`) | `CKN10396CT-ND` (`C&K PTS820 J25K SMTR LFS`) / `732-7102-1-ND` (`Wurth 434121025816`) | Extended (132,890) | SPST-NO subminiature 3x4 mm SMD tactile switch, 260 gf (2.6 N), 12 VDC / 50 mA, 100k cycles |
| **R_CC1, R_CC2 (5.1 kΩ)** | `0402WGF5101TCE` | UNI-ROYAL | 0402 | `C25905` | `311-5.10KLRCT-ND` (`Yageo RC0402FR-075K1L`) | **Basic** (4,959,500) | `5.1 kΩ ±1%`, 62.5 mW (1/16 W), 50 V; required independent pull-downs on USB-C `CC1` and `CC2` for 5 V Rd sink detection |
| **R_EN, R_BOOT (10 kΩ)** | `0402WGF1002TCE` | UNI-ROYAL | 0402 | `C25744` | `311-10.0KLRCT-ND` (`Yageo RC0402FR-0710KL`) | **Basic** (16,337,689) | `10 kΩ ±1%`, 62.5 mW, 50 V; pull-ups on `CHIP_PU` (`EN`) and `GPIO0` (`BOOT`) |
| **R_USB_DM/DP (22 Ω)** | `0402WGF220JTCE` | UNI-ROYAL | 0402 | `C25092` | `311-22.0LRCT-ND` (`Yageo RC0402FR-0722RL`) | **Basic** (2,818,226) | `22 Ω ±1%`, 62.5 mW, 50 V; optional 0 Ω / 22 Ω series damping on `USB_D-` (`GPIO19`) and `USB_D+` (`GPIO20`) |
| **R_LED1, R_LED2 (1 kΩ)** | `0402WGF1001TCE` | UNI-ROYAL | 0402 | `C11702` | `311-1.00KLRCT-ND` (`Yageo RC0402FR-071KL`) | **Basic** (21,247,933) | `1 kΩ ±1%`, 62.5 mW, 50 V; current-limiting resistor for 3.3 V power/status LEDs (~1.0–1.5 mA) |
| **R_JMP / R_XTAL (0 Ω)** | `0402WGF0000TCE` | UNI-ROYAL | 0402 | `C17168` | `311-0.0LRCT-ND` (`Yageo RC0402JR-070RL`) | **Basic** (10,726,812) | `0 Ω` jumper (<50 mΩ), 1 A rated; used on `XTAL_P` series tuning pad and RF antenna / u.FL path selection |
| **C_DEC (100 nF 0402)** | `CL05B104KO5NNNC` | Samsung Electro-Mechanics | 0402 | `C1525` | `1276-1000-1-ND` (`CL05B104KO5NNNC`) | **Basic** (35,250,212) | `100 nF (0.1 µF) ±10%`, 16 V, X7R; high-frequency decoupling on `VDDA`, `VDD3P3`, `VDD3P3_RTC`, `VDD_SPI`, `VDD3P3_CPU`, and switch debounce |
| **C_DEC1U (1 µF 0402)** | `CL05A105KA5NQNC` | Samsung Electro-Mechanics | 0402 | `C52923` | `1276-1006-1-ND` (`CL05A105KA5NQNC`) | **Basic** (10,689,612) | `1 µF ±10%`, 25 V, X5R; local rail decoupling for `VDD3P3`, `VDD_SPI`, `CHIP_PU` RC delay (`R=10k, C=1µF`), and LDO bypass |
| **C_BULK10U (10 µF 0402 / 0603)** | `CL05A106MQ5NUNC` (0402) / `CL10A106MP8NNNC` (0603) | Samsung Electro-Mechanics | 0402 / 0603 | `C15525` (0402) / `C19702` (0603) | `1276-1099-1-ND` (`CL10A106MP8NNNC`) | **Basic** (10,031,694 / 11,576,623) | `10 µF`, 6.3 V (0402) / 10 V (0603), X5R; required RF PA bulk decoupling on `VDD3P3` (pins 2, 3) and LDO input/output filtering |
| **C_BULK22U (22 µF 0603)** | `CL10A226MQ8NRNC` | Samsung Electro-Mechanics | 0603 | `C59461` | `1276-1119-1-ND` (`CL10A226MQ8NRNC`) | **Basic** (4,478,859) | `22 µF ±20%`, 6.3 V, X5R; main 3.3 V rail bulk reservoir at LDO output / SoC entry |
| **C_XTAL1, C_XTAL2 (15 pF / 18 pF / 12 pF)** | `0402CG150J500NT` / `0402CG180J500NT` / `0402CG120J500NT` | FH (Fenghua Advanced Tech) | 0402 | `C1548` (15 pF) / `C1549` (18 pF) / `C1547` (12 pF) | `490-5921-1-ND` (`Murata GRM1555C1H150JA01D`) | **Basic** (1,319,858 / 1,264,517 / 2,111,259) | `15 pF / 18 pF / 12 pF ±5%`, 50 V, C0G/NP0; crystal load capacitors matched to selected 40 MHz crystal `CL` |
| **L_RF / C_RF1 / C_RF2 (RF Pi Match)** | `SDCL1005C2N7STDF` (2.7 nH) + `0402CG1R5C500NT` (1.5 pF) | Sunlord / FH | 0402 | `C27123` (2.7 nH) / `C1552` (1.5 pF) | `490-14577-1-ND` (`Murata LQG15HS2N7S02D`) | Extended (113,679 / 183,850) | 0402 C-L-C Pi-network on `LNA_IN` (Pin 1) for 50 Ω impedance matching & harmonic suppression |
| **D_PWR (Red 0603 LED)** | `KT-0603R` | Hubei KENTO Elec | 0603 | `C2286` | `160-1447-1-ND` (`Lite-On LTST-C190KRKT`) | **Basic** (7,003,931) | Red 645 nm SMD LED, `V_F = 1.8–2.4 V`, 20 mA max, 300 mcd |
| **D_STAT (Green / White 0603 LED)** | `KT-0603G` (Green) / `KT-0603W` (White) | Hubei KENTO Elec | 0603 | `C12624` (Green, Ext) / `C2290` (White, **Basic**) | `160-1446-1-ND` (`Lite-On LTST-C190KGKT`) | Extended (`C12624`: 385,225) / **Basic** (`C2290`: 1,227,952) | Green 525 nm (`V_F = 3.1 V`) or White (`V_F = 2.6–3.1 V`, Basic library) 0603 status LED |

---

## 2. Critical Sourcing Findings & Catalog Corrections

1. **ESP32-S3FH4R2 LCSC Part Number (`C3013940`)**:
   - The bare QFN-56 7x7 mm IC `ESP32-S3FH4R2` (with 4 MB Flash and 2 MB Quad PSRAM integrated in-package) is **`C3013940`** (JLCPCB Extended, 2,641 in stock).
   - Do not confuse with `C2913206` (`ESP32-S3-MINI-1-N8` module).
2. **40 MHz Crystal LCSC Part Number (`C9010` / `C255942` / `C5186937`)**:
   - On LCSC/JLCPCB, **`C9006` is a 25 MHz crystal (`X322525MOB4SI`)**, NOT 40 MHz, and `X322540MLB4SI` is not stocked in the active JLCPCB SMT library.
   - For a **12 pF, 40 MHz ±10 ppm SMD3225-4P** crystal stocked on both JLCPCB and Digi-Key, use **Seiko Epson `X1E0000210179`** (`C255942`, 1,281 in stock) or **Yajingxin `TX322540M4FBCE2T`** (`C5186937`, 7,145 in stock).
   - For the highest-stock **YXC (Yangxing)** 40 MHz ±10 ppm SMD3225-4P crystal on JLCPCB, use **`X322540MPB4SI`** (`C9010`, 66,781 in stock, `CL = 15 pF`) or **`X322540MMB4SI`** (`C5210647`, 2,993 in stock, `CL = 10 pF`).
3. **2.4 GHz Chip Antenna (`C293767` vs `C89334`)**:
   - Johanson `2450AT18A100E` is LCSC **`C89334`** (note: `C127646` is an unrelated Walsin SAW filter) and currently has **0 stock** at JLCPCB/LCSC, though it is stocked at Digi-Key (`712-1005-1-ND`).
   - **Yageo `ANT3216LL00R2400A`** is LCSC **`C293767`** (JLCPCB Extended, **35,996 in stock**; LCSC **14,020 in stock**). Its land pattern is a 2-pad 1206 (3.2x1.6 mm) footprint (Pin 1 = Feed, Pin 2 = Solder/Mechanical anchor), whereas Johanson `2450AT18A100E` uses a different feed/keep-out geometry. Commit to `ANT3216LL00R2400A` (`C293767`) or `U.FL-R-SMT-1(80)` (`C88374`) before layout.
4. **Hirose u.FL Connector Packaging Suffix (`C88374` vs `C88373`)**:
   - `U.FL-R-SMT-1(10)` (`C88373`) has only 149 pcs at JLCPCB, whereas **`U.FL-R-SMT-1(80)` (`C88374`)** has **362,030 pcs in stock** at JLCPCB. Both are genuine Hirose U.FL connectors with identical mechanical dimensions and footprint.
5. **Tactile Switch Footprint vs JLCPCB Basic Status (`C318884` vs `C455280`)**:
   - XKB **`B3U-1000P` (`C318884`)** is the only SMD 4-pin tactile switch in the **JLCPCB Basic** library (1,066,650 in stock; saves the Extended feeder setup fee), and its body is **5.1 x 5.1 mm**.
   - If a **3.0 x 4.0 mm** switch is preferred for board density, use **XUNPU `TS-1088R-02026` (`C455280`, 132,890 in stock, Extended)** or **XKB `TS-1185-C-A-B-B` (`C465999`, 1,911 in stock, Extended)**.

---

## 3. Datasheet Circuit & Layout Requirements by Subsystem

### 3.1 ESP32-S3FH4R2 (QFN-56 7x7 mm, KiCad Footprint: `Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm`)
- **Authoritative QFN-56 Power, RF, Clock, USB, and Strapping Pin Map** (verified against KiCad 10 `MCU_Espressif:ESP32-S3` and Espressif ESP32-S3 Datasheet):
  - **Pin 1 (`LNA_IN`)**: RF input/output. Route via a 50 Ω controlled-impedance microstrip/coplanar waveguide through a C-L-C Pi-matching network (`C_RF1`, `L_RF`, `C_RF2`) to the antenna or u.FL connector.
  - **Pins 2, 3 (`VDD3P3`)**: Analog/RF PA power supply (3.0–3.6 V). Requires a **10 µF** (`C15525`/`C19702`) + **100 nF** (`C1525`) ceramic decoupling network placed immediately adjacent to Pins 2–3, plus an optional series CLC filter inductor (2.4–3.3 nH) on Pin 2 per Espressif reference schematic.
  - **Pin 4 (`CHIP_PU` / `EN`)**: Active-high reset/enable. Never leave floating. Connect a **10 kΩ pull-up resistor (`C25744`) to 3.3 V** and a **1 µF capacitor (`C52923`) to GND** (plus a 100 nF capacitor at the reset switch) to guarantee clean power-on reset timing (`t > 50 µs` after 3.3 V reaches 3.0 V).
  - **Pin 5 (`GPIO0`), Pin 8 (`GPIO3`), Pin 51 (`GPIO45`), Pin 52 (`GPIO46`)**: Strapping pins.
    - `GPIO0` (Pin 5): Internal weak pull-up; High = SPI Boot, Low = Download Boot (jointly with `GPIO46 = 0`). Connect tactile `BOOT` switch from `GPIO0` to GND with an external 10 kΩ pull-up (`C25744`) and 100 nF debounce cap (`C1525`).
    - `GPIO45` (Pin 51): Controls `VDD_SPI` voltage (`0` = 3.3 V, `1` = 1.8 V). Has internal weak pull-down. **In `ESP32-S3FH4R2`, the in-package 4 MB Flash and 2 MB PSRAM operate at 3.3 V**, so **never pull `GPIO45` high at reset**.
    - `GPIO46` (Pin 52): Internal weak pull-down. Must be Low (`0`) during reset to allow Download Boot when `GPIO0 = 0`. Do not pull high externally.
  - **Pin 20 (`VDD3P3_RTC`)**: RTC/backup domain 3.3 V supply. Decouple locally with **100 nF (`C1525`)**.
  - **Pins 25, 26 (`GPIO19/USB_D-`, `GPIO20/USB_D+`)**: Native Full-Speed USB 2.0 OTG/Serial-JTAG differential pair. Route as a 90 Ω differential pair with minimal stub length through `USBLC6-2SC6` (`C7519`) to the USB-C receptacle.
  - **Pins 28–37 (`SPICS1`, `VDD_SPI`, `SPIHD`, `SPIWP`, `SPICS0`, `SPICLK`, `SPIQ`, `SPID`, `SPICLK_N`, `SPICLK_P`)**:
    - **Pin 29 (`VDD_SPI`)**: Decouple with **1 µF (`C52923`) + 100 nF (`C1525`)** close to Pin 29. Driven internally at 3.3 V by the `VDD_SPI` regulator (or tied to 3.3 V if configured).
    - **Pins 28, 30–35**: Internally connected to the in-package 4 MB Flash and 2 MB Quad PSRAM on `ESP32-S3FH4R2`. **Do not connect external loads to `SPICS1`, `SPIHD`, `SPIWP`, `SPICS0`, `SPICLK`, `SPIQ`, `SPID`** as recommended by the ESP32-S3 datasheet for in-package Flash/PSRAM variants.
  - **Pin 46 (`VDD3P3_CPU`)**: Digital CPU power supply (3.0–3.6 V). Decouple with **1 µF (`C52923`) + 100 nF (`C1525`)** right at Pin 46.
  - **Pins 53, 54 (`XTAL_N`, `XTAL_P`)**: External 40 MHz crystal oscillator output (`XTAL_N`, Pin 53) and input (`XTAL_P`, Pin 54). Place a **0 Ω series resistor (`C17168`)** (tunable to 22–47 Ω if drive level reduction is needed) on `XTAL_N` (Pin 53) per Espressif guidelines.
  - **Pins 55, 56 (`VDDA`)**: Analog 3.3 V power supply. Decouple each pin with **100 nF (`C1525`)** plus a shared **1 µF (`C52923`) / 10 µF (`C15525`)** capacitor placed immediately adjacent to Pins 55–56.
  - **Pin 57 (`GND`)**: Center exposed thermal/ground pad (`4.0 x 4.0 mm`). Connect to the continuous inner/bottom GND plane via at least a 3x3 or 4x4 thermal/ground via array (`0.3 mm` drill).

### 3.2 40 MHz Crystal Circuit (`Y1`: `C255942` / `C9010`)
- Connect crystal Pin 1 and Pin 3 to `XTAL_P` (Pin 54) and `XTAL_N` (Pin 53) (via a 0 Ω series footprint on `XTAL_N`).
- Connect crystal Pin 2 and Pin 4 (lid/case ground) directly to GND with a local guard ring and ground vias isolating the crystal from RF (`LNA_IN`) and switching currents.
- Load capacitance formula: `C_1 = C_2 = 2 * (C_L - C_stray)`, where `C_stray` is typically `2 pF to 3 pF` (pin + short trace capacitance):
  - For a `C_L = 12 pF` crystal (`X1E0000210179` `C255942` or `TX322540M4FBCE2T` `C5186937`): use **`18 pF` (`C1549`) or `15 pF` (`C1548`)** 0402 C0G capacitors.
  - For a `C_L = 10 pF` crystal (`X322540MMB4SI` `C5210647`): use **`15 pF` (`C1548`) or `12 pF` (`C1547`)** 0402 C0G capacitors.
  - For a `C_L = 15 pF` crystal (`X322540MPB4SI` `C9010`): use **`22 pF` or `18 pF` (`C1549`)** 0402 C0G capacitors.

### 3.3 Power Supply (`J1` -> `D1` -> `U2` `AP2112K-3.3TRG1`)
- **USB-C Receptacle (`J1` `TYPE-C-31-M-12`, `C165948`)**:
  - Tie both `VBUS` pins (`A4/B9`, `B4/A9`) together; tie both `GND` pins (`A1/B12`, `B1/A12`) and the 4 shield pads to `GND`.
  - Short `DP1` (`A6`) to `DP2` (`B6`) and `DN1` (`A7`) to `DN2` (`B7`) at the connector pads for reversible USB 2.0 orientation.
  - Place **two independent `5.1 kΩ ±1%` resistors (`C25905`)** from `CC1` (`A5`) to `GND` and from `CC2` (`B5`) to `GND` (never share a single resistor between `CC1` and `CC2`). Leave `SBU1` (`A8`) and `SBU2` (`B8`) unconnected (`NC`).
- **Schottky Diode (`D1` `B5819W`, `C8598`)**:
  - Placed in series from `VBUS` (Anode) to the regulated input node `+5V` / `VIN` (Cathode) to prevent back-feeding USB host ports when external 5 V or 3.3 V debugging supplies are connected.
- **LDO (`U2` `AP2112K-3.3TRG1`, `C51118`, SOT-23-5)**:
  - Pinout: Pin 1 = `VIN`, Pin 2 = `GND`, Pin 3 = `EN`, Pin 4 = `NC`, Pin 5 = `VOUT` (`+3V3`).
  - Tie `EN` (Pin 3) to `VIN` (Pin 1) (directly or via 10 kΩ pull-up).
  - Decouple `VIN` (Pin 1) with **`10 µF` (`C19702` / `C15525`) + `100 nF` (`C1525`)** to `GND`.
  - Decouple `VOUT` (Pin 5) with **`22 µF` (`C59461`) + `10 µF` (`C19702`) + `100 nF` (`C1525`)** low-ESR X5R/X7R ceramic capacitors to handle ESP32-S3 Wi-Fi TX peak bursts (~340–500 mA).

### 3.4 USB 2.0 ESD Protection (`U3` `USBLC6-2SC6`, `C7519`, SOT-23-6)
- Pinout: Pin 1 = `I/O1` (`USB_D-`), Pin 2 = `GND`, Pin 3 = `I/O2` (`USB_D+`), Pin 4 = `I/O2` (`ESP_USB_D+`), Pin 5 = `VBUS`, Pin 6 = `I/O1` (`ESP_USB_D-`).
- Route `USB_D-` and `USB_D+` from `J1` straight through Pins 1 & 3 and out Pins 6 & 4 (flow-through layout) to `ESP32-S3` Pins 25 & 26 (`GPIO19` & `GPIO20`), with Pin 5 connected to `VBUS` (plus a local 100 nF bypass cap to GND) and Pin 2 via'd directly to the GND plane.

### 3.5 2.4 GHz RF Front-End (`ANT1` `C293767` and/or `J2` `C88374`)
- Place a 3-element 0402 Pi-matching network between `LNA_IN` (Pin 1) and the antenna feed: series element (`R_RF` / `L_RF`: `2.7 nH` `C27123` or `0 Ω` `C17168`) and two shunt elements to GND (`C_RF1`, `C_RF2`: `1.5 pF` `C1552` / `2.2 pF` `C1559` C0G).
- If populating both the SMD chip antenna (`ANT3216LL00R2400A` `C293767`) and the u.FL connector (`U.FL-R-SMT-1(80)` `C88374`), use a shared series 0402 `0 Ω` selector resistor (`C17168`) angled toward either the chip antenna path or the u.FL path so no open stub remains on the active 2.4 GHz transmission line.
- Enforce a strict copper keep-out zone on **all PCB layers** beneath and around the `ANT3216LL00R2400A` chip antenna at the board corner/edge per the Yageo datasheet land pattern.
