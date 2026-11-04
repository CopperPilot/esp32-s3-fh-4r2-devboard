#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""Lion Circuits assembly, procurement, BOM viewer, summary and cart."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import fab_browser as fb

BASE = "https://order.lioncircuits.com"
CART_URL = f"{BASE}/cart"
BOM_FIELDS = [
    "Item Number",
    "Designator",
    "Unit Quantity",
    "Description",
    "Manufacturer Part Number",
    "Footprint",
    "Value",
    "Assembly Instructions",
]


def _dialog(page: Any) -> Any:
    return page.locator("[role=dialog]").last


def _map_bom_fields(page: Any, overrides: Dict[str, str]) -> Dict[str, Any]:
    dlg = _dialog(page)
    dlg.get_by_text(re.compile("Map your (BOM )?fields", re.I)).first.wait_for(
        timeout=30000
    )
    selects = dlg.locator("select")
    n = selects.count()
    if n != len(BOM_FIELDS):
        raise fb.FabError(
            f"Expected {len(BOM_FIELDS)} BOM field selectors, found {n}. Use snapshot + select.",
            dialog=dlg.inner_text()[:800],
        )
    mapping: Dict[str, Any] = {}
    for i, field in enumerate(BOM_FIELDS):
        sel = selects.nth(i)
        options = [o.strip() for o in sel.locator("option").all_inner_texts()]
        current = sel.evaluate(
            "s => s.options[s.selectedIndex] ? s.options[s.selectedIndex].text : ''"
        ).strip()
        want = overrides.get(field.lower())
        auto = False
        if not want and current.lower() in ("", "yet to map"):
            want = next(
                (o for o in options if o.lower() == field.lower()), None
            )
            auto = bool(want)
        if want and want != current:
            if want not in options:
                raise fb.FabError(
                    f"Column '{want}' not in the uploaded file for field {field}.",
                    columns=[o for o in options if o != "Yet to map"],
                )
            sel.select_option(label=want)
            current = want
        mapping[field] = {
            "column": None if current.lower() == "yet to map" else current,
            "auto_filled_by_skill": auto,
        }
    unmapped_required = [f for f in BOM_FIELDS[:4] if not mapping[f]["column"]]
    if unmapped_required:
        raise fb.FabError(
            "Required BOM fields not mapped.",
            fields=unmapped_required,
            mapping=mapping,
        )
    dlg.get_by_role("button", name=re.compile(r"^\s*next\s*$", re.I)).click(
        timeout=10000
    )
    collect: Dict[str, Any] = {}
    found = None
    deadline = time.time() + 120
    while time.time() < deadline:
        fb.wait_idle(page, timeout_sec=10, settle_sec=1.0, collect=collect)
        txt = page.evaluate(
            "() => [...document.querySelectorAll('[role=dialog]')].map(d => d.innerText).join('\\n')"
        )
        m = re.search(r"(\d+)\s+components?", txt or "", re.I)
        if m or re.search(r"found", txt or "", re.I):
            found = (txt or "").strip()[:400]
            ok = page.locator("[role=dialog]").get_by_role(
                "button",
                name=re.compile(r"^\s*(ok|okay|done|continue)\s*$", re.I),
            )
            if ok.count():
                ok.first.click(timeout=5000)
            break
        if not txt:
            break
        time.sleep(1)
    fb.wait_idle(page, timeout_sec=30, settle_sec=1.5, collect=collect)
    return {
        "mapping": mapping,
        "processing_dialog": found,
        "toasts": collect.get("toasts_seen", []),
    }


def upload_bom(
    page: Any, bom: str, overrides: Dict[str, str]
) -> Dict[str, Any]:
    if not Path(bom).is_file():
        raise fb.FabError(f"BOM not found: {bom}")
    inp = page.locator("input#file-upload, input[type=file][accept*=csv]")
    if not inp.count():
        # BOM viewer / assembly re-upload button.
        btn = page.get_by_text(
            re.compile(r"^\s*(RE ?UPLOAD BOM|Change File)\s*$", re.I)
        ).first
        if not btn.count():
            step = page.evaluate(
                "() => document.querySelector('[class*=Quotationbar_active]')?.innerText?.replace(/^\\d+\\s*/, '').trim() || null"
            )
            raise fb.FabError(
                f"No BOM upload control on this page (step: {step or 'not on the QUOTATION wizard'}). "
                "Run `tab quotation`, then `add-proceed` from Fabrication or `goto-step assembly`, then retry.",
                step=step,
                url=page.url,
            )
        btn.click(timeout=10000)
        time.sleep(1.0)
        inp = page.locator("input[type=file]")
    inp.first.set_input_files(bom, timeout=15000)
    time.sleep(1.0)
    out = _map_bom_fields(page, {k.lower(): v for k, v in overrides.items()})
    out["file"] = bom
    return out


