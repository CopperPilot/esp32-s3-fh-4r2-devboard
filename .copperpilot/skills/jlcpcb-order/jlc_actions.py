#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""JLCPCB quick actions (cart.jlcpcb.com, jlcdfm.com)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict

import fab_browser as fb
import fab_preflight as fp
import jlc_cart as jc
import jlc_dfm as jd
import jlc_quote as jq
import jlc_smt as js
import kicad_locate as kl

SITE = "jlcpcb"
HOME_URL = "https://cart.jlcpcb.com/quote"
URL_MATCH = r"jlcpcb\.com|jlcdfm\.com"


def add_subcommands(sub: Any) -> None:
    p = sub.add_parser(
        "preflight",
        help="Offline check of Gerber zip / BOM / CPL before uploading (no browser)",
    )
    p.add_argument("--gerber")
    p.add_argument("--bom")
    p.add_argument("--cpl")
    sub.add_parser("doctor", help="Check runtime, Chrome/CDP and login state")
    sub.add_parser("status", help="Login state, current page and order step")
    p = sub.add_parser(
        "wait-login", help="Open sign-in and wait for the human to log in"
    )
    p.add_argument("--timeout-sec", type=float, default=600)

    p = sub.add_parser(
        "quote-upload",
        help="Open the quote page and upload a Gerber zip; returns detected board + options + price",
    )
    p.add_argument("--gerber", required=True)
    p.add_argument("--wait-sec", type=float, default=180)
    p.add_argument(
        "--fresh",
        action="store_true",
        help="Reload the quote page first (new quote)",
    )

    sub.add_parser(
        "quote-read",
        help="Read every PCB/PCBA option (selected/disabled), detected board and price panel",
    )

    p = sub.add_parser(
        "quote-set",
        help="Set quote options by label, e.g. --opt 'Surface Finish=ENIG' --opt 'PCB Qty=10'",
    )
    p.add_argument(
        "--opt",
        action="append",
        required=True,
        help="'Label=Value' (repeatable). Dimensions: 'Dimensions=100,100'",
    )

    p = sub.add_parser(
        "dfm-run",
        help="Gerber Viewer -> DFM Check -> run JLCDFM analysis; returns danger/warning counts per check",
    )
    p.add_argument("--timeout-sec", type=float, default=240)
    p.add_argument(
        "--rerun",
        action="store_true",
        help="Close any open DFM tab and analyse the latest upload",
    )

    sub.add_parser(
        "dfm-summary", help="Re-read DFM results from the open JLCDFM tab"
    )

    p = sub.add_parser(
        "dfm-details",
        help="Drill into one DFM check: per-layer items, values, board XY, zoomed screenshots",
    )
    p.add_argument(
        "--check",
        required=True,
        help="Check name from dfm-summary, e.g. 'Via to pad'",
    )
    p.add_argument(
        "--level",
        action="append",
        default=None,
        help="danger|warning|good (repeatable; default danger+warning)",
    )
    p.add_argument(
        "--max-items",
        type=int,
        default=6,
        help="Max items to screenshot/locate",
    )
    p.add_argument("--no-shots", action="store_true")
    p.add_argument(
        "--pcb",
        help="KiCad .kicad_pcb to map items to (default: auto-detect in project)",
    )

    p = sub.add_parser(
        "quote-next", help="Quote page NEXT (PCBA on) -> smt-order page"
    )

    p = sub.add_parser(
        "smt-step",
        help="Jump to an smt-order step: pcb | bom | placement | quote",
    )
    p.add_argument("--step", required=True)

    p = sub.add_parser(
        "smt-next",
        help="Click NEXT on the current smt-order step; dialogs come back as decision_required",
    )
    p.add_argument(
        "--choose",
        help="Answer the dialog that NEXT opens, e.g. 'Do not place' / 'Select parts'",
    )

    p = sub.add_parser(
        "dialog", help="Answer the currently open dialog on the smt-order page"
    )
    p.add_argument("--choose", required=True)

    p = sub.add_parser(
        "bom-upload",
        help="Upload BOM + CPL on the Bill of Materials step and process them; returns the parsed review",
    )
    p.add_argument("--bom", required=True)
    p.add_argument("--cpl", required=True)
    p.add_argument("--wait-sec", type=float, default=180)

    p = sub.add_parser(
        "bom-review",
        help="Parse the BOM review: per-line match (MPN, LCSC#, lib type, qty, cost, selected) and problems",
    )
    p.add_argument(
        "--all-rows",
        action="store_true",
        help="Include every row (default: only problems + header)",
    )

    p = sub.add_parser(
        "placement-shots",
        help="Component Placements: overview + zoomed shots per part to verify rotation/pin-1",
    )
    p.add_argument(
        "--designators",
        help="Comma list (default: polarized/multi-pin parts U,IC,D,LED,J,T,Q,SW,ESD...)",
    )
    p.add_argument("--view", default="3d", choices=["2d", "3d"])
    p.add_argument("--side", default="top", choices=["top", "bottom"])
    p.add_argument("--max-parts", type=int, default=12)
    p.add_argument(
        "--download-image",
        action="store_true",
        help="Also save JLCPCB's own full-resolution render",
    )

    sub.add_parser(
        "order-summary",
        help="Read the Quote & Order step (charges, total, build time, required fields)",
    )

    p = sub.add_parser(
        "product-description",
        help="Set the customs Product Description on Quote & Order",
    )
    p.add_argument(
        "value",
        nargs="?",
        help="'Category > Item' substrings, e.g. 'DIY > Development Board'. Omit to list all options.",
    )

    p = sub.add_parser(
        "save-to-cart",
        help="Click SAVE TO CART (quote page for PCB-only, Quote & Order for PCBA). Never pays.",
    )
    p.add_argument("--remark", help="Optional order remark")

    sub.add_parser(
        "cart-list",
        help="List cart items (name, order no., qty, build time, price)",
    )

    p = sub.add_parser(
        "cart-remove",
        help="Remove cart items whose text contains --match (order no. preferred)",
    )
    p.add_argument("--match", required=True)
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser(
        "build-time",
        help="Choose PCB build time radio (e.g. '2 days', '24 hours')",
    )
    p.add_argument("choice")


