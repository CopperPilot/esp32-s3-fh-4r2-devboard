---
required_inputs: [gerber zip, optional BOM + CPL (pick-and-place), order intent (qty, finish, color, PCBA type/side), project_dir]
artifact_outputs: [structured JSON per command, screenshots (DFM issues, placement), DFM/BOM review JSON reports, state.json + history.jsonl under .copperpilot/fab/jlcpcb]
---

# Skill: JLCPCB Order

## Objective
Order PCBs/PCBA from JLCPCB by driving the user's real Chrome: run `python .copperpilot/skills/jlcpcb-order/main.py <command>` (one JSON object out). Start with `preflight`, `status`, `quote-upload`, `dfm-run`, `bom-upload`, `placement-shots`, `save-to-cart`; read `.copperpilot/skills/jlcpcb-order/SKILL.md` before acting and REFERENCE.md for site quirks. Never pays; hands login/consent/payment to the user.

Operate **jlcpcb.com** the way a careful engineer would, in a real Chrome window:
upload Gerbers, read back what JLCPCB detected, run **JLCDFM** and drill into
every danger, configure PCB + PCBA options, upload **BOM + CPL**, review part
matching (LCSC #, Basic/Extended, stock, Standard-only parts), inspect
**component placement** (rotation / pin-1), read the itemised quote and
**SAVE TO CART**. Then iterate: fix the design or fab files, re-export,
re-upload, re-check, until clean.

## Hard rules
- **Never pay.** Stop at SAVE TO CART. Never click Secure Checkout, Pay, or
  Place Order. The skill blocks those controls (`status: blocked`), but don't try.
- **Humans own** login, captcha/OTP, terms-and-privacy consent dialogs, payment,
  and address/billing changes. Any result with `needs_human` means: stop, tell
  the user exactly what to do in the CopperPilot Chrome window, then retry
  (`wait-login` blocks until login completes).
- **Ask before money or scope changes:** switching Economic→Standard PCBA,
  "Do not place" decisions, dropping parts, build-time upgrades, or JLCPCB
  part-selection service ($). `decision_required` results list the options.
  Bring them to the user with the price impact.
- **Cart hygiene:** only the final iteration should stay in the cart. Remove
  earlier test items you added (`cart-remove --match <order no>`), never
  items you did not add (check `state.json` → `cart_adds`).
- Never edit `.copperpilot/fab/` files; the skill owns its state.

## Runtime
- `python .copperpilot/skills/jlcpcb-order/main.py <command> [args]` prints
  **one JSON object**. Common keys: `ok`, `status`
  (`ok|needs_human|decision_required|issues|partial|blocked|error`), `data`,
  `observations` (open modals, toasts, busy text), `warnings`, `needs_human`,
  `next_actions`, `artifacts` (screenshots/reports; open the images).
- Drives the user's **Google Chrome** (CopperPilot profile, CDP port 9333;
  auto-launched). If a quick action fails, retry it once before going manual.
- **Long actions** (uploads, DFM, processing) return `status: in_progress` + `job`
  after ~20 s (CopperPilot backgrounds shell commands after 25 s). Then run
  `main.py result --job <job> --wait-sec 20` until the status changes. Don't use `sleep`/`ps`,
  and don't start another browser command while a job is running.
- Relative paths resolve against `--project-dir` (default `.`).
- Each command is short-lived; Chrome keeps the state. Tabs the skill drives
  are tagged (quote, smt, cart), so re-running a command finds the same tab.

