# ESP32-S3FH4R2 Hardware Reference & Datasheet Verification

**Target Device:** Espressif `ESP32-S3FH4R2`
- **Package:** QFN-56 (7 × 7 mm), 0.4 mm pitch, **5.7 × 5.7 mm Exposed Pad (EPAD)** (Datasheet Figure 7-2; larger than the 4.0 × 4.0 mm EPAD of standard ESP32-S3 variants in Figure 7-1).
- **Integrated Memory:** 4 MB In-Package **Quad SPI** Flash (3.3 V) + 2 MB In-Package **Quad SPI** PSRAM (3.3 V).
- **Operating Temperature:** -40 °C to +85 °C ambient.
- **Authoritative Sources:** *ESP32-S3 Series Datasheet v2.2* and *ESP32-S3 Hardware Design Guidelines (Schematic Checklist & PCB Layout Design)*.

---

## 1. Complete 56-Pin + EPAD Pinout & In-Package Memory Allocation

### Summary of Internal Flash/PSRAM Pin Consumption on ESP32-S3FH4R2
- **Consumed Internally (7 GPIOs — DO NOT USE externally):**
  - **Pin 28 (`SPICS1` / `GPIO26`)**: Connected internally to 2 MB Quad SPI PSRAM `CE#`.
  - **Pin 30 (`SPIHD` / `GPIO27`)**: Connected internally to 4 MB Quad SPI Flash `HOLD#` and 2 MB Quad SPI PSRAM `SIO3`.
  - **Pin 31 (`SPIWP` / `GPIO28`)**: Connected internally to 4 MB Quad SPI Flash `WP#` and 2 MB Quad SPI PSRAM `SIO2`.
  - **Pin 32 (`SPICS0` / `GPIO29`)**: Connected internally to 4 MB Quad SPI Flash `CS#`.
  - **Pin 33 (`SPICLK` / `GPIO30`)**: Connected internally to 4 MB Quad SPI Flash `CLK` and 2 MB Quad SPI PSRAM `CLK`.
  - **Pin 34 (`SPIQ` / `GPIO31`)**: Connected internally to 4 MB Quad SPI Flash `DO` (`IO1`) and 2 MB Quad SPI PSRAM `SO/SIO1`.
  - **Pin 35 (`SPID` / `GPIO32`)**: Connected internally to 4 MB Quad SPI Flash `DI` (`IO0`) and 2 MB Quad SPI PSRAM `SI/SIO0`.
  - *(Note on Pin Numbering: Pin 29 is `VDD_SPI` power supply, located physically between Pin 28 `SPICS1/GPIO26` and Pin 30 `SPIHD/GPIO27`. Thus `GPIO26–GPIO32` occupy **Pins 28 and 30–35**).*
- **Free / Usable High-Numbered SPI/Octal Pins on ESP32-S3FH4R2:**
  - **Pins 38–42 (`GPIO33`, `GPIO34`, `GPIO35`, `GPIO36`, `GPIO37`)**: **FREE and fully usable as general-purpose GPIOs** (and `FSPI` / `SPI2` peripheral pins) on `ESP32-S3FH4R2`. These pins carry `SPIIO4–SPIIO7` (`DQ4–DQ7`) and `SPIDQS` (`DQS/DM`) only on 8-line Octal SPI variants (`ESP32-S3R8`, `ESP32-S3R8V`, `ESP32-S3R16V`). Because `ESP32-S3FH4R2` uses 4-line **Quad SPI** for both in-package Flash and PSRAM, `GPIO33–GPIO37` are not connected internally.
  - **Pins 36–37 (`SPICLK_N` / `GPIO48`, `SPICLK_P` / `GPIO47`)**: **FREE and fully usable as general-purpose GPIOs** (operating at 3.3 V on `ESP32-S3FH4R2`).
