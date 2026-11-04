#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""JLCPCB quote page (cart.jlcpcb.com/quote): Gerber upload, options, price."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import fab_browser as fb

QUOTE_URL = "https://cart.jlcpcb.com/quote"

# Reads every visible option row: label, buttons (selected/disabled), inputs.
OPTIONS_JS = r"""
(scopeSel) => {
  const clean = (t) => (t || '').replace(/\s+/g, ' ').trim();
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 1 && r.height > 1; };
  const root = scopeSel ? document.querySelector(scopeSel) : document;
  if (!root) return [];
  const rows = [];
  const seen = new Set();
  for (const g of root.querySelectorAll('.main-btn-group, .el-form-item, .smt-form-item')) {
    if (!vis(g) || seen.has(g)) continue;
    const lab = g.querySelector(':scope > label, :scope > .el-form-item__label, :scope > div > label');
    if (!lab) continue;
    const label = clean([...lab.childNodes]
      .filter(n => n.nodeType === 3 || (n.tagName && !n.classList.contains('pcb-faqs')))
      .map(n => n.textContent).join(' '));
    if (!label) continue;
    seen.add(g);
    const buttons = [...g.querySelectorAll('button, a.btn, a[type=button]')]
      .filter(b => vis(b) && !b.closest('.el-popover'))
      .map(b => ({
        text: clean(b.innerText),
        selected: /(^|\s)(cur|active|is-active|selected)(\s|$)/.test(b.className),
        disabled: !!b.disabled || /disabled/.test(b.className),
      }));
    const inputs = [...g.querySelectorAll('input:not([type=hidden]):not([type=file])')]
      .filter(vis)
      .map(i => ({ type: i.type, value: i.value, placeholder: i.placeholder || undefined,
                   checked: (i.type === 'checkbox' || i.type === 'radio') ? i.checked : undefined,
                   disabled: i.disabled || undefined }));
    // Custom dropdowns (PCB Qty / PCBA Qty) show the value in a span.
    let shown = '';
    const refs = [...g.querySelectorAll('.el-popover__reference-wrapper')].filter(r => !r.closest('label'));
    const ref = refs[refs.length - 1];
    if (ref && !buttons.length && !inputs.length) shown = clean(ref.innerText);
    const hint = [...g.querySelectorAll('.tips, .tip, .text-red, .red, .warning, .el-form-item__error')]
      .filter(vis).map(e => clean(e.innerText)).filter(Boolean).join(' | ');
    const row = { label };
    const sel = buttons.filter(b => b.selected).map(b => b.text);
    if (sel.length) row.selected = sel.length === 1 ? sel[0] : sel;
    else if (shown) row.selected = shown;
    else if (inputs.length) row.selected = inputs.map(i => i.type === 'checkbox' ? i.checked : i.value);
    if (buttons.length) row.options = buttons.map(b => b.text);
    const dis = buttons.filter(b => b.disabled).map(b => b.text);
    if (dis.length) row.disabled = dis;
    if (hint) row.hint = hint;
    rows.push(row);
  }
  // Advanced PCBA options: [data-service-code] rows with an el-select.
  for (const g of root.querySelectorAll('[data-service-code]')) {
    if (!vis(g) || seen.has(g)) continue;
    if (g.parentElement && g.parentElement.closest('[data-service-code]')) continue;
    const labEl = g.querySelector('span.text-14, span');
    const label = clean(labEl ? labEl.innerText : '');
    if (!label) continue;
    seen.add(g);
    const inp = g.querySelector('.el-select input');
    const lis = [...g.querySelectorAll('li.el-select-dropdown__item')];
    const own = (li) => { const c = li.cloneNode(true); c.querySelectorAll('[role=tooltip], .el-popover').forEach(x => x.remove()); return clean(c.textContent); };
    const tip = (li) => { const t = li.querySelector('[role=tooltip], .el-popover'); return t ? clean(t.textContent) : ''; };
    const row = { label, kind: 'select', selected: inp ? inp.value : undefined,
                  options: lis.map(own).filter(Boolean),
                  service_code: g.getAttribute('data-service-code') };
    const dis = lis.filter(li => /is-disabled/.test(li.className));
    if (dis.length) {
      row.disabled = dis.map(own);
      const reasons = [...new Set(dis.map(tip).filter(Boolean))];
      if (reasons.length) row.disabled_reason = reasons.join(' | ');
    }
    rows.push(row);
  }
  // Checkboxes such as the assembly terms agreement.
  for (const cb of root.querySelectorAll('label.el-checkbox')) {
    if (!vis(cb)) continue;
    const txt = clean(cb.innerText) || clean(cb.parentElement ? cb.parentElement.innerText : '');
    rows.push({ label: txt.slice(0, 120) || 'checkbox', kind: 'checkbox', selected: /is-checked/.test(cb.className) });
  }
  return rows;
}
"""