## Workflow (happy path)
1. **Build + preflight** (offline):
   `make build-pcb` (or the project's export), then
   `main.py preflight --gerber pcb/build/gerbers.zip --bom pcb/build/<x>-bom.csv --cpl pcb/build/<x>-cpl.csv`.
   Fix `errors` first: missing outline/drill, BOM↔CPL designator drift,
   qty mismatches.
2. `main.py status`: if `needs_human.reason == login`, ask the user to sign in,
   then `main.py wait-login`.
3. `main.py quote-upload --fresh --gerber pcb/build/gerbers.zip`.
   Check `detected` ("Detected 2 layer board of 100x100mm") against the design.
4. `main.py dfm-run`: returns `totals` and `problems` (per check:
   danger/warning/good). For each danger: `main.py dfm-details --check "<name>"`.
   Each item has a value, objects, `board_xy_mm`, a `kicad` block (KiCad
   coordinates, nearest via/pad with ref + pad number), and a marked
   **screenshot**. Read the images.
5. Configure from the project's order spec (ORDER_SPEC.md) or the user:
   `main.py quote-set --opt "PCB Qty=5" --opt "PCB Color=Red" --opt "Surface Finish=ENIG" --opt "PCB Assembly=on" --opt "PCBA Type=Standard" --opt "Assembly Side=Both Sides"`.
   Set **every** spec row (material/TG, panel, via covering, test...); `quote-read`
   lists all options. Labels/values: case-insensitive prefix of the site text.
   Price before/after is reported. Report any row you could not match exactly,
   and ask if matching it costs more.
6. `main.py quote-next` → `main.py smt-next` (PCB step) →
   `main.py bom-upload --bom ... --cpl ...`. Read `review.header`
   (parts detected/confirmed/not selected) and `review.problems`.
7. `main.py smt-next`. If `decision_required` comes back (e.g. "Project has
   unselected parts", "Standard PCBA Parts"), ask the user, then
   `main.py dialog --choose "<option>"`.
8. `main.py placement-shots` (3D, top), plus `--side bottom` if both sides are
   assembled. Verify every polarized part in the screenshots.
9. `main.py smt-next` → `main.py order-summary`. If
   `product_description_required`: `main.py product-description "DIY > Development Board"`
   (omit the value to list options). Pick the description that truly matches
   the product, because it drives customs.
10. `main.py save-to-cart` → `main.py cart-list`. Report total, breakdown,
    build time, and cart item order numbers. Tell the user payment is theirs.

## Iteration loop (what "good" looks like)
Treat every website response as review feedback. After each change, diff the
feedback against the previous round.
- **DFM dangers** (via-to-pad, silkscreen-to-pad/hole, annular ring,
  clearance): map `kicad.nearest_pads/vias` to the board. Decide fix vs accept.
  Fix in KiCad (move or tent the via, clip silkscreen, adjust clearance), then
  run DRC, `make build-pcb`, `quote-upload --fresh`, and `dfm-run --rerun`.
  `changes_vs_previous_run` shows what improved. Warnings are judgment calls;
  silkscreen-only issues are usually cosmetic (JLC clips silk). Say so.
- **BOM problems**: unmatched part, wrong LCSC #, out of stock / qty 0,
  "comment does not match", Standard-only parts. Fix the part fields
  (LCSC/MPN) in the schematic or BOM, re-export, then `bom-upload` again.
  Prefer Basic parts where electrically equivalent (Extended adds a feeder fee
  per unique part).
- **Placement**: wrong rotation or offset. Fix the CPL rotation (or the KiCad
  footprint origin/rotation export), re-upload, re-check the screenshots.
- Budget: up to 3 rounds per problem class without user input. Then summarise
  with screenshots and ask.

## Command reference
Site actions:
- `preflight --gerber Z --bom B --cpl C` · `doctor` · `status` · `wait-login`
- `quote-upload --gerber Z [--fresh]` · `quote-read` · `quote-set --opt 'Label=Value' ...` · `build-time '24 hours'`
  - special labels: `PCB Assembly=on|off`; checkbox rows take `on|off`;
    `Dimensions=100,100`.
- `dfm-run [--rerun]` · `dfm-summary` · `dfm-details --check NAME [--level danger --level warning] [--max-items N] [--pcb board.kicad_pcb]`
- `quote-next` · `smt-step --step pcb|bom|placement|quote` · `smt-next [--choose OPT]` · `dialog --choose OPT`
- `bom-upload --bom B --cpl C` · `bom-review [--all-rows]`
- `placement-shots [--view 3d|2d] [--side top|bottom] [--designators U1,J1] [--download-image]`
- `order-summary` · `product-description ["Category > Item"]` · `save-to-cart`
- `cart-list` · `cart-remove --match ORDER_NO [--dry-run]`

Generic browser tools for anything else: `snapshot` (refs like `e42`) → `click --ref e42` / `fill` / `hover`; plus `text`, `tables`, `observe`, `screenshot`, `wait`, `press`, `scroll`, `upload`, `reload`, `goto`, `tabs`, `eval`. Details in REFERENCE.md.

## More
Site quirks, timings, and DOM gotchas: `.copperpilot/skills/jlcpcb-order/REFERENCE.md`. `main.py <command> --help` documents every flag.