- **Total Usable GPIOs on ESP32-S3FH4R2:** **38 usable GPIOs** out of 45 total SoC GPIOs (`GPIO0–GPIO21` [22 pins] + `GPIO33–GPIO48` [16 pins]).

### Complete Pin Table (Pins 1 to 56 + Pin 57 EPAD)

| Pin No. | Pin Name | Type | Power Domain | Reset Default | Primary / Multiplexed Functions | Status on ESP32-S3FH4R2 |
|---:|---|---|---|---|---|---|
| 1 | `LNA_IN` | Analog | — | — | 2.4 GHz RF LNA input / PA output | Dedicated RF antenna matching pin |
| 2 | `VDD3P3` | Power | Analog | — | Analog/RF PA power supply (3.0–3.6 V) | Power input (via LC filter `L1`) |
| 3 | `VDD3P3` | Power | Analog | — | Analog/RF PA power supply (3.0–3.6 V) | Power input (via LC filter `L1`) |
| 4 | `CHIP_PU` | Analog (In) | `VDD3P3_RTC` | — | Chip Enable / Reset (`High` = Enable, `Low` = Reset) | Dedicated reset/enable (never float) |
| 5 | `GPIO0` | IO | `VDD3P3_RTC` | `WPU, IE` | `GPIO0`, `RTC_GPIO0`, `sar_i2c_scl_0` | **Usable GPIO** (Strapping pin: Boot mode) |
| 6 | `GPIO1` | IO | `VDD3P3_RTC` | `IE` | `GPIO1`, `RTC_GPIO1`, `TOUCH1`, `ADC1_CH0`, `sar_i2c_sda_0` | **Free GPIO** |
| 7 | `GPIO2` | IO | `VDD3P3_RTC` | `IE` | `GPIO2`, `RTC_GPIO2`, `TOUCH2`, `ADC1_CH1`, `sar_i2c_scl_1` | **Free GPIO** |
| 8 | `GPIO3` | IO | `VDD3P3_RTC` | `IE` (Float) | `GPIO3`, `RTC_GPIO3`, `TOUCH3`, `ADC1_CH2`, `sar_i2c_sda_1` | **Usable GPIO** (Strapping pin: JTAG source) |
| 9 | `GPIO4` | IO | `VDD3P3_RTC` | High-Z | `GPIO4`, `RTC_GPIO4`, `TOUCH4`, `ADC1_CH3` | **Free GPIO** |
| 10 | `GPIO5` | IO | `VDD3P3_RTC` | High-Z | `GPIO5`, `RTC_GPIO5`, `TOUCH5`, `ADC1_CH4` | **Free GPIO** |
| 11 | `GPIO6` | IO | `VDD3P3_RTC` | High-Z | `GPIO6`, `RTC_GPIO6`, `TOUCH6`, `ADC1_CH5` | **Free GPIO** |
| 12 | `GPIO7` | IO | `VDD3P3_RTC` | High-Z | `GPIO7`, `RTC_GPIO7`, `TOUCH7`, `ADC1_CH6` | **Free GPIO** |
| 13 | `GPIO8` | IO | `VDD3P3_RTC` | High-Z | `GPIO8`, `RTC_GPIO8`, `TOUCH8`, `ADC1_CH7`, `SUBSPICS1` | **Free GPIO** |
| 14 | `GPIO9` | IO | `VDD3P3_RTC` | `IE` (after rst) | `GPIO9`, `RTC_GPIO9`, `TOUCH9`, `ADC1_CH8`, `FSPIHD`, `SUBSPIHD` | **Free GPIO** |
| 15 | `GPIO10` | IO | `VDD3P3_RTC` | `IE` (after rst) | `GPIO10`, `RTC_GPIO10`, `TOUCH10`, `ADC1_CH9`, `FSPICS0`, `FSPIIO4` | **Free GPIO** |
| 16 | `GPIO11` | IO | `VDD3P3_RTC` | `IE` (after rst) | `GPIO11`, `RTC_GPIO11`, `TOUCH11`, `ADC2_CH0`, `FSPID`, `FSPIIO5` | **Free GPIO** |
| 17 | `GPIO12` | IO | `VDD3P3_RTC` | `IE` (after rst) | `GPIO12`, `RTC_GPIO12`, `TOUCH12`, `ADC2_CH1`, `FSPICLK`, `FSPIIO6` | **Free GPIO** |
| 18 | `GPIO13` | IO | `VDD3P3_RTC` | `IE` (after rst) | `GPIO13`, `RTC_GPIO13`, `TOUCH13`, `ADC2_CH2`, `FSPIQ`, `FSPIIO7` | **Free GPIO** |
| 19 | `GPIO14` | IO | `VDD3P3_RTC` | `IE` (after rst) | `GPIO14`, `RTC_GPIO14`, `TOUCH14`, `ADC2_CH3`, `FSPIWP`, `FSPIDQS` | **Free GPIO** |
| 20 | `VDD3P3_RTC` | Power | RTC / Digital | — | RTC & partial Digital power input; feeds `VDD_SPI` via $14\,\Omega$ switch | Power input (3.0–3.6 V) |
| 21 | `XTAL_32K_P` | IO | `VDD3P3_RTC` | High-Z | `GPIO15`, `RTC_GPIO15`, `XTAL_32K_P`, `ADC2_CH4`, `U0RTS` | **Free GPIO** (or 32.768 kHz XTAL P) |
| 22 | `XTAL_32K_N` | IO | `VDD3P3_RTC` | High-Z | `GPIO16`, `RTC_GPIO16`, `XTAL_32K_N`, `ADC2_CH5`, `U0CTS` | **Free GPIO** (or 32.768 kHz XTAL N) |
| 23 | `GPIO17` | IO | `VDD3P3_RTC` | `IE` (after rst) | `GPIO17`, `RTC_GPIO17`, `ADC2_CH6`, `U1TXD` | **Free GPIO** (10 mA default drive) |
| 24 | `GPIO18` | IO | `VDD3P3_RTC` | `IE` (after rst) | `GPIO18`, `RTC_GPIO18`, `ADC2_CH7`, `U1RXD`, `CLK_OUT3` | **Free GPIO** (10 mA default drive) |
| 25 | `GPIO19` | IO | `VDD3P3_RTC` | High-Z | `GPIO19`, `RTC_GPIO19`, `USB_D-`, `ADC2_CH8`, `U1RTS`, `CLK_OUT2` | **Usable GPIO / Native `USB_D-`** |
| 26 | `GPIO20` | IO | `VDD3P3_RTC` | `USB_PU` | `GPIO20`, `RTC_GPIO20`, `USB_D+`, `ADC2_CH9`, `U1CTS`, `CLK_OUT1` | **Usable GPIO / Native `USB_D+`** |
| 27 | `GPIO21` | IO | `VDD3P3_RTC` | High-Z | `GPIO21`, `RTC_GPIO21` | **Free GPIO** |
| 28 | `SPICS1` | IO | `VDD_SPI` | `WPU, IE` | `SPICS1`, `GPIO26` | **CONSUMED (In-Package PSRAM `CE#`)** |
| 29 | `VDD_SPI` | Power | `VDD_SPI` | 3.3 V Out | In-package Flash & PSRAM 3.3 V power rail | Decouple externally (`0.1 µF + 1 µF`) |
| 30 | `SPIHD` | IO | `VDD_SPI` | `WPU, IE` | `SPIHD`, `GPIO27` | **CONSUMED (Flash `HOLD#` / PSRAM `SIO3`)** |
| 31 | `SPIWP` | IO | `VDD_SPI` | `WPU, IE` | `SPIWP`, `GPIO28` | **CONSUMED (Flash `WP#` / PSRAM `SIO2`)** |
| 32 | `SPICS0` | IO | `VDD_SPI` | `WPU, IE` | `SPICS0`, `GPIO29` | **CONSUMED (In-Package Flash `CS#`)** |
| 33 | `SPICLK` | IO | `VDD_SPI` | `WPU, IE` | `SPICLK`, `GPIO30` | **CONSUMED (Flash `CLK` / PSRAM `CLK`)** |
| 34 | `SPIQ` | IO | `VDD_SPI` | `WPU, IE` | `SPIQ`, `GPIO31` | **CONSUMED (Flash `DO` / PSRAM `SO/SIO1`)** |
| 35 | `SPID` | IO | `VDD_SPI` | `WPU, IE` | `SPID`, `GPIO32` | **CONSUMED (Flash `DI` / PSRAM `SI/SIO0`)** |
| 36 | `SPICLK_N` | IO | `VDD_SPI`/`CPU` | `IE` | `GPIO48`, `SPICLK_N_DIFF`, `SUBSPICLK_N_DIFF` | **Free GPIO** (3.3 V on FH4R2) |
| 37 | `SPICLK_P` | IO | `VDD_SPI`/`CPU` | `IE` | `GPIO47`, `SPICLK_P_DIFF`, `SUBSPICLK_P_DIFF` | **Free GPIO** (3.3 V on FH4R2) |
| 38 | `GPIO33` | IO | `VDD_SPI`/`CPU` | `IE` (after rst) | `GPIO33`, `FSPIHD`, `SUBSPIHD`, `SPIIO4` | **Free GPIO** (Quad PSRAM frees `SPIIO4`) |
| 39 | `GPIO34` | IO | `VDD_SPI`/`CPU` | `IE` (after rst) | `GPIO34`, `FSPICS0`, `SUBSPICS0`, `SPIIO5` | **Free GPIO** (Quad PSRAM frees `SPIIO5`) |
| 40 | `GPIO35` | IO | `VDD_SPI`/`CPU` | `IE` (after rst) | `GPIO35`, `FSPID`, `SUBSPID`, `SPIIO6` | **Free GPIO** (Quad PSRAM frees `SPIIO6`) |
| 41 | `GPIO36` | IO | `VDD_SPI`/`CPU` | `IE` (after rst) | `GPIO36`, `FSPICLK`, `SUBSPICLK`, `SPIIO7` | **Free GPIO** (Quad PSRAM frees `SPIIO7`) |
| 42 | `GPIO37` | IO | `VDD_SPI`/`CPU` | `IE` (after rst) | `GPIO37`, `FSPIQ`, `SUBSPIQ`, `SPIDQS` | **Free GPIO** (Quad PSRAM frees `SPIDQS`) |
| 43 | `GPIO38` | IO | `VDD3P3_CPU` | `IE` (after rst) | `GPIO38`, `FSPIWP`, `SUBSPIWP` | **Free GPIO** |
| 44 | `MTCK` | IO | `VDD3P3_CPU` | `IE, WPU` | `GPIO39`, `MTCK` (JTAG TCK), `CLK_OUT3`, `SUBSPICS1` | **Usable GPIO** (or pad JTAG `TCK`) |
| 45 | `MTDO` | IO | `VDD3P3_CPU` | `IE` (after rst) | `GPIO40`, `MTDO` (JTAG TDO), `CLK_OUT2` | **Usable GPIO** (or pad JTAG `TDO`) |
| 46 | `VDD3P3_CPU` | Power | `VDD3P3_CPU` | — | Digital CPU & Digital IO power supply (3.0–3.6 V) | Power input |
| 47 | `MTDI` | IO | `VDD3P3_CPU` | `IE` (after rst) | `GPIO41`, `MTDI` (JTAG TDI), `CLK_OUT1` | **Usable GPIO** (or pad JTAG `TDI`) |
| 48 | `MTMS` | IO | `VDD3P3_CPU` | `IE` (after rst) | `GPIO42`, `MTMS` (JTAG TMS) | **Usable GPIO** (or pad JTAG `TMS`) |
| 49 | `U0TXD` | IO | `VDD3P3_CPU` | `WPU, IE` | `GPIO43`, `U0TXD` (UART0 TX), `CLK_OUT1` | **Usable GPIO / Default `U0TXD`** |
| 50 | `U0RXD` | IO | `VDD3P3_CPU` | `WPU, IE` | `GPIO44`, `U0RXD` (UART0 RX), `CLK_OUT2` | **Usable GPIO / Default `U0RXD`** |
| 51 | `GPIO45` | IO | `VDD3P3_CPU` | `WPD, IE` | `GPIO45` | **Usable GPIO** (Strapping: `VDD_SPI` 3.3 V/1.8 V) |
| 52 | `GPIO46` | IO | `VDD3P3_CPU` | `WPD, IE` | `GPIO46` | **Usable GPIO** (Strapping: Boot mode / log) |
| 53 | `XTAL_N` | Analog | — | — | External 40 MHz crystal oscillator output (`XOUT`) | Dedicated 40 MHz crystal pin |
| 54 | `XTAL_P` | Analog | — | — | External 40 MHz crystal oscillator input (`XIN`) | Dedicated 40 MHz crystal pin |
| 55 | `VDDA` | Power | Analog | — | Analog / PLL / Crystal power supply (3.0–3.6 V) | Power input |
| 56 | `VDDA` | Power | Analog | — | Analog / PLL / Crystal power supply (3.0–3.6 V) | Power input |
| 57 | `GND` (EPAD) | Power | Ground | — | Exposed thermal & ground pad (**5.7 × 5.7 mm** on FH4R2) | Connect to GND plane ($\ge 9$ vias) |

