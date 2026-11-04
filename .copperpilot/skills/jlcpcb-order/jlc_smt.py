#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""JLCPCB PCBA order flow (cart.jlcpcb.com/smt-order): BOM/CPL, review, placement, quote, cart."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import fab_browser as fb

SMT_RX = r"cart\.jlcpcb\.com/smt-order"
STEPS = ["PCB", "Bill of Materials", "Component Placements", "Quote & Order"]

BOM_REVIEW_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[\s ]+/g, ' ').trim();
  const own = (el) => { if (!el) return ''; const c = el.cloneNode(true);
    c.querySelectorAll('[role=tooltip], .el-popover, table').forEach(x => x.remove()); return clean(c.textContent); };
  const tips = (el) => [...el.querySelectorAll('[role=tooltip], .el-popover')].map(t => clean(t.textContent))
    .filter(t => t && !/Recommended Order Qty|Component Usage/.test(t));
  const body = document.body.innerText || '';
  const num = (rx) => { const m = body.match(rx); return m ? parseInt(m[1]) : null; };
  const header = {
    side: (body.match(/(Top|Bottom) Side\s*\n?\s*Total/) || [])[1] || null,
    parts_detected: num(/(\d+)\s*parts detected/i),
    parts_confirmed: num(/(\d+)\s*Parts confirmed/i),
    parts_not_selected: num(/(\d+)\s*parts not selected/i),
  };
  const rows = [];
  let section = 'matched';
  for (const tr of document.querySelectorAll('tr.el-table__row, .unmatched-title, [class*=unmatched]')) {
    if (!tr.matches('tr')) { if (/Unmatched/i.test(tr.innerText || '')) section = 'unmatched'; continue; }
    const r = tr.getBoundingClientRect(); if (r.height < 2) continue;
    const td = [...tr.children];
    if (td.length < 5) continue;
    const t = (i) => own(td[i]);
    const model = td[3] && td[3].querySelector('.modelName');
    const code = td[3] && td[3].querySelector('.componentCode');
    const desc = td[3] && td[3].querySelector('.description');
    const selCell = td[td.length - 1];
    const cb = tr.querySelector('.el-checkbox, input[type=checkbox]');
    const checked = cb ? (/is-checked/.test(cb.className) || !!tr.querySelector('.el-checkbox.is-checked, input[type=checkbox]:checked')) : null;
    const txt3 = t(3);
    const row = {
      designators: t(0), comment: t(1), footprint: t(2),
      mpn: model ? clean(model.textContent) : null,
      lcsc: code ? clean(code.textContent).split(' ')[0] : null,
      description: desc ? clean(desc.textContent) : (model ? null : txt3),
      qty: t(4) || null, source: t(5) || null, lib_type: t(6) || null, total_cost: t(7) || null,
      selected: checked,
    };
    if (!model && /No Part Selected/i.test(txt3)) { row.unmatched = true; row.mpn = null; }
    const badge = own(selCell);
    if (badge && !/^Select$/.test(badge)) row.flag = badge;
    const cellTexts = new Set(td.map((c) => own(c)));
    const w = tips(tr).filter(x => x.length < 400 && !cellTexts.has(x) && !/^(Edit Part|Select|Search|Pre-order)$/i.test(x)
      && !Object.values(row).includes(x));
    if (w.length) row.notes = [...new Set(w)].slice(0, 4);
    const warnIcon = tr.querySelector('[class*=warn], [class*=Warn], .el-icon-warning, [class*=error]');
    if (warnIcon) row.warning_icon = true;
    if (section === 'unmatched') row.unmatched = true;
    rows.push(row);
  }
  return { header, rows };
}
"""

QUOTE_ORDER_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[ \t ]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim();
  const main = document.querySelector('main') || document.body;
  return clean(main.innerText);
}
"""


def smt_page(sess: fb.Session) -> Any:
    return fb.find_role_page(sess, "smt", SMT_RX)


def current_step(page: Any) -> Optional[str]:
    return page.evaluate(
        r"""(steps) => {
          for (const s of steps) {
            const el = [...document.querySelectorAll('div,span,a,li')].find(e => e.children.length === 0 && (e.innerText||'').trim() === s);
            if (!el) continue;
            const cls = (el.className || '') + ' ' + (el.parentElement ? el.parentElement.className : '');
            const color = getComputedStyle(el).color;
            if (/active|cur|is-active|text-primary/.test(cls) || color === 'rgb(23, 104, 255)' || color === 'rgb(25, 118, 255)') return s;
          }
          return null;
        }""",
        STEPS,
    )