def handle_offline(args: Any, res: fb.Result, project_dir: Path) -> bool:
    if args.command == "preflight":

        def rel(p):
            if not p:
                return None
            q = Path(p).expanduser()
            return str(q if q.is_absolute() else project_dir / q)

        out = fp.preflight(
            SITE, rel(args.gerber), rel(args.bom), rel(args.cpl)
        )
        res.data.update(out)
        if out["errors"]:
            res.status = "issues"
            res.next_actions.append(
                "Fix the error-level issues (re-export from KiCad) before uploading."
            )
        return True
    return False


def login_state(page: Any) -> Dict[str, Any]:
    js = r"""
    () => {
      const t = document.body ? document.body.innerText : '';
      return {
        sign_in_visible: /\bSign in\b/i.test(t) && !/My Account/.test(t),
        my_account: /My Account/.test(t),
      };
    }
    """
    try:
        s = page.evaluate(js)
    except Exception:
        s = {}
    return {"logged_in": bool(s.get("my_account")), **s}


def needs_login(res: fb.Result) -> None:
    res.status = "needs_human"
    res.needs_human = {
        "reason": "login",
        "message": (
            "JLCPCB is not signed in. Ask the user to sign in (Google or email) in the CopperPilot "
            "Chrome window, then run `wait-login` or retry."
        ),
        "url": "https://passport.jlcpcb.com/login",
    }