---

## 2. Power Pins & Recommended Decoupling Capacitors Per Pin

From the *ESP32-S3 Reference Schematic* (`esp32s3-sche-core.png`), *Section 2.5 Power Supply*, and *ESP32-S3 Hardware Design Guidelines*:

| Pin Number(s) | Pin Name | Voltage Range | Ref Schematic Designators | Recommended Decoupling / Filtering Per Pin | Notes |
|---|---|---|---|---|---|
| Main Rail Entry | `VDD33` | 3.0–3.6 V (3.3 V typ, $\ge 500\text{ mA}$) | `D1`, `C21` | `10 µF` (`C21`) + ESD diode (`D1`) at rail entrance | Can be shared with `C6` if entrance is adjacent to Pins 2 & 3 |
| **Pins 2, 3** | `VDD3P3` | 3.0–3.6 V | `C6`, `C7`, `C8`, `L1`, `C9` | Upstream of `L1`: `10 µF` (`C6`) + `1 µF` (`C7`) + `0.1 µF` (`C8`); Series Inductor `L1 = 2.0 nH` ($\pm 0.1\text{ nH}$, $\ge 500\text{ mA}$); Downstream at Pins 2 & 3: `0.1 µF` (`C9`, 0201) | Analog/RF PA supply; high transient current during Wi-Fi TX |
| **Pin 20** | `VDD3P3_RTC` | 3.0–3.6 V | `C15` | `0.1 µF` (`C15`) placed directly at Pin 20 | Also feeds `VDD_SPI` via internal $R_{\text{SPI}} \approx 14\,\Omega$; keep `VDD3P3_RTC` $> 3.0\text{ V}$ |
| **Pin 29** | `VDD_SPI` | 3.3 V Output (on FH4R2) | `C13`, `C14` | `0.1 µF` (`C13`) + `1 µF` (`C14`) placed directly at Pin 29 to GND | Powers in-package 4 MB Flash & 2 MB PSRAM; do NOT add excessive bulk C |
| **Pin 46** | `VDD3P3_CPU` | 3.0–3.6 V | `C10` | `0.1 µF` (`C10`) placed directly at Pin 46 | Digital CPU & Digital IO rail ($\le 3.3\text{ V}$ if burning eFuses) |
| **Pins 55, 56** | `VDDA` | 3.0–3.6 V | `C3`, `C2` | `1 µF` (`C3`) + `10 nF` (`C2`, $0.01\,\mu\text{F}$) placed directly near Pins 55 & 56 | Analog / crystal / PLL supply |
| **Pin 57 (EPAD)** | `GND` | 0 V | — | Solid connection to ground plane via $\ge 9$ ground vias | **5.7 × 5.7 mm** nominal EPAD on `ESP32-S3FH4R2` |