def goto_step(page: Any, step: str) -> Dict[str, Any]:
    match = next(
        (s for s in STEPS if s.lower().startswith(step.lower())), None
    )
    if not match:
        raise fb.FabError(f"Unknown step '{step}'.", steps=STEPS)
    loc = page.get_by_text(
        re.compile(r"^\s*" + re.escape(match) + r"\s*$")
    ).first
    loc.click(timeout=10000)
    idle = fb.wait_idle(page, timeout_sec=60, settle_sec=1.5)
    return {"step": match, "idle": fb._compact_idle(idle)}


def click_next(
    page: Any, wait_sec: float = 60, choose: Optional[str] = None
) -> Dict[str, Any]:
    btns = page.get_by_role("button", name=re.compile(r"^\s*next\s*$", re.I))
    target = None
    for i in range(btns.count()):
        if fb._safe_visible(btns.nth(i)):
            target = btns.nth(i)
    if target is None:
        raise fb.FabError("No visible NEXT button on this step.")
    target.scroll_into_view_if_needed(timeout=5000)
    target.click(timeout=10000)
    time.sleep(1.0)
    collect: Dict[str, Any] = {}
    idle = fb.wait_idle(
        page, timeout_sec=wait_sec, settle_sec=1.5, collect=collect
    )
    out: Dict[str, Any] = {"idle": fb._compact_idle(idle)}
    opts = modal_buttons(page)
    if opts:
        if choose:
            out["dialog"] = choose_modal(page, choose)
        else:
            out["decision_required"] = {
                "dialog": (fb.observe(page).get("modals") or [""])[0][:600],
                "options": opts,
                "how": "Decide (ask the user if it changes cost/what gets assembled), then `smt-next --choose '<option>'` or `dialog --choose`.",
            }
    out["step"] = current_step(page)
    return out


def modal_buttons(page: Any) -> List[str]:
    return page.evaluate(
        r"""() => { const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 2 && r.height > 2; };
             const ms = [...document.querySelectorAll('.el-dialog, .el-message-box, [role=dialog]')].filter(vis);
             const out = []; for (const m of ms) for (const b of m.querySelectorAll('button, a.btn, .el-button'))
               { const t = (b.innerText||'').trim(); if (t && vis(b) && !/^close$/i.test(t)) out.push(t); }
             return [...new Set(out)]; }"""
    )


def choose_modal(page: Any, choice: str) -> Dict[str, Any]:
    opts = modal_buttons(page)
    hit = next((o for o in opts if o.lower() == choice.lower()), None) or next(
        (o for o in opts if choice.lower() in o.lower()), None
    )
    if not hit:
        raise fb.FabError(f"No dialog button '{choice}'.", options=opts)
    btn = (
        page.locator(".el-dialog, .el-message-box, [role=dialog]")
        .get_by_text(re.compile(r"^\s*" + re.escape(hit) + r"\s*$"))
        .first
    )
    fb.guard_click(btn)
    btn.click(timeout=10000)
    time.sleep(1.0)
    idle = fb.wait_idle(page, timeout_sec=60, settle_sec=1.5)
    return {"chose": hit, "idle": fb._compact_idle(idle)}


