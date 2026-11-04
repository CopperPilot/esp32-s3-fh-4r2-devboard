# lioncircuits-order: site reference

## Site knowledge (gotchas)
- Wizard: Fabrication → Assembly → Procurement → Summary. "Add & Proceed" saves the
  step. "Skip <step>" exists for fab-only or assembly-only orders.
- **Units reset to 1** when you navigate back to Assembly. Re-check
  `assembly-read` before proceeding.
- The page has one BOM `<input type=file>`. XY files go through the Top / Bottom /
  Combined tiles, which open an "Upload XY File" dialog. Never put a CPL into the
  BOM input (it replaces the BOM).
- BOM mapping fields: Item Number*, Designator*, Unit Quantity*, Description*,
  Manufacturer Part Number, Footprint, Value, Assembly Instructions.
- Build time values: none = 5-6 days, rush = 4-5, super_rush = 2-3 (flash), flash = 1-2
  (flash). Flash restricts finish and copper and adds NRE.
- Busy overlays: "Uploading Gerber…", "Getting Quotation…", "Uploading BOM…",
  "Fetching data…", "Downloading Quotation…". The skill waits for them.
- Prices are INR, and GST (18%) is added at Summary. Shipping is Standard (2-3 working
  days, free) or Premium (1-2).