---

## 3. Clock, RF Matching, CHIP_PU Reset, and Strapping Pins on ESP32-S3FH4R2

### 3.1 40 MHz Crystal & CLC Values (Pins 53 `XTAL_N`, 54 `XTAL_P`)
- **Crystal (`Y1`)**: 40 MHz fundamental SMD crystal, frequency tolerance **$\pm 10\text{ ppm}$**, amplitude $> 500\text{ mV}$.
- **Series Harmonic Filter (`L4` on `XTAL_P`, Pin 54)**: Place series component `L4` close to Pin 54 (`XTAL_P`) between the chip and crystal pin `XIN` (before load capacitor `C1`). Espressif recommends an initial value of **`24 nH` inductor** to attenuate crystal harmonics affecting RF performance.
- **Load Capacitors (`C1` at `XIN` to GND, `C4` at `XOUT`/Pin 53 to GND)**:
  $$C_L = \frac{C_1 \times C_4}{C_1 + C_4} + C_{\text{stray}}$$
  With typical PCB stray capacitance $C_{\text{stray}} \approx 2\text{--}3\text{ pF}$ and $C_1 = C_4$:
  - For $C_L = 8\text{ pF}$ crystal: **$C_1 = C_4 = 10\text{--}12\text{ pF}$**
  - For $C_L = 10\text{ pF}$ crystal: **$C_1 = C_4 = 14\text{--}16\text{ pF}$**
  - For $C_L = 12\text{ pF}$ crystal: **$C_1 = C_4 = 18\text{--}20\text{ pF}$**