def upload_bom_cpl(
    page: Any, bom: Optional[str], cpl: Optional[str], wait_sec: float = 180
) -> Dict[str, Any]:
    for f in (bom, cpl):
        if f and not Path(f).is_file():
            raise fb.FabError(f"File not found: {f}")
    inputs = page.locator("input.el-upload__input")
    if inputs.count() < 2:
        # Review screen: open the re-upload dialog.
        btn = page.get_by_text(re.compile(r"Upload BOM/CPL", re.I)).first
        btn.click(timeout=10000)
        time.sleep(1.0)
        inputs = page.locator("input.el-upload__input")
    if inputs.count() < 2:
        raise fb.FabError(
            "BOM/CPL file inputs not found. Go to the Bill of Materials step first (`smt-step --step bom`)."
        )
    # Inputs are rendered BOM first, then CPL; take the last two in case hidden duplicates exist.
    n = inputs.count()
    bom_in, cpl_in = inputs.nth(n - 2), inputs.nth(n - 1)
    if bom:
        bom_in.set_input_files(bom, timeout=15000)
        time.sleep(1.0)
    if cpl:
        cpl_in.set_input_files(cpl, timeout=15000)
        time.sleep(1.0)
    proc = page.get_by_text(re.compile(r"^\s*Process BOM\s*&\s*CPL\s*$", re.I))
    target = None
    for i in range(proc.count()):
        if fb._safe_visible(proc.nth(i)):
            target = proc.nth(i)
    if target is None:
        raise fb.FabError(
            "'Process BOM & CPL' button not visible after attaching files."
        )
    target.click(timeout=10000)
    t0 = time.time()
    try:
        page.get_by_text(re.compile(r"parts detected", re.I)).first.wait_for(
            state="visible", timeout=int(wait_sec * 1000)
        )
    except Exception:
        pass
    collect: Dict[str, Any] = {}
    idle = fb.wait_idle(page, timeout_sec=30, settle_sec=2.0, collect=collect)
    return {
        "processing_sec": round(time.time() - t0, 1),
        "idle": fb._compact_idle(idle),
        "observations": fb.observe(page),
    }


def read_bom_review(page: Any) -> Dict[str, Any]:
    raw = page.evaluate(BOM_REVIEW_JS)
    rows = raw["rows"]
    problems = []
    for r in rows:
        why = []
        if r.get("unmatched"):
            why.append("no part matched")
        if r.get("selected") is False:
            why.append("not selected (will not be assembled)")
        if r.get("flag"):
            why.append(r["flag"])
        if r.get("notes"):
            why += r["notes"]
        if r.get("qty") in ("0",):
            why.append("qty 0 / out of stock")
        if why:
            problems.append(
                {
                    "designators": r["designators"],
                    "comment": r["comment"],
                    "mpn": r.get("mpn"),
                    "lcsc": r.get("lcsc"),
                    "issues": why,
                }
            )
    lib: Dict[str, Any] = {}
    for r in rows:
        if r.get("lib_type"):
            lib[r["lib_type"]] = lib.get(r["lib_type"], 0) + 1
    return {
        "header": raw["header"],
        "lines": len(rows),
        "lib_type_counts": lib,
        "problems": problems,
        "rows": rows,
    }


def read_quote_order(page: Any) -> Dict[str, Any]:
    text = page.evaluate(QUOTE_ORDER_JS)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    money = re.compile(r"^\$[\d,]+(\.\d+)?$")
    items = []
    for i, ln in enumerate(lines[:-1]):
        nxt = lines[i + 1]
        if not money.match(ln) and money.match(nxt) and len(ln) < 60:
            items.append({"label": ln.rstrip(":"), "amount": nxt})
    total = None
    m = re.search(r"Total Price:?\s*\n?\s*(\$[\d,.]+)", text)
    if m:
        total = m.group(1)
    weight = None
    m = re.search(r"Weight\s*\n?\s*([\d.]+\s*g)", text)
    if m:
        weight = m.group(1)
    build = re.findall(r"(PCB|PCBA)\s*:\s*([^\n$]+)", text)
    radios = page.evaluate(
        r"""() => [...document.querySelectorAll('.el-radio')].filter(e => e.getBoundingClientRect().width > 0)
              .map(e => ({ option: (e.innerText||'').trim().replace(/\s+/g, ' '), selected: /is-checked/.test(e.className) }))"""
    )
    needs_desc = bool(
        page.evaluate(
            "() => { const i = document.querySelector('.el-cascader input'); return !!i && !i.value; }"
        )
    )
    return {
        "total": total,
        "weight": weight,
        "items": items,
        "build_time": [f"{a}: {b.strip()}" for a, b in build],
        "pcba_build_time_options": radios,
        "product_description": page.evaluate(
            "() => document.querySelector('.el-cascader input')?.value || null"
        ),
        "product_description_required": needs_desc,
    }


def _cascader_menus(page: Any) -> List[List[str]]:
    return page.evaluate(
        r"""() => [...document.querySelectorAll('.el-cascader-menu')].filter(m => m.getBoundingClientRect().width > 0)
              .map(m => [...m.querySelectorAll('.el-cascader-node')].map(n => n.innerText.trim()))"""
    )


