#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""Lion Circuits quick actions (order.lioncircuits.com)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict

import fab_browser as fb
import fab_preflight as fp
import lion_assembly as la_
import lion_project as lp
import lion_quote as lq

SITE = "lioncircuits"
HOME_URL = "https://order.lioncircuits.com/viewProjects"
URL_MATCH = r"lioncircuits\.com"


def add_subcommands(sub: Any) -> None:
    p = sub.add_parser(
        "preflight",
        help="Offline check of Gerber zip / BOM / CPL before uploading (no browser)",
    )
    p.add_argument("--gerber")
    p.add_argument("--bom")
    p.add_argument("--cpl")
    sub.add_parser("doctor", help="Check runtime, Chrome/CDP and login state")
    sub.add_parser("status", help="Login state, current page, project, step")
    sub.add_parser(
        "projects",
        help="List projects (name, PID, fab/assembly status) and the selected billing ID",
    )

    p = sub.add_parser(
        "project-new",
        help="New Project: name + layers + Gerber zip -> PID and quotation page",
    )
    p.add_argument("--name", required=True)
    p.add_argument("--gerber", required=True)
    p.add_argument("--layers", type=int)
    p.add_argument("--description")
    p.add_argument("--wait-sec", type=float, default=180)

    p = sub.add_parser(
        "project-open",
        help="Open a project's quotation by PID (default: last PID in state)",
    )
    p.add_argument("--pid")

    sub.add_parser(
        "quote-read",
        help="Current step, every option (selected/disabled) and the Charge Details panel",
    )

    p = sub.add_parser(
        "quote-set",
        help="Set options on the current step: --opt 'PCB Finish=ENIG' --opt 'PCB Qty=10'",
    )
    p.add_argument("--opt", action="append", required=True)

    p = sub.add_parser(
        "build-time",
        help="Build time: '5-6' (standard) | '4-5' | '2-3' | '1-2' (flash)",
    )
    p.add_argument("choice")

    p = sub.add_parser(
        "add-proceed",
        help="Click 'Add & Proceed' to save this step and go to the next",
    )
    p.add_argument("--wait-sec", type=float, default=120)

    p = sub.add_parser(
        "skip-step", help="Click 'Skip <step>' (e.g. skip Procurement)"
    )

    p = sub.add_parser(
        "goto-step",
        help="Jump to a wizard step: fabrication|assembly|procurement|summary",
    )
    p.add_argument("step")

    p = sub.add_parser(
        "tab",
        help="Open a project tab: quotation | project details | pcb image | bom viewer | dfm feedback | update design",
    )
    p.add_argument("name")

    p = sub.add_parser(
        "bom-upload",
        help="Assembly step / BOM viewer: upload BOM, auto-map fields (Footprint/Value/Assembly Instructions too), process",
    )
    p.add_argument("--bom", required=True)
    p.add_argument(
        "--map",
        action="append",
        default=[],
        help="Override: 'Footprint=Package' (Lion field = column in your file)",
    )

    p = sub.add_parser(
        "bom-map", help="Complete an already-open 'Map your BOM fields' dialog"
    )
    p.add_argument("--map", action="append", default=[])

    sub.add_parser(
        "assembly-read",
        help="Assembly step: units, assembly type, XY status, stencil, solder, price",
    )

    p = sub.add_parser(
        "units",
        help="Set assembly Units (it resets to 1 after navigation - always re-check)",
    )
    p.add_argument("n", type=int)

    p = sub.add_parser(
        "xy-upload",
        help="Upload the pick-and-place (XY/CPL) file for top|bottom|combined",
    )
    p.add_argument("--xy", required=True)
    p.add_argument(
        "--side", default="top", choices=["top", "bottom", "combined"]
    )

    sub.add_parser(
        "procurement-read",
        help="Procurement step: per-MPN availability, order qty (MOQ bumps), prices, missing parts",
    )

    p = sub.add_parser(
        "alternates-search",
        help="Search Lion's component catalog (stock, price) for candidate MPNs or keywords",
    )
    p.add_argument(
        "terms",
        nargs="+",
        help="MPNs or keywords, one search each (e.g. B5819WS 1N5819WS)",
    )
    p.add_argument(
        "--qty",
        type=int,
        help="Required quantity for pricing (default: the BOM row's)",
    )

    p = sub.add_parser(
        "procurement-mode",
        help="Procure By LC | Procure By Me | Partial Procure",
    )
    p.add_argument("mode")

    p = sub.add_parser(
        "bom-viewer",
        help="BOM VIEWER tab: version, columns, rows (MPN availability icons)",
    )
    p.add_argument("--all-rows", action="store_true")

    sub.add_parser(
        "summary-read",
        help="Summary step: shipping options, charge breakdown, total",
    )

    p = sub.add_parser("shipping", help="Summary: Standard | Premium")
    p.add_argument("method")

    p = sub.add_parser(
        "download-quote",
        help="Summary: download the Fab or Assembly quote PDF",
    )
    p.add_argument("which", choices=["fab", "assembly"])

    sub.add_parser("add-to-cart", help="Summary: Add To Cart (never Pay Now)")

    sub.add_parser(
        "pcb-image",
        help="PCB IMAGE tab: screenshots of Lion's top/bottom render (sanity-check the Gerber parse)",
    )

    sub.add_parser(
        "cart-list",
        help="List Lion cart projects (fab/assembly/procurement lines, units, price)",
    )

    p = sub.add_parser(
        "cart-remove",
        help="Remove a project from the cart by exact project name (only ones you added)",
    )
    p.add_argument("--project", required=True)
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser(
        "wait-login",
        help="Open the login page and wait for the human to log in",
    )
    p.add_argument("--timeout-sec", type=float, default=600)


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
    url = page.url
    js = r"""
    () => {
      const t = document.body ? document.body.innerText : '';
      return {
        has_login_form: !!document.querySelector('input[type=password]'),
        has_logout: /\bLogout\b/.test(t),
        has_my_projects: /My Projects/.test(t),
      };
    }
    """
    try:
        s = page.evaluate(js)
    except Exception:
        s = {}
    logged_in = bool(
        s.get("has_logout")
        or (s.get("has_my_projects") and not s.get("has_login_form"))
    )
    if "/login" in url:
        logged_in = False
    return {"logged_in": logged_in, **s}