def handle(
    args: Any, res: fb.Result, sess: fb.Session, project_dir: Path
) -> bool:
    cmd = args.command
    if cmd in ("doctor", "status"):
        # Login lives on jlcpcb.com pages (jlcdfm.com/passport tabs don't show "My Account").
        page = fb.find_role_page(
            sess,
            "quote",
            r"cart\.jlcpcb\.com/(quote|smt-order|shopcart)",
            open_url=HOME_URL,
        )
        st = login_state(page)
        res.url, res.title = page.url, page.title()
        res.data["login"] = st
        res.data["tabs"] = [
            t for t in fb.list_tabs(sess) if re.search(URL_MATCH, t["url"])
        ]
        res.data["state"] = fb.load_state(project_dir, SITE)
        if cmd == "doctor":
            res.data["cdp"] = fb.cdp_version(sess.port)
        if not st["logged_in"]:
            needs_login(res)
        res.observations = fb.observe(page)
        return True
    if cmd in ("quote-upload", "quote-read", "quote-set", "build-time"):
        page = fb.find_role_page(
            sess,
            "quote",
            r"cart\.jlcpcb\.com/quote(\?|$|#)",
            open_url=jq.QUOTE_URL,
        )
        if cmd == "quote-upload":
            if args.fresh or "/quote" not in page.url:
                for other in sess.pages():
                    if other is not page and re.search(
                        r"cart\.jlcpcb\.com/quote|gerberview|jlcdfm\.com",
                        other.url or "",
                    ):
                        other.close()
                page.goto(
                    jq.QUOTE_URL, wait_until="domcontentloaded", timeout=60000
                )
                fb.tag_page(page, "quote")
                fb.wait_idle(page, timeout_sec=30)
            res.data["upload"] = jq.upload_gerber(
                page, args.gerber, args.wait_sec
            )
            res.data.update(jq.summarize_quote(page))
            st = fb.load_state(project_dir, SITE)
            st.update(
                {
                    "gerber": res.data["upload"]["file"],
                    "quote_url": page.url,
                    "detected": res.data.get("detected"),
                }
            )
            fb.save_state(project_dir, SITE, st)
            if not res.data.get("detected"):
                res.warnings.append(
                    "Upload finished but no 'Detected … board' line appeared. Screenshot the page and check for an error modal."
                )
            res.next_actions = [
                "Compare `detected` with the design (layers, size).",
                "Run `gerber-viewer` / `dfm-run` to check how JLCPCB interpreted the files.",
                "Set options with `quote-set --opt 'Label=Value'` per the project's ORDER_SPEC.",
            ]
        elif cmd == "quote-read":
            res.data.update(jq.summarize_quote(page))
        elif cmd == "quote-set":
            applied, errors = [], []
            before = jq.read_panel(page).get("web_price")
            for spec in args.opt:
                if "=" not in spec:
                    errors.append(
                        {"opt": spec, "error": "expected Label=Value"}
                    )
                    continue
                label, value = [x.strip() for x in spec.split("=", 1)]
                try:
                    applied.append(jq.set_option(page, label, value))
                except fb.FabError as exc:
                    errors.append(
                        {"opt": spec, "error": str(exc), **exc.extra}
                    )
                gate = fb.settle_dialog(page)
                if gate and gate.get("acknowledged_dialog"):
                    applied[-1]["acknowledged_dialog"] = gate[
                        "acknowledged_dialog"
                    ]
                elif gate and gate.get("decision_required"):
                    res.status = "decision_required"
                    res.data["decision_required"] = {
                        **gate["decision_required"],
                        "after": spec,
                        "how": "Decide (ask the user if cost/scope changes), answer with `click --text '<option>'`, then re-run the remaining --opt values.",
                    }
                    res.data["not_applied_yet"] = args.opt[
                        args.opt.index(spec) + 1 :
                    ]
                    break
            summary = jq.summarize_quote(page)
            res.data["applied"] = applied
            if errors:
                res.data["errors"] = errors
                res.status = "partial" if applied else "error"
                res.ok = bool(applied)
            res.data["price_before"] = before
            res.data["price_after"] = summary["price"].get("web_price")
            res.data["options_now"] = {
                r["label"]: r.get("selected")
                for r in summary["pcb_options"] + summary["pcba_options"]
            }
            res.data["price"] = summary["price"]
        elif cmd == "build-time":
            res.data.update(jq.select_build_time(page, args.choice))
            res.data["price"] = jq.read_panel(page)
        res.url, res.title = page.url, page.title()
        res.observations = fb.observe(page)
        return True
    if cmd.startswith("dfm-"):
        if cmd == "dfm-run":
            if args.rerun:
                for pg in sess.pages():
                    if "jlcdfm.com" in pg.url or "gerberview" in pg.url:
                        pg.close()
            try:
                quote = fb.find_page(sess, r"cart\.jlcpcb\.com/quote(\?|$)")
            except fb.FabError:
                quote = None
            page = jd.run_dfm(sess, quote, args.timeout_sec)
            summ = jd.read_summary(page)
            prev_f = (
                fb.artifacts_dir(project_dir, SITE)
                / "dfm"
                / "latest-summary.json"
            )
            if prev_f.is_file():
                try:
                    res.data["changes_vs_previous_run"] = jd.diff_summaries(
                        json.loads(prev_f.read_text()), summ
                    )
                except Exception:
                    pass
            res.artifacts["dfm_summary"] = jd.save_report(
                project_dir, SITE, summ, page.url
            )
            res.artifacts["overview"] = fb.screenshot(
                page,
                fb.artifacts_dir(project_dir, SITE)
                / "shots"
                / f"{fb.stamp()}-dfm-overview.png",
            )
            res.data["totals"] = summ["totals"]
            res.data["problems"] = summ["problems"]
            if summ["totals"]["unanalyzed"] == summ["totals"]["checks"]:
                res.warnings.append(
                    "All checks still 'Unanalyzed' - the analysis did not run. Try `reload --url-match jlcdfm` then `dfm-run`."
                )
            res.next_actions = [
                "Statistics are (danger, warning, good). Danger items are likely to be rejected or fail; warnings are judgment calls.",
                "Drill in: `dfm-details --check '<name>'` gives values, board XY (Gerber origin) and zoomed screenshots.",
                "Fix real issues in KiCad, re-export (`make build-pcb`), `quote-upload --fresh`, then `dfm-run --rerun` and compare `changes_vs_previous_run`.",
            ]
        elif cmd == "dfm-summary":
            page = jd._dfm_page(sess)
            summ = jd.read_summary(page)
            res.data["totals"] = summ["totals"]
            res.data["problems"] = summ["problems"]
        elif cmd == "dfm-details":
            page = jd._dfm_page(sess)
            page.bring_to_front()
            fb.mark_active(page.url)
            levels = args.level or ["danger", "warning"]
            pcb = Path(args.pcb) if args.pcb else kl.find_pcb(project_dir)
            res.data.update(
                jd.details(
                    page,
                    args.check,
                    fb.artifacts_dir(project_dir, SITE) / "shots",
                    levels,
                    args.max_items,
                    not args.no_shots,
                    pcb,
                )
            )
            if pcb:
                res.data["kicad_pcb"] = str(pcb)
            res.next_actions = [
                "board_xy_mm is in Gerber coordinates (this project exports with a lower-left aux origin). Map to KiCad items and decide: fix, or accept with rationale.",
                "Read the zoomed screenshots before changing the layout.",
            ]
        res.url, res.title = page.url, page.title()
        return True
    if cmd == "quote-next":
        page = fb.find_role_page(
            sess, "quote", r"cart\.jlcpcb\.com/quote(\?|$|#)"
        )
        if not jq.pcba_enabled(page):
            raise fb.FabError(
                "PCB Assembly is off. Use `quote-set --opt 'PCB Assembly=on'` or `save-to-cart` for PCB only."
            )
        res.data.update(js.click_next(page))
        try:
            page.wait_for_url(re.compile(js.SMT_RX), timeout=30000)
        except Exception:
            pass
        fb.tag_page(page, "smt")
        st = fb.load_state(project_dir, SITE)
        st["smt_url"] = page.url
        fb.save_state(project_dir, SITE, st)
        res.url, res.title = page.url, page.title()
        res.next_actions = [
            "`smt-next` (PCB step) then `bom-upload --bom ... --cpl ...`."
        ]
        return True
    if cmd in (
        "placement-shots",
        "smt-step",
        "smt-next",
        "dialog",
        "bom-upload",
        "bom-review",
        "order-summary",
        "product-description",
        "save-to-cart",
    ):
        if cmd == "save-to-cart":
            try:
                page = js.smt_page(sess)
            except fb.FabError:
                page = fb.find_role_page(
                    sess, "quote", r"cart\.jlcpcb\.com/quote(\?|$|#)"
                )
        else:
            page = js.smt_page(sess)
        if cmd == "smt-step":
            res.data.update(
                js.goto_step(
                    page,
                    {
                        "bom": "Bill",
                        "placement": "Component",
                        "quote": "Quote",
                    }.get(args.step.lower(), args.step),
                )
            )
        elif cmd == "smt-next":
            res.data.update(js.click_next(page, choose=args.choose))
            if res.data.get("decision_required"):
                res.status = "decision_required"
        elif cmd == "dialog":
            res.data.update(js.choose_modal(page, args.choose))
        elif cmd == "bom-upload":
            res.data["upload"] = js.upload_bom_cpl(
                page, args.bom, args.cpl, args.wait_sec
            )
            rv = js.read_bom_review(page)
            res.data["review"] = {k: v for k, v in rv.items() if k != "rows"}
            st = fb.load_state(project_dir, SITE)
            st.update({"bom": args.bom, "cpl": args.cpl, "smt_url": page.url})
            fb.save_state(project_dir, SITE, st)
            rep = (
                fb.artifacts_dir(project_dir, SITE)
                / f"{fb.stamp()}-bom-review.json"
            )
            rep.write_text(json.dumps(rv, indent=2))
            res.artifacts["bom_review"] = str(rep)
            res.next_actions = [
                "Resolve every entry in review.problems: fix the MPN/LCSC# in the KiCad fields (or BOM), re-export, `bom-upload` again.",
                "Rows flagged 'Standard Only' need Standard PCBA (more expensive): ask the user before switching.",
                "When clean: `smt-next` to Component Placements and inspect rotations with `placement-shots`.",
            ]
        elif cmd == "bom-review":
            rv = js.read_bom_review(page)
            res.data.update(
                rv
                if args.all_rows
                else {k: v for k, v in rv.items() if k != "rows"}
            )
        elif cmd == "placement-shots":
            des = (
                [d.strip() for d in args.designators.split(",")]
                if args.designators
                else None
            )
            res.data.update(
                js.placement_shots(
                    page,
                    fb.artifacts_dir(project_dir, SITE) / "shots",
                    des,
                    args.view,
                    args.side,
                    args.max_parts,
                    args.download_image,
                )
            )
            res.next_actions = [
                "Open each screenshot. The pink dot marks the footprint pin 1; the part body/pin-1 marker must sit on it. Check polarity bands on diodes/LEDs and connector orientation.",
                "If a part is rotated/offset: fix the CPL rotation/offset (KiCad export or per-part correction), `bom-upload` again, re-check.",
            ]
        elif cmd == "order-summary":
            res.data.update(js.read_quote_order(page))
        elif cmd == "product-description":
            res.data.update(js.set_product_description(page, args.value))
            if args.value:
                res.data["order"] = js.read_quote_order(page)
        elif cmd == "save-to-cart":
            res.data.update(js.save_to_cart(page))
            st = fb.load_state(project_dir, SITE)
            st.setdefault("cart_adds", []).append(
                {"at": fb.stamp(), "from_url": page.url}
            )
            fb.save_state(project_dir, SITE, st)
            res.next_actions = [
                "`cart-list` to confirm the item; never proceed to checkout/payment - hand off to the user."
            ]
        res.url, res.title = page.url, page.title()
        if not res.observations:
            res.observations = fb.observe(page)
        return True
    if cmd in ("cart-list", "cart-remove"):
        page = jc.cart_page(sess)
        if cmd == "cart-list":
            res.data.update(jc.list_cart(page))
        else:
            res.data.update(jc.remove_items(page, args.match, args.dry_run))
            st = fb.load_state(project_dir, SITE)
            st.setdefault("cart_removed", []).append(
                {
                    "match": args.match,
                    "at": fb.stamp(),
                    "removed": res.data.get("removed"),
                }
            )
            fb.save_state(project_dir, SITE, st)
        res.url, res.title = page.url, page.title()
        res.next_actions = [
            "Payment/checkout is the user's step. Never click Secure Checkout."
        ]
        return True
    if cmd == "wait-login":
        page = fb.find_role_page(
            sess,
            "quote",
            r"cart\.jlcpcb\.com/(quote|smt-order|shopcart)",
            open_url=HOME_URL,
        )
        deadline = time.time() + args.timeout_sec
        while time.time() < deadline:
            st = login_state(page)
            if st["logged_in"]:
                res.data["login"] = st
                res.url = page.url
                return True
            time.sleep(2)
        needs_login(res)
        res.ok = False
        return True
    return False