- **Layout Rules**: Place crystal $\ge 2.0\text{ mm}$ from the chip clock pins, no vias on `XTAL_P`/`XTAL_N` traces, no high-frequency digital traces underneath, surrounded by stitched ground vias.

### 3.2 RF Matching Pi-Network (CLC) Values (Pin 1 `LNA_IN`)
- **Topology**: Shunt capacitor `C12` (chip side, closest to Pin 1) $\rightarrow$ Series inductor `L2` $\rightarrow$ Shunt capacitor `C11` (antenna side) on a **$50\,\Omega$ single-ended** microstrip trace.
- **Recommended Component Value Ranges (0201 packages required, placed in zigzag orientation)**:
  - **`C12` (chip-side shunt capacitor)**: **1.2 ~ 1.8 pF** (typical starting value **1.5 pF**, e.g., Murata `GRM0335C1H1RXBA01D`). Include a **15 mil length, $100\,\Omega \pm 10\%$ ground stub** on `C12`'s ground pad (with Layer 2 ground cleared under the stub, referenced to Layer 3) to suppress 4.8 GHz 2nd harmonics.
  - **`L2` (series inductor)**: **2.0 ~ 3.0 nH** (typical starting value **2.4 nH – 2.7 nH**, e.g., Murata `LQP03TN2NXB02D`).
  - **`C11` (antenna-side shunt capacitor)**: **1.2 ~ 1.8 pF** (typical starting value **1.5 pF**, e.g., Murata `GRM0335C1H1RXBA01D`).