PANEL_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[ \t]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim();
  const cands = [...document.querySelectorAll('div')].filter(d => {
    const t = d.innerText || '';
    return /^\s*Charge Details/.test(t) && t.length < 2500 && d.getBoundingClientRect().height > 0;
  });
  cands.sort((a, b) => (a.innerText.length - b.innerText.length));
  const panel = cands[cands.length - 1];
  if (!panel) return null;
  const radios = [...panel.querySelectorAll('li')].filter(l => l.querySelector('.choose-active-date-icon') && l.getBoundingClientRect().height > 0)
    .map(l => ({ text: clean(l.innerText).replace(/\n/g, ' '), checked: !!l.querySelector('.choose-active-date-icon.on') }))
    .filter(r => r.text);
  return { text: clean(panel.innerText), radios };
}
"""


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9.+±/()]+", "", (s or "").lower())


def read_options(
    page: Any, scope: Optional[str] = None
) -> List[Dict[str, Any]]:
    return page.evaluate(OPTIONS_JS, scope)


def read_panel(page: Any) -> Dict[str, Any]:
    raw = page.evaluate(PANEL_JS) or {}
    text = raw.get("text") or ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    price: Dict[str, Any] = {"lines": lines}
    money = re.compile(r"^[-+]?\$\s?[\d,]+(\.\d+)?$")
    pairs = []
    head = (
        lines[: lines.index("PCB Build Time")]
        if "PCB Build Time" in lines
        else lines
    )
    for i, ln in enumerate(head[:-1]):
        if not money.match(ln) and money.match(head[i + 1]):
            pairs.append((ln, head[i + 1]))
    price["items"] = [{"label": a, "amount": b} for a, b in pairs]
    if "Calculated Price" in lines:
        for ln in lines[lines.index("Calculated Price") + 1 :]:
            if money.match(ln):
                price["web_price"] = ln
                break
    for i, ln in enumerate(lines):
        if ln in ("Weight",) and i + 1 < len(lines):
            price["weight"] = lines[i + 1]
    m = re.search(
        r"Shipping Estimate\s*\n?(\$[\d,.]+)\s*\n?([^\n]+)\n?([^\n]*business days)?",
        text,
    )
    if m:
        price["shipping"] = {
            "amount": m.group(1),
            "method": m.group(2).strip(),
            "eta": (m.group(3) or "").strip(),
        }
    build = [
        r
        for r in raw.get("radios", [])
        if re.search(r"day|hour", r["text"], re.I)
    ]
    if build:
        price["build_time_options"] = build
        sel = [r["text"] for r in build if r["checked"]]
        if sel:
            price["build_time"] = sel[0]
    return price


def detected_board(page: Any) -> Optional[str]:
    try:
        return page.evaluate(
            r"""() => { const m = (document.body.innerText||'').match(/Detected[^\n]*board[^\n]*/i); return m ? m[0].trim() : null; }"""
        )
    except Exception:
        return None


def upload_gerber(
    page: Any, gerber: str, wait_sec: float = 180.0
) -> Dict[str, Any]:
    path = Path(gerber).expanduser().resolve()
    if not path.is_file():
        raise fb.FabError(f"Gerber archive not found: {path}")
    if path.suffix.lower() not in (".zip", ".rar"):
        raise fb.FabError(
            "JLCPCB accepts .zip or .rar Gerber archives only.", file=str(path)
        )
    before = detected_board(page)
    inp = page.locator("input[type=file]").first
    if inp.count() == 0:
        raise fb.FabError(
            "No Gerber file input on the page. Is this the quote page?"
        )
    inp.set_input_files(str(path), timeout=15000)
    collect: Dict[str, Any] = {}
    # The page shows progress then the parsed result. Wait for "Detected".
    deadline = time.time() + wait_sec
    idle: Dict[str, Any] = {}
    while time.time() < deadline:
        idle = fb.wait_idle(
            page,
            timeout_sec=max(5.0, deadline - time.time()),
            settle_sec=1.5,
            collect=collect,
        )
        det = detected_board(page)
        if det and (det != before or not before):
            break
        time.sleep(1)
    return {
        "file": str(path),
        "size_bytes": path.stat().st_size,
        "detected": detected_board(page),
        "idle": fb._compact_idle(idle),
    }


def _set_select_row(
    page: Any, label: str, value: str
) -> Optional[Dict[str, Any]]:
    """Advanced PCBA options rendered as Element UI selects in [data-service-code] rows."""
    rows = page.locator("[data-service-code]").filter(
        has=page.locator(
            "span", has_text=re.compile("^" + re.escape(label), re.I)
        )
    )
    for i in range(rows.count()):
        row = rows.nth(i)
        if not fb._safe_visible(row):
            continue
        sel = row.locator(".el-select").first
        sel.click(timeout=5000)
        time.sleep(0.4)
        items = page.locator("li.el-select-dropdown__item")
        avail = []
        for j in range(items.count()):
            li = items.nth(j)
            if not fb._safe_visible(li):
                continue
            t = (li.inner_text() or "").strip()
            avail.append(t)
            if _norm(t) == _norm(value) or _norm(t).startswith(_norm(value)):
                li.click(timeout=5000)
                fb.wait_idle(page, timeout_sec=10, settle_sec=0.6)
                return {"label": label, "set": t}
        page.keyboard.press("Escape")
        raise fb.FabError(
            f"'{value}' is not an option for {label}.", options=avail
        )
    return None


def find_row(
    page: Any, label: str, scope: Optional[str] = None
) -> Tuple[Any, str]:
    rows = read_options(page, scope)
    want = _norm(label)
    exact = [r for r in rows if _norm(r["label"]) == want]
    pref = [r for r in rows if _norm(r["label"]).startswith(want)]
    sub = [r for r in rows if want in _norm(r["label"])]
    match = (exact or pref or sub or [{}])[0]
    if not match:
        raise fb.FabError(
            f"No option row labelled '{label}'.",
            available=[r["label"] for r in rows],
        )
    # Locate the DOM group again by label text.
    groups = page.locator(
        ".main-btn-group, .el-form-item, .smt-form-item"
    ).filter(has=page.locator("label", has_text=match["label"]))
    n = groups.count()
    for i in range(n):
        g = groups.nth(i)
        if fb._safe_visible(g):
            return g, match["label"]
    raise fb.FabError(f"Option row '{match['label']}' is not visible.")


def set_option(
    page: Any, label: str, value: str, scope: Optional[str] = None
) -> Dict[str, Any]:
    if label.lower() in ("pcb assembly", "pcba", "assembly"):
        return set_pcba_enabled(
            page,
            value.lower() in ("on", "yes", "true", "1", "enable", "enabled"),
        )
    rows = {r["label"]: r for r in read_options(page, scope)}
    match = next(
        (r for k, r in rows.items() if _norm(k).startswith(_norm(label))), None
    )
    if match and match.get("kind") == "select":
        out = _set_select_row(page, match["label"], value)
        if out:
            return out
    if match and match.get("kind") == "checkbox":
        want_on = value.lower() in ("on", "yes", "true", "1", "checked")
        if bool(match.get("selected")) != want_on:
            page.locator(
                "label.el-checkbox", has_text=match["label"][:40]
            ).first.click(timeout=5000)
        return {"label": match["label"], "set": want_on}
    group, real_label = find_row(page, label, scope)
    want = _norm(value)
    # 1) Popover quantity pickers (PCB Qty, PCBA Qty).
    ref = group.locator(
        ".qtySelect, .el-popover__reference-wrapper:not(label *)"
    ).first
    buttons = group.locator("button, a.btn, a[type=button]")
    vis_buttons = [
        buttons.nth(i)
        for i in range(buttons.count())
        if fb._safe_visible(buttons.nth(i))
    ]
    if not vis_buttons and ref.count() and fb._safe_visible(ref):
        ref.click(timeout=5000)
        time.sleep(0.4)
        opts = page.locator(
            ".el-popover .qty-select-list button, .el-popover:visible button"
        )
        found = None
        avail = []
        for i in range(opts.count()):
            b = opts.nth(i)
            if not fb._safe_visible(b):
                continue
            t = (b.inner_text() or "").strip()
            avail.append(t)
            if _norm(t) == want:
                found = b
        if not found:
            page.keyboard.press("Escape")
            raise fb.FabError(
                f"'{value}' is not an allowed value for {real_label}.",
                allowed=avail,
            )
        found.click(timeout=5000)
        fb.wait_idle(page, timeout_sec=15, settle_sec=0.8)
        return {"label": real_label, "set": value}
    # 2) Button groups.
    if vis_buttons:
        choices = []
        target = None
        for b in vis_buttons:
            t = (b.inner_text() or "").strip()
            choices.append(t)
            if _norm(t) == want or (
                target is None and _norm(t).startswith(want) and want
            ):
                target = target or b
                if _norm(t) == want:
                    target = b
                    break
        if target is None:
            raise fb.FabError(
                f"'{value}' is not an option for {real_label}.",
                options=choices,
            )
        if target.is_disabled():
            raise fb.FabError(
                f"'{value}' is disabled for {real_label} with the current combination of options.",
                options=choices,
            )
        fb.guard_click(target)
        target.click(timeout=5000)
        idle = fb.wait_idle(page, timeout_sec=15, settle_sec=0.8)
        return {
            "label": real_label,
            "set": value,
            "idle": fb._compact_idle(idle),
        }
    # 3) Text inputs (Dimensions, remarks...).
    inputs = group.locator("input:not([type=hidden]):not([type=file])")
    if inputs.count():
        vals = [v.strip() for v in value.split(",")]
        for i, v in enumerate(vals[: inputs.count()]):
            inputs.nth(i).fill(v)
            inputs.nth(i).dispatch_event("change")
            inputs.nth(i).dispatch_event("blur")
        fb.wait_idle(page, timeout_sec=10, settle_sec=0.6)
        return {"label": real_label, "set": vals}
    raise fb.FabError(
        f"Don't know how to set '{real_label}'. Use snapshot + click."
    )


def pcba_enabled(page: Any) -> Optional[bool]:
    return page.evaluate(
        r"""() => { const s = document.querySelector('#smtQuoteRef .switch-btn'); return s ? /(^|\s)on(\s|$)/.test(s.className) : null; }"""
    )


def set_pcba_enabled(page: Any, on: bool) -> Dict[str, Any]:
    if pcba_enabled(page) != on:
        page.locator("#smtQuoteRef .switch-box").first.click(timeout=5000)
        fb.wait_idle(page, timeout_sec=15, settle_sec=0.8)
    return {"label": "PCB Assembly", "set": pcba_enabled(page)}


def select_build_time(page: Any, choice: str) -> Dict[str, Any]:
    want = _norm(choice)
    labels = page.locator("li:has(.choose-active-date-icon)")
    hits = []
    for i in range(labels.count()):
        lab = labels.nth(i)
        if not fb._safe_visible(lab):
            continue
        t = (lab.inner_text() or "").strip()
        hits.append(t)
        if _norm(t).startswith(want):
            lab.locator(".choose-active-date-icon").click(timeout=5000)
            fb.wait_idle(page, timeout_sec=15, settle_sec=0.8)
            return {"build_time": t}
    raise fb.FabError(
        f"No build-time option starting with '{choice}'.", options=hits
    )


def wait_price_stable(
    page: Any, timeout_sec: float = 20.0, stable_sec: float = 2.0
) -> Optional[str]:
    """Prices recalculate asynchronously; wait until the web price stops changing."""
    deadline = time.time() + timeout_sec
    last, since = None, time.time()
    while time.time() < deadline:
        try:
            cur = read_panel(page).get("web_price")
        except Exception:
            cur = None
        if cur != last:
            last, since = cur, time.time()
        elif cur is not None and time.time() - since >= stable_sec:
            return cur
        time.sleep(0.5)
    return last


def summarize_quote(page: Any) -> Dict[str, Any]:
    wait_price_stable(page)
    rows = read_options(page, None)
    pcb_rows: List[Dict[str, Any]] = []
    pcba_rows: List[Dict[str, Any]] = []
    in_pcba = False
    pcba_first = {"PCBA Type", "Assembly Side", "PCBA Qty"}
    for r in rows:
        if r["label"] in pcba_first:
            in_pcba = True
        (pcba_rows if in_pcba else pcb_rows).append(r)
    pcba_on = pcba_enabled(page)
    return {
        "detected": detected_board(page),
        "pcb_options": pcb_rows,
        "pcba_enabled": pcba_on,
        "pcba_options": pcba_rows,
        "price": read_panel(page),
    }