def needs_login(res: fb.Result) -> None:
    res.status = "needs_human"
    res.needs_human = {
        "reason": "login",
        "message": (
            "Lion Circuits is not logged in. Ask the user to log in in the CopperPilot Chrome window "
            "(email/password or Google), then run `wait-login` or retry."
        ),
        "url": "https://order.lioncircuits.com/login/",
    }


def handle(
    args: Any, res: fb.Result, sess: fb.Session, project_dir: Path
) -> bool:
    cmd = args.command
    if cmd in ("doctor", "status"):
        page = fb.find_page(sess, URL_MATCH, open_url=HOME_URL)
        st = login_state(page)
        res.url, res.title = page.url, page.title()
        res.data["login"] = st
        res.data["state"] = fb.load_state(project_dir, SITE)
        if cmd == "doctor":
            res.data["cdp"] = fb.cdp_version(sess.port)
            res.data["python"] = __import__("sys").version
        if not st["logged_in"]:
            needs_login(res)
        res.observations = fb.observe(page)
        return True
    if cmd in (
        "project-open",
        "quote-read",
        "quote-set",
        "build-time",
        "add-proceed",
        "skip-step",
        "goto-step",
        "tab",
    ):
        page = fb.find_role_page(
            sess, "lion", URL_MATCH, open_url=lp.PROJECTS_URL
        )
        st = fb.load_state(project_dir, SITE)
        if cmd == "project-open":
            pid = args.pid or st.get("pid")
            if not pid:
                raise fb.FabError(
                    "No PID given and none in state. Run `projects` or `project-new`."
                )
            page.goto(
                f"{lq.BASE}/projectdetails/{pid}/quotation",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            fb.wait_idle(page, timeout_sec=60, settle_sec=2.0)
            st["pid"] = str(pid)
            fb.save_state(project_dir, SITE, st)
            res.data.update(lq.summarize(page))
        elif cmd == "quote-read":
            note = lq.ensure_project_page(page, st.get("pid"))
            if note:
                res.warnings.append(note)
            res.data.update(lq.summarize(page))
        elif cmd == "quote-set":
            applied, errors = [], []
            before = lq.read_panel(page).get("items")
            for spec in args.opt:
                if "=" not in spec:
                    errors.append(
                        {"opt": spec, "error": "expected Label=Value"}
                    )
                    continue
                k, v = [x.strip() for x in spec.split("=", 1)]
                if k.lower().startswith("pcb qty"):
                    st["pcb_qty"] = v
                    fb.save_state(project_dir, SITE, st)
                note = lq.ensure_project_page(page, st.get("pid"))
                if note:
                    res.warnings.append(note)
                try:
                    applied.append(lq.set_option(page, k, v))
                except fb.FabError as exc:
                    if (
                        not str(exc).startswith("No option")
                        or lq.current_step(page) != "Fabrication"
                    ):
                        errors.append(
                            {"opt": spec, "error": str(exc), **exc.extra}
                        )
                        continue
                    page.reload(wait_until="domcontentloaded", timeout=60000)
                    lq.ensure_project_page(page, st.get("pid"))
                    try:
                        applied.append(lq.set_option(page, k, v))
                        res.warnings.append(
                            f"'{k}' was not rendered yet; reloaded and applied it."
                        )
                    except fb.FabError as exc2:
                        errors.append(
                            {"opt": spec, "error": str(exc2), **exc2.extra}
                        )
            res.data["applied"] = applied
            if errors:
                res.data["errors"] = errors
                res.status = "partial" if applied else "error"
                res.ok = bool(applied)
            res.data["charges_before"] = before
            res.data["charges"] = lq.read_panel(page)
        elif cmd == "build-time":
            res.data.update(lq.set_build_time(page, args.choice))
        elif cmd == "add-proceed":
            step = lq.current_step(page)
            res.data["from_step"] = step
            res.data.update(
                lq.click_action(
                    page, r"^\s*Add\s*&\s*Proceed\s*$", args.wait_sec
                )
            )
            res.data["to_step"] = lq.current_step(page)
            if res.data["to_step"] == step:
                res.warnings.append(
                    "Still on the same step: a required input may be missing (see toasts/observations), or the site is slow. `quote-read` to check."
                )
        elif cmd == "skip-step":
            res.data.update(lq.click_action(page, r"^\s*Skip\s+\w+\s*$"))
            res.data["to_step"] = lq.current_step(page)
        elif cmd == "goto-step":
            hit = next(
                (
                    x
                    for x in lq.STEPS
                    if x.lower().startswith(args.step.lower())
                ),
                None,
            )
            if not hit:
                raise fb.FabError("Unknown step.", steps=lq.STEPS)
            page.locator(
                "[class*=Quotationbar_step]", has_text=hit
            ).first.click(timeout=10000)
            fb.wait_idle(page, timeout_sec=60, settle_sec=1.5)
            res.data.update(lq.summarize(page))
        elif cmd == "tab":
            res.data.update(lq.open_tab(page, args.name))
        res.url, res.title = page.url, page.title()
        res.observations = fb.observe(page)
        return True
    if cmd in (
        "bom-upload",
        "bom-map",
        "assembly-read",
        "units",
        "xy-upload",
        "procurement-read",
        "procurement-mode",
        "alternates-search",
        "bom-viewer",
        "summary-read",
        "shipping",
        "download-quote",
        "add-to-cart",
        "cart-list",
        "cart-remove",
        "pcb-image",
    ):
        page = fb.find_role_page(
            sess, "lion", URL_MATCH, open_url=lp.PROJECTS_URL
        )
        shots = fb.artifacts_dir(project_dir, SITE)
        maps = {}
        for m in getattr(args, "map", []) or []:
            if "=" in m:
                k, v = m.split("=", 1)
                maps[k.strip()] = v.strip()
        if cmd == "bom-upload":
            res.data.update(la_.upload_bom(page, args.bom, maps))
            res.data["step"] = lq.current_step(page)
            res.data["charges"] = lq.read_panel(page)
            st = fb.load_state(project_dir, SITE)
            st["bom"] = args.bom
            fb.save_state(project_dir, SITE, st)
            res.next_actions = [
                "`assembly-read`, set `units`, `xy-upload`, then `add-proceed` to Procurement and `procurement-read`."
            ]
        elif cmd == "bom-map":
            res.data.update(
                la_._map_bom_fields(
                    page, {k.lower(): v for k, v in maps.items()}
                )
            )
        elif cmd == "pcb-image":
            lq.open_tab(page, "pcb image")
            res.artifacts.update(la_.pcb_images(page, shots / "shots"))
            lq.open_tab(page, "quotation")
        elif cmd == "assembly-read":
            res.data.update(la_.assembly_state(page))
            st = fb.load_state(project_dir, SITE)
            if (
                st.get("pcb_qty")
                and res.data.get("units")
                and str(st["pcb_qty"]) != str(res.data["units"])
            ):
                res.warnings.append(
                    f"Assembly units ({res.data['units']}) != PCB qty ({st['pcb_qty']}). Lion resets units to 1 after navigation; set `units` deliberately."
                )
            if not any(
                x.get("uploaded") for x in res.data.get("xy_files", [])
            ):
                res.warnings.append(
                    "No XY (pick-and-place) file uploaded yet: `xy-upload --xy <cpl> --side top|bottom|combined`."
                )
            res.data["options"] = lq.read_options(page)
            res.data["charges"] = lq.read_panel(page)
        elif cmd == "units":
            res.data.update(la_.set_units(page, args.n))
            res.data["charges"] = lq.read_panel(page)
        elif cmd == "xy-upload":
            res.data.update(la_.upload_xy(page, args.xy, args.side))
            res.data["assembly"] = la_.assembly_state(page)
        elif cmd == "procurement-read":
            pr = la_.read_procurement(page)
            rep = shots / f"{fb.stamp()}-procurement.json"
            rep.write_text(json.dumps(pr, indent=2))
            res.artifacts["procurement"] = str(rep)
            res.data.update({k: v for k, v in pr.items() if k != "rows"})
            res.data["charges"] = lq.read_panel(page)
            if pr["not_available"]:
                res.next_actions = [
                    "Each not_available MPN: shortlist equivalents (same footprint, voltage/current ratings, pinout) and check "
                    "Lion stock with `alternates-search <MPN> <MPN> ...`; prefer exact_match hits with stock >= required.",
                    "Update the KiCad MPN field / BOM, re-export, `bom-upload` again, `procurement-read` again.",
                    "If a part must be supplied by the user, discuss `procurement-mode 'Partial Procure'` with the user.",
                ]
        elif cmd == "alternates-search":
            res.data.update(la_.search_alternates(page, args.terms, args.qty))
            if res.data.get("not_searched"):
                res.warnings.append(
                    f"Lion searches at most one term per BOM line; re-run for: {res.data['not_searched']}"
                )
        elif cmd == "procurement-mode":
            want = args.mode.strip().lower()
            lab = page.get_by_text(
                re.compile(
                    r"^\s*Procure By (LC|Me)\s*$|^\s*Partial Procure\s*$", re.I
                )
            )
            hit = None
            for i in range(lab.count()):
                if want in lab.nth(i).inner_text().lower():
                    hit = lab.nth(i)
            if not hit:
                raise fb.FabError(
                    "Mode must be one of: Procure By LC, Procure By Me, Partial Procure."
                )
            hit.click(timeout=5000)
            fb.wait_idle(page, timeout_sec=30, settle_sec=1.5)
            res.data.update(
                {
                    k: v
                    for k, v in la_.read_procurement(page).items()
                    if k != "rows"
                }
            )
        elif cmd == "bom-viewer":
            bv = la_.read_bom_viewer(page)
            res.data.update(
                bv
                if args.all_rows
                else {
                    **{k: v for k, v in bv.items() if k != "rows"},
                    "row_count": len(bv["rows"]),
                    "first_rows": bv["rows"][:3],
                }
            )
        elif cmd == "summary-read":
            res.data.update(la_.read_summary(page))
        elif cmd == "shipping":
            page.get_by_text(
                re.compile(
                    r"^\s*" + re.escape(args.method.capitalize()) + r"\s*$"
                )
            ).first.click(timeout=5000)
            fb.wait_idle(page, timeout_sec=20, settle_sec=1.0)
            res.data.update(la_.read_summary(page))
        elif cmd == "download-quote":
            res.artifacts["quote_pdf"] = la_.download_quote(
                page, args.which, shots
            )
        elif cmd == "add-to-cart":
            res.data.update(lq.click_action(page, r"^\s*Add To Cart\s*$", 90))
            st = fb.load_state(project_dir, SITE)
            st.setdefault("cart_adds", []).append(
                {"pid": st.get("pid"), "at": fb.stamp()}
            )
            fb.save_state(project_dir, SITE, st)
            res.next_actions = [
                "`cart-list` to confirm. Payment (Pay Now) is the user's step."
            ]
        elif cmd == "cart-list":
            res.data.update(la_.list_cart(page))
        elif cmd == "cart-remove":
            res.data.update(
                la_.remove_project(page, args.project, args.dry_run)
            )
        res.url, res.title = page.url, page.title()
        res.observations = fb.observe(page)
        return True
    if cmd in ("projects", "project-new"):
        page = fb.find_role_page(
            sess, "lion", URL_MATCH, open_url=lp.PROJECTS_URL
        )
        page.context._cp_shots = str(
            fb.artifacts_dir(project_dir, SITE) / "shots"
        )
        if cmd == "projects":
            res.data["projects"] = lp.list_projects(page)
            res.data.update(lp.billing(page))
        else:
            out = lp.create_project(
                page,
                args.name,
                args.gerber,
                args.layers,
                args.description,
                args.wait_sec,
            )
            if not out.get("pid"):
                # Lion often shows "Problem while processing design files" yet still creates the
                # project; it can take a minute or more to appear in the list.
                before = {p.get("PID") for p in out.get("projects_before", [])}
                deadline = time.time() + 150
                while not out.get("pid") and time.time() < deadline:
                    page.goto(
                        lp.PROJECTS_URL,
                        wait_until="domcontentloaded",
                        timeout=60000,
                    )
                    hits = [
                        p
                        for p in lp.list_projects(page)
                        if p.get("Project Name") == args.name
                        and p.get("PID") not in before
                    ]
                    if hits:
                        out["pid"] = max(
                            hits, key=lambda p: int(p.get("PID") or 0)
                        ).get("PID")
                        out["recovered_from_project_list"] = True
                        res.warnings.append(
                            "Lion showed 'Problem while processing design files' but created the project anyway (normal for this site). "
                            "Verify board dimensions/layers on the quotation page and `pcb-image`."
                        )
                        page.goto(
                            f"{lq.BASE}/projectdetails/{out['pid']}/quotation",
                            wait_until="domcontentloaded",
                            timeout=60000,
                        )
                        fb.wait_idle(page, timeout_sec=60, settle_sec=2.0)
                        break
                    time.sleep(10)
            out.pop("projects_before", None)
            res.data.update(out)
            if out.get("pid"):
                res.data["quotation"] = lq.summarize(page)
            if out.get("pid"):
                st = fb.load_state(project_dir, SITE)
                st.update(
                    {
                        "pid": out["pid"],
                        "project_name": args.name,
                        "gerber": args.gerber,
                    }
                )
                st.setdefault("projects_created", []).append(
                    {"pid": out["pid"], "name": args.name, "at": fb.stamp()}
                )
                fb.save_state(project_dir, SITE, st)
                res.next_actions = [
                    "`quote-read` to see the Fabrication options + price, then `quote-set`."
                ]
            else:
                res.ok = False
                res.status = "error"
                res.next_actions = [
                    "No project named this appeared within ~2.5 min. Run `projects` once more (Lion can be slow) before retrying; "
                    "a retry with the same name creates a duplicate. Check `selected_billing_id`, run `preflight`; "
                    "if it still fails, ask the user to contact support@lioncircuits.com.",
                ]
        res.url, res.title = page.url, page.title()
        res.observations = fb.observe(page)
        return True
    if cmd == "wait-login":
        page = fb.find_page(
            sess, URL_MATCH, open_url="https://order.lioncircuits.com/login/"
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