def set_product_description(page: Any, value: Optional[str]) -> Dict[str, Any]:
    """Customs description cascader. value = 'Category > Item' (substrings, case-insensitive) or None to list."""
    inp = page.locator(".el-cascader input").first
    if not inp.count():
        raise fb.FabError(
            "Product Description field not found. Go to the Quote & Order step."
        )
    inp.click(timeout=5000)
    time.sleep(0.6)
    menus = _cascader_menus(page)
    if not menus:
        raise fb.FabError("Product Description menu did not open.")
    if not value:
        cats = {}
        for cat in menus[0]:
            page.locator(".el-cascader-node", has_text=cat).first.click(
                timeout=5000
            )
            time.sleep(0.3)
            m = _cascader_menus(page)
            cats[cat] = m[1] if len(m) > 1 else []
        page.keyboard.press("Escape")
        return {"options": cats}
    parts = [p.strip().lower() for p in re.split(r">|/", value) if p.strip()]
    level1 = next((c for c in menus[0] if parts[0] in c.lower()), None)
    if not level1 and len(parts) == 1:
        for cat in menus[0]:
            page.locator(".el-cascader-node", has_text=cat).first.click(
                timeout=5000
            )
            time.sleep(0.3)
            m = _cascader_menus(page)
            if len(m) > 1 and any(parts[0] in c.lower() for c in m[1]):
                level1, parts = cat, [cat.lower(), parts[0]]
                break
    if not level1:
        page.keyboard.press("Escape")
        raise fb.FabError(
            f"No category or item containing '{parts[0]}'. Omit the value to list all options.",
            categories=menus[0],
        )
    page.locator(".el-cascader-node", has_text=level1).first.click(
        timeout=5000
    )
    time.sleep(0.5)
    menus = _cascader_menus(page)
    if len(menus) < 2:
        return {"product_description": level1}
    want = parts[1] if len(parts) > 1 else ""
    level2 = next((c for c in menus[1] if want and want in c.lower()), None)
    if not level2:
        page.keyboard.press("Escape")
        raise fb.FabError(f"Pick an item under '{level1}'.", items=menus[1])
    page.locator(".el-cascader-menu").nth(1).locator(
        ".el-cascader-node", has_text=level2
    ).first.click(timeout=5000)
    time.sleep(0.8)
    shown = inp.input_value()
    return {"product_description": shown or f"{level1} / {level2}"}


def save_to_cart(page: Any) -> Dict[str, Any]:
    btn = page.get_by_role(
        "button", name=re.compile(r"^\s*save to cart\s*$", re.I)
    )
    target = None
    for i in range(btn.count()):
        if fb._safe_visible(btn.nth(i)):
            target = btn.nth(i)
    if target is None:
        raise fb.FabError(
            "No visible SAVE TO CART button. Finish the current step first."
        )
    fb.guard_click(target)
    target.click(timeout=10000)
    try:
        page.wait_for_url(re.compile(r"shopcart"), timeout=30000)
    except Exception:
        pass
    time.sleep(2.0)
    collect: Dict[str, Any] = {}
    idle = fb.wait_idle(page, timeout_sec=60, settle_sec=2.0, collect=collect)
    return {
        "clicked": "SAVE TO CART",
        "url_after": page.url,
        "idle": fb._compact_idle(idle),
        "observations": fb.observe(page),
    }


POLARIZED_PREFIXES = (
    "U",
    "IC",
    "D",
    "LED",
    "J",
    "T",
    "Q",
    "SW",
    "ESD",
    "Y",
    "X",
    "BT",
)