def assembly_state(page: Any) -> Dict[str, Any]:
    return page.evaluate(
        r"""() => {
          const clean = (t) => (t || '').replace(/[\s ]+/g, ' ').trim();
          const body = document.body.innerText || '';
          const units = document.querySelector('input[name=units], input#units, input[type=number]');
          const bomFile = (body.match(/([\w.\-]+\.(csv|xlsx?|xlsm))\s*\n?\s*(Change File)?/i) || [])[1] || (/Bom File Uploaded/i.test(body) ? 'uploaded' : null);
          const xy = [...document.querySelectorAll('[class*=xy_file_uploads]')].map(u => ({ side: clean(u.innerText),
             uploaded: !!u.querySelector('[class*=xy_uploaded]') }));
          return { units: units ? units.value : null, bom_file: bomFile, xy_files: xy,
                   notes: [...document.querySelectorAll('li')].map(l => clean(l.innerText)).filter(t => /Tape|Through-Hole|Procurement Tool|Sourced Components/i.test(t)) };
        }"""
    )


def set_units(page: Any, units: int) -> Dict[str, Any]:
    inp = page.locator("input[type=number]").first
    inp.click(timeout=5000)
    inp.fill(str(units))
    inp.press("Tab")
    fb.wait_idle(page, timeout_sec=20, settle_sec=1.0)
    return {"units": inp.input_value()}


def upload_xy(page: Any, xy: str, side: str) -> Dict[str, Any]:
    """Tile (Top/Bottom/Combined) -> 'Upload XY File' dialog -> its own input -> UPLOAD.

    Only the dialog's input is used: the page also has the BOM input, and
    putting a CPL there would replace the BOM.
    """
    if not Path(xy).is_file():
        raise fb.FabError(f"XY/CPL file not found: {xy}")
    label = {"top": "Top", "bottom": "Bottom", "combined": "Combined"}[
        side.lower()
    ]
    tile = (
        page.locator("[class*=xy_file_uploads]")
        .filter(
            has=page.locator("h5", has_text=re.compile(rf"^\s*{label}\s*$"))
        )
        .locator("[class*=xy_file_div]")
        .first
    )
    if not tile.count():
        raise fb.FabError(
            "XY File tiles not found. Are you on the Assembly step?"
        )
    tile.click(timeout=10000)
    dlg = (
        page.locator("[role=dialog]")
        .filter(has_text=re.compile("Upload XY File", re.I))
        .last
    )
    dlg.wait_for(timeout=15000)
    dlg.locator("input[type=file]").first.set_input_files(xy, timeout=15000)
    time.sleep(1.0)
    dlg.get_by_role("button", name=re.compile(r"^\s*upload\s*$", re.I)).click(
        timeout=10000
    )
    collect: Dict[str, Any] = {}
    fb.wait_idle(page, timeout_sec=60, settle_sec=1.5, collect=collect)
    return {
        "xy_file": xy,
        "side": label,
        "toasts": collect.get("toasts_seen", []),
        "observations": fb.observe(page),
    }


