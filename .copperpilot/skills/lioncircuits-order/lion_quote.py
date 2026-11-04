#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""Lion Circuits quotation wizard: Fabrication -> Assembly -> Procurement -> Summary."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

import fab_browser as fb

BASE = "https://order.lioncircuits.com"
STEPS = ["Fabrication", "Assembly", "Procurement", "Summary"]
TABS = [
    "QUOTATION",
    "PROJECT DETAILS",
    "PCB IMAGE",
    "BOM VIEWER",
    "DFM FEEDBACK",
    "HELP",
    "TEAM MEMBERS",
    "UPDATE DESIGN",
]
BUILD_TIME_VALUES = {
    "none": "5-6 Days (standard)",
    "rush": "4-5 Days",
    "super_rush": "2-3 Days (flash)",
    "flash": "1-2 Days (flash)",
}

OPTIONS_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[\s ]+/g, ' ').trim();
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 1 && r.height > 1; };
  const rows = [];
  for (const g of document.querySelectorAll('[class*=spec_container], [class*=generic_spec]')) {
    if (!vis(g)) continue;
    const h = g.querySelector('h4, h5, [class*=spec_header], [class*=header]');
    const label = clean(h ? h.innerText : '');
    if (!label || rows.some(r => r.label === label)) continue;
    const opts = [...g.querySelectorAll('[class*=spec_option]')].filter(o => !/spec_options|option_text/.test(o.className) && vis(o));
    const row = { label };
    if (opts.length) {
      row.options = opts.map(o => clean(o.innerText));
      const sel = opts.filter(o => /selected/.test(o.className)).map(o => clean(o.innerText));
      if (sel.length) row.selected = sel.length === 1 ? sel[0] : sel;
      const dis = opts.filter(o => /not-allowed/.test(o.getAttribute('style') || '') || Number(getComputedStyle(o).opacity) < 0.6).map(o => clean(o.innerText));
      if (dis.length) row.disabled = dis;
    }
    const inp = g.querySelector('input:not([type=hidden]):not([type=file])');
    if (inp && !opts.length) row.selected = inp.value;
    if (inp && opts.length === 0) row.kind = 'number';
    if (!opts.length && !inp) { const v = clean((g.querySelector('[class*=spec_options]') || {}).innerText); if (v) row.selected = v; }
    // Icon-button rows (XY File Top/Bottom/Combined) on the assembly step.
    if (!opts.length && !inp) {
      const btns = [...g.querySelectorAll('button, [role=button], [class*=icon_btn], [class*=xy]')].filter(vis).map(b => clean(b.innerText)).filter(Boolean);
      if (btns.length) row.options = [...new Set(btns)];
    }
    rows.push(row);
  }
  return rows;
}
"""

PANEL_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[ \t ]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim();
  const h = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && (e.innerText || '').trim() === 'Charge Details');
  if (!h) return null;
  let p = h; for (let i = 0; i < 2; i++) p = p.parentElement;
  const radios = [...p.querySelectorAll('input[type=radio]')].map(i => ({ value: i.value, checked: i.checked, disabled: i.disabled }));
  const banners = [...p.querySelectorAll('div, p')].filter(e => e.children.length === 0 && /only|not available|max|min/i.test(e.innerText || '') && (e.innerText || '').length < 200)
    .map(e => clean(e.innerText));
  return { text: clean(p.innerText), radios, banners: [...new Set(banners)] };
}
"""


def current_step(page: Any) -> Optional[str]:
    return page.evaluate(
        r"""() => { const a = document.querySelector('[class*=Quotationbar_active]'); return a ? (a.innerText || '').replace(/^\d+\s*/, '').trim() : null; }"""
    )


def step_states(page: Any) -> List[Dict[str, Any]]:
    return page.evaluate(
        r"""() => [...document.querySelectorAll('[class*=Quotationbar_step]')].map(s => ({ step: (s.innerText||'').replace(/^\d+\s*/, '').trim(),
              active: /active/.test(s.className), done: !!s.querySelector('svg, [class*=done], [class*=check]') && !/^\d/.test((s.innerText||'').trim()) }))"""
    )


def read_options(page: Any) -> List[Dict[str, Any]]:
    return page.evaluate(OPTIONS_JS)


def read_panel(page: Any) -> Dict[str, Any]:
    raw = page.evaluate(PANEL_JS) or {}
    text = raw.get("text", "")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    money = re.compile(r"^₹\s?[\d,]+(\.\d+)?$|^\$[\d,.]+$")
    out: Dict[str, Any] = {"lines": lines}
    items = []
    for i, ln in enumerate(lines[:-1]):
        if not money.match(ln) and (
            money.match(lines[i + 1])
            or re.match(r"^₹[\d,.]+\s*[xX]\s*\d+$", lines[i + 1])
        ):
            items.append({"label": ln, "amount": lines[i + 1]})
    out["items"] = items
    radios = raw.get("radios") or []
    if radios:
        out["build_time"] = [
            {
                "value": r["value"],
                "label": BUILD_TIME_VALUES.get(r["value"], r["value"]),
                "selected": r["checked"],
                "disabled": r["disabled"],
            }
            for r in radios
        ]
    if raw.get("banners"):
        out["constraints"] = raw["banners"]
    return out