- **Impedance Target**: Chip conjugate match point is **$35 + j0\,\Omega$** ($S_{21} < -35\text{ dB}$ at 4.8 GHz and 7.2 GHz). Reserve an additional CLC pi-network (`C23`, `L5`, `C22`) near PCB antennas if antenna tuning is required.

### 3.3 `CHIP_PU` (`EN`, Pin 4) Power-On-Reset RC Circuit
- **Values**: Pull-up resistor **$R = 10\text{ k}\Omega$** to `VDD33` (3.3 V) and delay capacitor **$C = 1\,\mu\text{F}$** to `GND`.
- **Timing Requirements**:
  - $t_{\text{STBL}} \ge 50\,\mu\text{s}$: Time `CHIP_PU` must remain below $V_{\text{IL\_nRST}}$ ($\le 0.25 \times \text{VDD3P3\_RTC} \approx 0.825\text{ V}$) after the 3.3 V rails stabilize ($\ge 2.8\text{ V}$).
  - $t_{\text{RST}} \ge 50\,\mu\text{s}$: Minimum low pulse width on `CHIP_PU` to guarantee a clean hardware reset.
  - High-level release threshold: $V_{\text{IH\_nRST}} \ge 0.75 \times \text{VDD3P3\_RTC}$ ($\approx 2.48\text{ V}$).
  - Never leave `CHIP_PU` floating.

