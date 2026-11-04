---
required_inputs: [gerber zip, optional Lion-format BOM (Item Number, Designator, Unit Quantity, Description, MPN, Footprint, Value, Assembly Instructions) + XY/CPL file, order intent (qty, finish, color, units, build time), project_dir]
artifact_outputs: [structured JSON per command, screenshots, procurement JSON, quote PDFs, state.json + history.jsonl under .copperpilot/fab/lioncircuits]
---

# Skill: Lion Circuits Order

## Objective
Order PCBs/PCBA from Lion Circuits (India) by driving the user's real Chrome: run `python .copperpilot/skills/lioncircuits-order/main.py <command>` (one JSON object out). Start with `preflight`, `status`, `projects`, `project-new`, `quote-set`, `bom-upload`, `xy-upload`, `procurement-read`, `add-to-cart`; read `.copperpilot/skills/lioncircuits-order/SKILL.md` before acting and REFERENCE.md for site quirks. Never pays; hands login/billing/payment to the user.

Operate **order.lioncircuits.com** (Bengaluru, India; prices in ₹ + 18% GST)
the way a careful engineer would, in a real Chrome window. Create a project
from Gerbers, configure **Fabrication**, upload the **BOM** (with field mapping)
and **XY** file for **Assembly**, read **Procurement** availability per MPN,
review the **Summary**, and **Add To Cart**. Iterate on the feedback (missing
MPNs, MOQ bumps, render mismatches, price constraints) until the order is clean.

## Hard rules
- **Never pay.** Stop at Add To Cart. "Pay Now" and the cart's "Proceed"
  (checkout) are blocked by the skill (`status: blocked`).
- **Humans own** login (email/password or Google), creating or switching
  **billing accounts**, addresses, GSTIN, coupons, and payment. On
  `needs_human`, tell the user exactly what to do in the CopperPilot Chrome
  window, then retry (`wait-login` blocks until login completes).
- **Ask before money or scope changes:** Flash build times (often ~10× fab
  price plus NRE), Premium shipping, "Procure By Me"/"Partial Procure", dropping
  parts, more units than asked. If an open question changes what gets bought
  (placeholder or DNP parts, which BOM variant), ask and stop **before** `add-to-cart`.
- Never edit `.copperpilot/fab/` files; the skill owns its state.
- **Cart hygiene:** keep only the final project in the cart. Remove earlier test
  projects you added (`cart-remove --project <name>`), never anything you
  did not add (see `state.json` → `cart_adds`, `projects_created`).

## Runtime
- `python .copperpilot/skills/lioncircuits-order/main.py <command> [args]`
  prints **one JSON object**: `ok`, `status`, `data`, `observations` (modals,
  toasts, busy text), `warnings`, `needs_human`, `next_actions`, `artifacts`.
- Drives the CopperPilot Chrome profile (CDP port 9333); keeps the window ≥1280 px
  wide (narrower switches Lion to a mobile layout).
- **Long actions** (project creation, BOM/XY upload, step changes) return `status: in_progress` + `job`
  after ~20 s (CopperPilot backgrounds shell commands after 25 s). Then run
  `main.py result --job <job> --wait-sec 20` until the status changes. Don't use `sleep`/`ps`,
  and don't start another browser command while a job is running.

## Workflow (happy path)
1. **Build + preflight**: `make build-pcb`, then
   `main.py preflight --gerber pcb/build/gerbers.zip --bom pcb/build/<x>-bom-lioncircuits.csv --cpl pcb/build/<x>-cpl-lioncircuits.csv`.
2. `main.py status`, then `main.py projects`. `selected_billing_id` must be set.
   If it is missing, the user must create or select a billing account (Lion
   refuses to process designs or quote without one).
3. `main.py project-new --name "<Project>-r1" --gerber pcb/build/gerbers.zip --layers 2`
   returns `pid` and the Fabrication quotation. Lion often shows a toast,
   "Problem while processing design files", and still creates the project. The
   skill recovers it from the project list and warns. Then check the board
   dimensions and `pcb-image` against the design.
4. Fabrication: `quote-read`, then
   `quote-set --opt "PCB Qty=10" --opt "PCB Finish=ENIG" --opt "Mask Color=Red" --opt "PCB Thickness=1.6 mm"`,
   then `build-time 5-6` (standard). Every set reports `now` and the charge panel.
   Constraints show up in `charges.constraints`, e.g. "Only ENIG PCB finish and
   max 2 oz copper thickness available for Flash option". `add-proceed`.