def ensure_project_page(
    page: Any, pid: Optional[str], timeout_sec: float = 25
) -> Optional[str]:
    """Lion sometimes bounces to /viewProjects or renders Fabrication rows late.
    Re-open the project if needed and wait until the step's options are rendered.
    Returns a note when it had to recover."""
    note = None
    if pid and f"/projectdetails/{pid}" not in (page.url or ""):
        note = f"Tab was on {page.url}; reopened project {pid}."
        page.goto(
            f"{BASE}/projectdetails/{pid}/quotation",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        fb.wait_idle(page, timeout_sec=30, settle_sec=1.5)
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if current_step(page) != "Fabrication" or len(read_options(page)) >= 5:
            break
        time.sleep(0.5)
    return note


def set_option(page: Any, label: str, value: str) -> Dict[str, Any]:
    rows = read_options(page)
    want_l = label.strip().lower()
    row = next(
        (r for r in rows if r["label"].lower() == want_l), None
    ) or next((r for r in rows if r["label"].lower().startswith(want_l)), None)
    if not row:
        raise fb.FabError(
            f"No option '{label}' on this step.",
            available=[r["label"] for r in rows],
        )
    group = (
        page.locator("[class*=spec_container], [class*=generic_spec]")
        .filter(
            has=page.locator(
                "h4, h5, [class*=spec_header], [class*=header]",
                has_text=re.compile("^" + re.escape(row["label"]) + "$"),
            )
        )
        .first
    )
    if row.get("options"):
        want = value.strip().lower()
        opts = row["options"]
        hit = next((o for o in opts if o.lower() == want), None) or next(
            (o for o in opts if o.lower().startswith(want)), None
        )
        if not hit:
            raise fb.FabError(
                f"'{value}' is not an option for {row['label']}.", options=opts
            )
        if hit in (row.get("disabled") or []):
            raise fb.FabError(
                f"'{hit}' is disabled for {row['label']} with the current choices (see panel constraints).",
                options=opts,
            )
        el = group.locator(
            "[class*=spec_option]",
            has_text=re.compile("^\\s*" + re.escape(hit) + "\\s*$"),
        ).last
        el.click(timeout=5000)
    else:
        inp = group.locator("input:not([type=hidden]):not([type=file])").first
        inp.click(timeout=5000)
        inp.fill(str(value))
        inp.press("Tab")
    collect: Dict[str, Any] = {}
    fb.wait_idle(page, timeout_sec=20, settle_sec=1.0, collect=collect)
    now = next(
        (r for r in read_options(page) if r["label"] == row["label"]), {}
    )
    return {
        "label": row["label"],
        "requested": value,
        "now": now.get("selected"),
        "toasts": collect.get("toasts_seen", []),
    }


def set_build_time(page: Any, choice: str) -> Dict[str, Any]:
    key = choice.strip().lower().replace(" ", "_").replace("-", "_")
    alias = {
        "5_6": "none",
        "standard": "none",
        "4_5": "rush",
        "2_3": "super_rush",
        "1_2": "flash",
    }
    for k, v in alias.items():
        if key.startswith(k):
            key = v
    if key not in BUILD_TIME_VALUES:
        raise fb.FabError(
            f"Unknown build time '{choice}'.",
            choices=list(BUILD_TIME_VALUES.values()),
        )
    radio = page.locator(f"input[type=radio][value='{key}']").first
    if radio.is_disabled():
        raise fb.FabError(f"Build time {BUILD_TIME_VALUES[key]} is disabled.")
    radio.check(force=True, timeout=5000)
    fb.wait_idle(page, timeout_sec=20, settle_sec=1.0)
    return {"build_time": BUILD_TIME_VALUES[key], "panel": read_panel(page)}


def click_action(
    page: Any, name_rx: str, wait_sec: float = 120
) -> Dict[str, Any]:
    btn = page.get_by_role("button", name=re.compile(name_rx, re.I))
    target = None
    for i in range(btn.count()):
        if fb._safe_visible(btn.nth(i)):
            target = btn.nth(i)
            break
    if target is None:
        # Some actions are styled divs/spans.
        alt = page.get_by_text(re.compile(name_rx, re.I))
        for i in range(alt.count()):
            if fb._safe_visible(alt.nth(i)):
                target = alt.nth(i)
                break
    if target is None:
        raise fb.FabError(f"No visible control matching /{name_rx}/.")
    label = fb.guard_click(target)
    if target.is_disabled() if hasattr(target, "is_disabled") else False:
        raise fb.FabError(
            f"'{label}' is disabled (a required input is missing on this step)."
        )
    target.click(timeout=10000)
    time.sleep(1.0)
    collect: Dict[str, Any] = {}
    fb.wait_idle(page, timeout_sec=wait_sec, settle_sec=1.5, collect=collect)
    return {
        "clicked": label,
        "toasts": collect.get("toasts_seen", []),
        "busy_seen": collect.get("busy_seen"),
        "observations": fb.observe(page),
    }


def open_tab(page: Any, tab: str) -> Dict[str, Any]:
    hit = next(
        (t for t in TABS if t.lower().startswith(tab.strip().lower())), None
    )
    if not hit:
        raise fb.FabError(f"Unknown project tab '{tab}'.", tabs=TABS)
    page.get_by_text(
        re.compile(r"^\s*" + re.escape(hit) + r"\s*$", re.I)
    ).first.click(timeout=10000)
    fb.wait_idle(page, timeout_sec=60, settle_sec=1.5)
    return {"tab": hit, "url": page.url}


def summarize(page: Any) -> Dict[str, Any]:
    head = page.evaluate(
        r"""() => { const t = document.body.innerText || ''; const n = t.match(/Project Name\s*:\s*\n?\s*([^\n]+)/); const p = t.match(/PID\s*:\s*(\d+)/);
                   return { project_name: n ? n[1].trim() : null, pid: p ? p[1] : null }; }"""
    )
    return {
        **head,
        "step": current_step(page),
        "options": read_options(page),
        "charges": read_panel(page),
    }