PROCUREMENT_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[\s ]+/g, ' ').trim();
  const body = document.body.innerText || '';
  const mode = [...document.querySelectorAll('input[type=radio]')].filter(r => r.checked).map(r => clean((r.closest('label') || r.parentElement.parentElement).innerText));
  const tag = (body.match(/Iteration Tag\s*:\s*(\S+)/) || [])[1] || null;
  const boards = (body.match(/Total Number Of Boards\s*:\s*(\d+)/) || [])[1] || null;
  const rows = [];
  for (const tr of document.querySelectorAll('tr')) {
    const td = [...tr.querySelectorAll('td')];
    if (td.length < 6) continue;
    const icon = td[1] && td[1].querySelector('svg, img');
    const color = icon ? getComputedStyle(icon).color + ' ' + (icon.getAttribute('fill') || '') + ' ' + (icon.getAttribute('class') || '') : '';
    const cells = td.map(c => clean(c.innerText));
    const unavailable = /No Component/i.test(cells.join(' '));
    rows.push({ no: cells[0], mpn: cells[1], unit_qty: cells[2], required_qty: cells[3], order_qty: cells[4], unit_price: cells[5], extended_cost: cells[6] || null, available: !unavailable });
  }
  return { mode, iteration_tag: tag, total_boards: boards, rows };
}
"""


def read_procurement(page: Any) -> Dict[str, Any]:
    raw = page.evaluate(PROCUREMENT_JS)
    rows = raw["rows"]
    missing = [r for r in rows if not r["available"]]
    moq_bumps = [
        r
        for r in rows
        if r["available"]
        and r["order_qty"]
        and r["required_qty"]
        and r["order_qty"].isdigit()
        and r["required_qty"].isdigit()
        and int(r["order_qty"]) > int(r["required_qty"])
    ]
    return {
        **{k: v for k, v in raw.items() if k != "rows"},
        "lines": len(rows),
        "available": len(rows) - len(missing),
        "not_available": [
            {"mpn": r["mpn"], "required_qty": r["required_qty"]}
            for r in missing
        ],
        "moq_bumps": [
            {
                "mpn": r["mpn"],
                "required": r["required_qty"],
                "order": r["order_qty"],
            }
            for r in moq_bumps
        ],
        "rows": rows,
    }


ALTERNATES_JS = r"""
async ({ terms, qty }) => {
  const root = document.getElementById('root');
  const key = root && Object.keys(root).find(k => k.startsWith('__reactContainer') || k.startsWith('_reactRootContainer'));
  let st = null;
  const seen = new Set(), q = key ? [root[key]] : [];
  while (q.length && seen.size < 200000) {
    const n = q.shift();
    if (!n || typeof n !== 'object' || seen.has(n)) continue;
    seen.add(n);
    if (n.store && typeof n.store.getState === 'function') { st = n.store.getState(); break; }
    for (const v of Object.values(n)) if (v && typeof v === 'object') q.push(v);
  }
  const bp = st && st.bomParserValues;
  const rowsIn = bp && bp.bomParsedData && bp.bomParsedData.notAvailableComponents;
  if (!rowsIn || !rowsIn.length || !bp.bomProjectId) return { error: 'no_bom_state' };
  const base = JSON.parse(JSON.stringify(rowsIn));
  const n = Math.min(terms.length, base.length);
  base.forEach((r, i) => {
    r.selected = i < n ? 1 : 0;
    if (i < n) { r.description = terms[i]; if (qty) r.requiredQuantity = qty; }
  });
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
  const currency = (bp.bomParsedData.iterationData && bp.bomParsedData.iterationData.iterationBomData || {}).currency || 'INR';
  const r = await fetch('/searchAlternateMpn/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: JSON.stringify({ notAvailableComponentData: base, currency, bomProjectId: bp.bomProjectId }),
  });
  let res = await r.text();
  for (let i = 0; i < 2 && typeof res === 'string'; i++) { try { res = JSON.parse(res); } catch (e) { break; } }
  if (!res || res.lcStatus !== 1200) return { error: 'search_failed', http: r.status, response: res, searched: n };
  const out = {};
  for (const [k, v] of Object.entries(res.alternateComponents || {})) {
    const term = terms[Number(k)] !== undefined ? terms[Number(k)] : v.description;
    out[term] = (v.mpnData || []).map(m => ({
      mpn: m.mpn, description: m.description, stock: m.inStockQuantity, unit_cost: m.unitCost, extended_cost: m.extendedCost,
    }));
  }
  return { currency, searched: n, max_terms: base.length, results: out };
}
"""


def search_alternates(
    page: Any, terms: List[str], qty: Optional[int] = None
) -> Dict[str, Any]:
    """Lion's 'Search For Alternate Components': free-text catalog search, one result list per term."""
    raw = page.evaluate(ALTERNATES_JS, {"terms": terms, "qty": qty})
    if raw.get("error") == "no_bom_state":
        raise fb.FabError(
            "No BOM loaded in this page. Open the project (`project-open --pid N`), make sure a BOM is uploaded, then retry."
        )
    if raw.get("error"):
        raise fb.FabError("Lion alternate search failed.", detail=raw)
    results = {}
    for term, hits in raw["results"].items():
        exact = [
            h for h in hits if (h.get("mpn") or "").lower() == term.lower()
        ]
        results[term] = {
            "exact_match": bool(exact),
            "hits": sorted(
                hits,
                key=lambda h: (
                    h.get("mpn", "").lower() != term.lower(),
                    -(h.get("stock") or 0),
                ),
            )[:8],
        }
    out = {"currency": raw["currency"], "results": results}
    if len(terms) > raw["searched"]:
        out["not_searched"] = terms[raw["searched"] :]
    return out