5. Assembly: `bom-upload --bom pcb/build/<x>-bom-lioncircuits.csv` (auto-maps
   all 8 fields, including Footprint/Value/Assembly Instructions, which Lion
   leaves unmapped; override with `--map 'Footprint=Package'`). Read
   `processing_dialog` ("We Found N Component…"). Then `units 10`, and
   `xy-upload --xy pcb/build/<x>-cpl-lioncircuits.csv --side top|bottom|combined`
   (use `combined` when the CPL has both Top and Bottom rows). Then
   `assembly-read` (check `xy_files[].uploaded`, `units`, and warnings),
   then `add-proceed`.
6. Procurement: `procurement-read` returns `not_available` (MPNs Lion cannot
   source), `moq_bumps` (order qty above required), prices, and the iteration
   tag. If parts are missing, iterate (below). Then `add-proceed`.
7. Summary: `summary-read` (fab/assembly/procurement lines, GST, total),
   `download-quote fab` / `download-quote assembly` (PDFs in artifacts), then
   `add-to-cart` and `cart-list`. Report total, breakdown, lead times, PID, cart
   contents, and that payment is the user's step.

## Iteration loop
- **Unavailable MPN** (`procurement-read.not_available`): look at the line in
  `bom-viewer`. Shortlist equivalents with the same footprint, pinout and ratings
  (check the datasheet), then `alternates-search MPN1 MPN2 ...` for Lion stock
  and price (prefer `exact_match`). Update the symbol's MPN field in KiCad (or the BOM generator),
  re-export, `goto-step assembly`, `bom-upload` again, re-run `units` and
  `xy-upload` if they reset, `add-proceed`, then `procurement-read`. The
  iteration tag advances (V1_L0 → V2_L1_reupload).
- **MOQ bumps** are normal for passives (Lion buys cut tape/reels). Report the
  cost, don't "fix" them.
- **Render / dimension mismatch** (`pcb-image`, board dimension on Fabrication):
  Lion's preview can be low-fidelity, but a wrong outline or size is a real
  issue. Confirm the Edge.Cuts export, then ask the user before ordering.
- **DFM:** Lion's DFM FEEDBACK tab only fills in **after payment** (engineers
  review the order). Before ordering, rely on local KiCad DRC against Lion's
  published limits (read the site's Capabilities page with `goto` + `text`, or the
  project's LIONCIRCUITS_ORDER_SPEC.md; do not guess numbers). Optionally run the JLCPCB skill's `dfm-run` on the same
  Gerbers as a free third-party check, and say that is what you did.
- Up to 3 rounds per problem class without user input. Then summarise and ask.

## Command reference
Site actions:
- `preflight --gerber Z --bom B --cpl C` · `doctor` · `status` · `wait-login`
- `projects` · `project-new --name N --gerber Z [--layers 2] [--description D]` · `project-open --pid P`
- `quote-read` · `quote-set --opt 'Label=Value' ...` · `build-time 5-6|4-5|2-3|1-2`
- `add-proceed` · `skip-step` · `goto-step fabrication|assembly|procurement|summary`
- `tab quotation|"project details"|"pcb image"|"bom viewer"|"dfm feedback"|"update design"`
- `bom-upload --bom B [--map 'Field=Column']` · `bom-map` (finish an open mapping dialog)
- `assembly-read` · `units N` · `xy-upload --xy F --side top|bottom|combined`
- `procurement-read` · `alternates-search TERM... [--qty N]` · `procurement-mode "Procure By LC"` · `bom-viewer [--all-rows]`
- `summary-read` · `shipping standard|premium` · `download-quote fab|assembly`
- `add-to-cart` · `cart-list` · `cart-remove --project NAME [--dry-run]` · `pcb-image`

Generic browser tools (anything else): `snapshot [--scope CSS] [--grep RX] [--interactive-only]`
gives refs (`e42`), then `click --ref e42` / `fill --ref e42 --value V` / `hover`.
Also: `text`, `tables`, `observe`, `screenshot`, `wait`, `press Escape`, `scroll`,
`upload`, `select`, `reload`, `goto`, `eval` (read-only unless `--allow-mutation`).

## More
Site quirks, timings, and DOM gotchas: `.copperpilot/skills/lioncircuits-order/REFERENCE.md`. `main.py <command> --help` documents every flag.