### 3.4 Strapping Pins Behavior on `ESP32-S3FH4R2` (`GPIO0`, `GPIO3`, `GPIO45`, `GPIO46`)
Strapping pins are latched at reset release (`CHIP_PU` rising edge) with minimum setup time **$t_{\text{SU}} \ge 0\text{ ms}$** and minimum hold time **$t_{\text{H}} \ge 3\text{ ms}$**. After $t_{\text{H}}$, they operate as normal GPIOs.

| Strapping Pin | Pin No. | Internal Reset Pull | Default Bit | Function & Specific Behavior on `ESP32-S3FH4R2` |
|---|---:|---|---:|---|
| **`GPIO0`** | Pin 5 | Weak Pull-Up (`WPU`, $\approx 45\text{ k}\Omega$) | `1` | **Boot Mode Control** (with `GPIO46`). `1` = SPI Boot (from 4 MB in-package Quad Flash); `0` (with `GPIO46 = 0`) = Joint Download Boot (USB-Serial-JTAG / USB-OTG / UART0). External $10\text{ k}\Omega$ pull-up recommended; avoid large capacitance on `GPIO0`. |
| **`GPIO3`** | Pin 8 | **Floating** (No internal pull) | Undefined | **JTAG Signal Source Control**. Ignored by default (`EFUSE_STRAP_JTAG_SEL = 0`), where JTAG defaults to the internal USB Serial/JTAG controller (`GPIO19`/`GPIO20`). Only sampled at reset if `EFUSE_STRAP_JTAG_SEL = 1` is burned (`1` = USB Serial/JTAG, `0` = Pad JTAG on `GPIO39–42`). |
| **`GPIO45`** | Pin 51 | Weak Pull-Down (`WPD`, $\approx 45\text{ k}\Omega$) | `0` | **`VDD_SPI` Voltage Selection**. When `EFUSE_VDD_SPI_FORCE = 0`: `0` = `VDD_SPI` at **3.3 V** (via $14\,\Omega$ switch from `VDD3P3_RTC`); `1` = `VDD_SPI` at **1.8 V** (internal LDO). **CRITICAL on `ESP32-S3FH4R2`**: In-package 4 MB Flash and 2 MB PSRAM are **3.3 V devices**. `GPIO45` **MUST be `0` at reset** (do NOT pull high externally) unless `EFUSE_VDD_SPI_FORCE=1` and `EFUSE_VDD_SPI_TIEH=1` are burned. |
| **`GPIO46`** | Pin 52 | Weak Pull-Down (`WPD`, $\approx 45\text{ k}\Omega$) | `0` | **Boot Mode Control** (with `GPIO0`) & **ROM Print Control**. Must be `0` when `GPIO0 = 0` to enter Joint Download Boot (`GPIO0 = 0, GPIO46 = 1` is invalid and blocks download mode). **Do NOT pull `GPIO46` high at reset.** |