BOM_VIEWER_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[\s ]+/g, ' ').trim();
  const body = document.body.innerText || '';
  const version = (body.match(/BOM Version\s*:\s*(V[\d.]+)/i) || [])[1] || null;
  const updated = (body.match(/Last Update\s*:\s*([^\n]+)/i) || [])[1] || null;
  const head = [...document.querySelectorAll('th')].map(th => clean(th.innerText));
  const rows = [];
  for (const tr of document.querySelectorAll('tbody tr')) {
    const td = [...tr.querySelectorAll('td')].map(c => clean(c.innerText));
    if (td.length < 5) continue;
    const o = {}; head.forEach((h, i) => { if (h) o[h] = td[i]; });
    const mpnCell = tr.querySelector('td svg, td img');
    rows.push(o);
  }
  return { version, last_update: updated, columns: head.filter(Boolean), rows };
}
"""


def read_bom_viewer(page: Any) -> Dict[str, Any]:
    return page.evaluate(BOM_VIEWER_JS)


SUMMARY_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[ \t ]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim();
  const body = document.body.innerText || '';
  const ship = [...document.querySelectorAll('[class*=shipping_option]')].filter(e => !/column|radio/.test(e.className))
     .map(e => ({ option: clean(e.innerText), selected: (e.className.match(/FabricationQuotation_/g) || []).length > 1 || /selected|active/.test(e.className) }));
  const h = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && (e.innerText || '').trim() === 'Charge Details');
  let p = h; for (let i = 0; i < 2 && p; i++) p = p.parentElement;
  return { shipping_options: ship.slice(0, 2), charges_text: p ? clean(p.innerText) : null,
           buttons: [...document.querySelectorAll('button')].map(b => clean(b.innerText)).filter(t => /cart|pay|quote|apply/i.test(t)) };
}
"""


def read_summary(page: Any) -> Dict[str, Any]:
    raw = page.evaluate(SUMMARY_JS)
    lines = [
        ln.strip()
        for ln in (raw.get("charges_text") or "").splitlines()
        if ln.strip()
    ]
    money = re.compile(r"^(₹|\$)\s?[\d,]+(\.\d+)?$")
    sections: Dict[str, Any] = {}
    for name in ("Fabrication", "Assembly", "Procurement"):
        if name in lines:
            i = lines.index(name)
            detail = (
                lines[i + 1]
                if i + 1 < len(lines) and not money.match(lines[i + 1])
                else None
            )
            amt = next(
                (ln for ln in lines[i + 1 : i + 4] if money.match(ln)), None
            )
            sections[name.lower()] = {"detail": detail, "amount": amt}

    def after(label: str) -> Optional[str]:
        if label not in lines:
            return None
        i = lines.index(label)
        return next(
            (
                ln
                for ln in lines[i + 1 : i + 4]
                if money.match(ln) or ln in ("Free",)
            ),
            None,
        )

    return {
        "shipping_options": raw["shipping_options"],
        "charges": sections,
        "items_total": after("Items"),
        "shipping": after("Shipping"),
        "gst": next((after(ln) for ln in lines if ln.startswith("GST")), None),
        "total_incl_gst_shipping": after("Total"),
        "buttons": raw["buttons"],
    }


def download_quote(page: Any, which: str, out_dir: Path) -> Optional[str]:
    label = {"fab": "Fab Quote", "assembly": "Assembly Quote"}[which]
    el = page.get_by_text(re.compile(r"^\s*" + label + r"\s*$")).first
    with page.expect_download(timeout=90000) as dl:
        el.click(timeout=10000)
    d = dl.value
    dest = (
        out_dir
        / f"{fb.stamp()}-{which}-quote-{d.suggested_filename or 'quote.pdf'}"
    )
    d.save_as(str(dest))
    return str(dest)