PLACEMENT_LIST_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[\s\u00a0]+/g, ' ').trim();
  const rows = [];
  for (const tr of document.querySelectorAll('tr')) {
    const td = [...tr.querySelectorAll('td')];
    if (td.length < 4) continue;
    const r = tr.getBoundingClientRect(); if (r.width < 2) continue;
    const des = clean(td[0].innerText);
    if (!/^[A-Za-z]+\d/.test(des)) continue;
    rows.push({ designators: des, lcsc: clean(td[1].innerText), comment: clean(td[2].innerText), footprint: clean(td[3].innerText) });
  }
  return rows;
}
"""


def _viewer_box(page: Any) -> Optional[Dict[str, float]]:
    return page.evaluate(
        r"""() => { const cs = [...document.querySelectorAll('canvas')].map(c => c.getBoundingClientRect()).filter(r => r.width > 300 && r.height > 200);
                   cs.sort((a, b) => b.width * b.height - a.width * a.height); const r = cs[0];
                   if (!r) return null; const top = Math.max(r.y, 0); return { x: r.x, y: top, width: r.width, height: Math.min(r.height, window.innerHeight - top) }; }"""
    )


def _toggle(page: Any, label: str) -> None:
    loc = page.get_by_text(re.compile(r"^\s*" + re.escape(label) + r"\s*$"))
    for i in range(loc.count()):
        el = loc.nth(i)
        if fb._safe_visible(el):
            el.click(timeout=5000)
            time.sleep(1.2)
            return


def placement_list(page: Any) -> List[Dict[str, Any]]:
    return page.evaluate(PLACEMENT_LIST_JS)


def download_placement_image(
    page: Any, out_dir: Path, side: str
) -> Optional[str]:
    icon = page.locator("i[class*=download-icon]").first
    if not icon.count():
        return None
    with page.expect_download(timeout=30000) as dl:
        icon.click(timeout=5000)
    d = dl.value
    name = d.suggested_filename or f"placement-{side}.png"
    dest = out_dir / f"{fb.stamp()}-jlc-{side}-{name}"
    d.save_as(str(dest))
    return str(dest)


def placement_shots(
    page: Any,
    out_dir: Path,
    designators: Optional[List[str]],
    view: str,
    side: str,
    max_parts: int = 12,
    download_image: bool = False,
) -> Dict[str, Any]:
    page.evaluate("() => window.scrollTo(0, 0)")
    time.sleep(0.5)
    if "Component Placements" != current_step(page):
        goto_step(page, "Component Placements")
    _toggle(page, side.capitalize())
    _toggle(page, view.upper())
    rows = placement_list(page)
    out: Dict[str, Any] = {
        "view": view,
        "side": side,
        "parts_listed": len(rows),
        "shots": [],
    }
    # Overview: fit to window (toolbar icon title varies; try keyboard-free approach via icon order).
    box = _viewer_box(page)
    if not box:
        raise fb.FabError(
            "Placement viewer canvas not found (still 'Processing files…'?). Wait and retry."
        )
    fit = page.locator("i[class*=adapt-window-icon]")
    for i in range(fit.count()):
        if fb._safe_visible(fit.nth(i)):
            try:
                fit.nth(i).click(timeout=3000)
                time.sleep(1.0)
            except Exception:
                pass
            break
    out["overview"] = fb.screenshot(
        page,
        out_dir / f"{fb.stamp()}-placement-{side}-{view}-overview.png",
        clip=box,
    )
    if download_image:
        try:
            out["downloaded_image"] = download_placement_image(
                page, out_dir, side
            )
        except Exception as exc:
            out["downloaded_image_error"] = str(exc).splitlines()[0]
    wanted: List[str] = []
    if designators:
        wanted = designators
    else:
        for r in rows:
            first = r["designators"].split(",")[0].strip()
            m = re.match(r"[A-Za-z]+", first)
            pref = m.group(0).upper() if m else ""
            if pref in POLARIZED_PREFIXES:
                wanted.append(first)
    for des in wanted[:max_parts]:
        row = next(
            (
                r
                for r in rows
                if des in [x.strip() for x in r["designators"].split(",")]
            ),
            None,
        )
        if not row:
            out["shots"].append(
                {
                    "designator": des,
                    "error": "not in placement list (not assembled on this side?)",
                }
            )
            continue
        trs = page.locator("tr").filter(
            has=page.locator(
                "td",
                has_text=re.compile(
                    r"(^|,)\s*" + re.escape(des) + r"\s*(,|$)"
                ),
            )
        )
        clicked = False
        for i in range(trs.count()):
            if fb._safe_visible(trs.nth(i)):
                trs.nth(i).click(timeout=5000)
                clicked = True
                break
        if not clicked:
            out["shots"].append(
                {"designator": des, "error": "row not clickable"}
            )
            continue
        time.sleep(1.5)
        box = _viewer_box(page) or box
        path = fb.screenshot(
            page,
            out_dir / f"{fb.stamp()}-placement-{side}-{view}-{des}.png",
            clip=box,
        )
        out["shots"].append(
            {
                "designator": des,
                "lcsc": row["lcsc"],
                "comment": row["comment"],
                "footprint": row["footprint"],
                "screenshot": path,
            }
        )
    if len(wanted) > max_parts:
        out["note"] = (
            f"{len(wanted) - max_parts} more parts not captured; pass --designators or raise --max-parts."
        )
    return out