CART_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[\s\u00a0]+/g, ' ').trim();
  const body = document.body.innerText || '';
  if (/cart is empty/i.test(body)) return { empty: true, projects: [] };
  const projects = [];
  for (const pj of document.querySelectorAll('[class*=cart__item__project]')) {
    const name = clean((pj.querySelector('h2') || {}).innerText);
    const lines = [...pj.querySelectorAll('[class*=cart__item__]')].filter(e => !/project/.test(e.className)).map(it => ({
      kind: clean((it.querySelector('h2') || {}).innerText),
      detail: clean((it.querySelector('[class*=sub_text]') || {}).innerText),
      specs: [...it.querySelectorAll('[class*=spec_text]')].map(p => clean(p.innerText)).filter(Boolean),
      units: clean((it.querySelector('[class*=item_qty] h3') || {}).innerText),
      price: clean((it.querySelector('[class*=item_price]') || {}).innerText),
    }));
    projects.push({ name, lines });
  }
  const sub = (body.match(/Sub Total\s*\n?\s*(₹\s?[\d,]+)/) || [])[1] || null;
  return { empty: projects.length === 0, projects, sub_total: sub };
}
"""


def list_cart(page: Any) -> Dict[str, Any]:
    if "/cart" not in page.url:
        page.goto(CART_URL, wait_until="domcontentloaded", timeout=60000)
    else:
        page.reload(wait_until="domcontentloaded", timeout=60000)
    try:
        page.locator(
            "[class*=cart__item__project], :text('cart is empty')"
        ).first.wait_for(timeout=30000)
    except Exception:
        pass
    fb.wait_idle(page, timeout_sec=30, settle_sec=1.5)
    return page.evaluate(CART_JS)


def remove_project(
    page: Any, name: str, dry_run: bool = False
) -> Dict[str, Any]:
    """Remove a whole project (fab + assembly + procurement) from the cart by exact project name."""
    before = list_cart(page)
    hits = [p for p in before.get("projects", []) if p["name"] == name]
    if not hits or dry_run:
        return {
            "matched": hits,
            "removed": 0,
            "dry_run": dry_run,
            "cart_before": before,
        }
    block = (
        page.locator("[class*=cart__item__project]")
        .filter(
            has=page.locator(
                "h2", has_text=re.compile("^" + re.escape(name) + "$")
            )
        )
        .first
    )
    header = block.locator("[class*=project_name_container]").first
    removed = 0
    for _ in range(4):  # project-level delete, else line-by-line
        header.hover(timeout=5000)
        time.sleep(0.4)
        icons = block.locator("img[alt=Delete]")
        target = None
        for i in range(icons.count()):
            if fb._safe_visible(icons.nth(i)):
                target = icons.nth(i)
                break
        if target is None:
            break
        target.click(timeout=5000)
        time.sleep(0.8)
        dlg = page.locator("[role=dialog]").last
        if dlg.count() and fb._safe_visible(dlg):
            btn = dlg.get_by_role(
                "button",
                name=re.compile(r"^\s*(yes|delete|remove|confirm|ok)\b", re.I),
            )
            if btn.count():
                btn.first.click(timeout=5000)
        fb.wait_idle(page, timeout_sec=30, settle_sec=1.5)
        removed += 1
        now = page.evaluate(CART_JS)
        if not any(p["name"] == name for p in now.get("projects", [])):
            break
    after = list_cart(page)
    return {
        "matched": hits,
        "delete_clicks": removed,
        "still_in_cart": any(
            p["name"] == name for p in after.get("projects", [])
        ),
        "cart_after": after,
    }


def pcb_images(page: Any, out_dir: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for side in ("Top", "Bottom"):
        el = page.get_by_text(re.compile(rf"^\s*{side}\s*$")).first
        try:
            el.click(timeout=5000)
            time.sleep(2.0)
        except Exception:
            pass
        imgs = page.locator("main img, [class*=image] img, canvas")
        box = None
        best = 0
        for i in range(min(imgs.count(), 30)):
            b = imgs.nth(i).bounding_box()
            if b and b["width"] * b["height"] > best:
                best, box = b["width"] * b["height"], b
        path = out_dir / f"{fb.stamp()}-lion-pcb-{side.lower()}.png"
        out[side.lower()] = (
            fb.screenshot(page, path, clip=box)
            if box and best > 40000
            else fb.screenshot(page, path)
        )
    return out
