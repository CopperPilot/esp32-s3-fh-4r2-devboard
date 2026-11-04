#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""JLCDFM (jlcdfm.com/viewer): run DFM, read results, drill into issues."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import fab_browser as fb
import kicad_locate as kl

DFM_URL_RX = r"jlcdfm\.com/viewer"
VIEWER_URL_RX = r"gerberview"

SUMMARY_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/\s+/g, ' ').trim();
  const out = [];
  let section = null;
  const nodes = document.querySelectorAll('h1,h2,h3,h4,div,span,td,th,tr,[role=row]');
  for (const n of nodes) {
    const t = clean(n.innerText);
    if (n.children.length <= 1 && /layer analysis$/i.test(t) && t.length < 40) { section = t; continue; }
    if ((n.tagName === 'TR' || n.getAttribute('role') === 'row')) {
      const cells = [...n.querySelectorAll('td,[role=cell]')].map(c => clean(c.innerText));
      if (cells.length >= 2 && /^\d+,\s*\d+,\s*\d+$/.test(cells[1])) {
        const [danger, warning, good] = cells[1].split(',').map(x => parseInt(x));
        out.push({ section, check: cells[0], danger, warning, good });
      } else if (cells.length >= 2 && /unanalyzed/i.test(cells[1])) {
        out.push({ section, check: cells[0], unanalyzed: true });
      }
    }
  }
  const seen = new Set();
  return out.filter(r => { const k = r.section + '|' + r.check + '|' + r.danger + r.warning + r.good; if (seen.has(k)) return false; seen.add(k); return true; });
}
"""

MODAL_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[\s\u00a0]+/g, ' ').trim();
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 50 && r.height > 50 && getComputedStyle(el).visibility !== 'hidden'; };
  const m = [...document.querySelectorAll('[class*=eda-modal-container]')].filter(vis)
    .find(e => /analysis\s*>/.test(e.innerText || ''));
  if (!m) return null;
  const title = clean((m.querySelector('[class*=modal-title], [class*=modal-header]') || m).innerText.split('\n')[0]);
  const tables = [...m.querySelectorAll('table')];
  const layers = [];
  const items = [];
  for (const tb of tables) {
    for (const tr of tb.querySelectorAll('tr')) {
      const cells = [...tr.querySelectorAll('td')].map(td => clean(td.innerText));
      if (!cells.length) continue;
      if (/^\d+$/.test(cells[0]) && cells.length >= 3) {
        items.push({ no: +cells[0], level: cells[1], value: cells[2], object1: cells[3], object2: cells[4],
                     selected: /active|selected|cur|current/.test(tr.className) });
      }
    }
  }
  for (const li of m.querySelectorAll('[class*=list-item]')) {
    const t = clean(li.innerText);
    const mm = t.match(/^(.*?)\s*\((\d+),\s*(\d+),\s*(\d+)\)$/);
    if (mm) layers.push({ layer: mm[1], file: li.getAttribute('title') || undefined, danger: +mm[2], warning: +mm[3], good: +mm[4],
                          selected: /active/.test(li.className) });
  }
  const text = m.innerText || '';
  const desc = (text.split(/First\s*Previous\s*Next\s*Last\s*All/)[1] || '').split(/Alert value/)[0];
  const alert = (text.split(/Alert value[：:]/)[1] || '').replace(/Danger|Warning|Good/g, ' ');
  return { title, layers, items, description: clean(desc), alert_thresholds: clean(alert) };
}
"""


def _dfm_page(sess: fb.Session) -> Any:
    return fb.find_page(sess, DFM_URL_RX)


def read_summary(page: Any) -> Dict[str, Any]:
    rows = page.evaluate(SUMMARY_JS)
    analyzed = [r for r in rows if not r.get("unanalyzed")]
    tot = {
        "danger": sum(r.get("danger", 0) for r in analyzed),
        "warning": sum(r.get("warning", 0) for r in analyzed),
        "checks": len(rows),
        "unanalyzed": len(rows) - len(analyzed),
    }
    problems = sorted(
        [r for r in analyzed if r.get("danger") or r.get("warning")],
        key=lambda r: (-r.get("danger", 0), -r.get("warning", 0)),
    )
    return {"totals": tot, "problems": problems, "all_checks": rows}


def _await_page(
    sess: fb.Session, url_rx: str, timeout_sec: float, what: str
) -> Any:
    """JLC opens these either as a new tab or by navigating the current one."""
    rx = re.compile(url_rx)
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        pages = sess.pages()
        hits = [p for p in pages if rx.search(p.url or "")]
        if hits:
            return hits[-1]
        # time.sleep would not pump Playwright's event loop, so new tabs and URL changes would never show up.
        pages[0].wait_for_timeout(500)
    raise fb.FabError(
        f"{what} did not open within {int(timeout_sec)}s.",
        tabs=fb.list_tabs(sess),
    )


def run_dfm(
    sess: fb.Session, quote_page: Optional[Any], timeout_sec: float = 240
) -> Any:
    """From the quote page: Gerber Viewer -> DFM Check -> jlcdfm 'DFM check'. Returns the DFM page."""
    dfm = None
    try:
        dfm = _dfm_page(sess)
    except fb.FabError:
        dfm = None
    if dfm is None:
        if quote_page is None:
            raise fb.FabError(
                "No quote page with an uploaded Gerber. Run `quote-upload` first."
            )
        viewer = None
        try:
            viewer = fb.find_page(sess, VIEWER_URL_RX)
        except fb.FabError:
            quote_page.get_by_text("Gerber Viewer", exact=True).first.click(
                timeout=10000
            )
            viewer = _await_page(sess, VIEWER_URL_RX, 60, "Gerber Viewer")
        viewer.wait_for_load_state("domcontentloaded", timeout=60000)
        btn = viewer.get_by_role("button", name="DFM Check")
        btn.first.wait_for(state="visible", timeout=60000)
        btn.first.click(timeout=10000)
        dfm = _await_page(sess, DFM_URL_RX, 120, "JLCDFM viewer")
        dfm.wait_for_load_state("domcontentloaded", timeout=90000)
    dfm.bring_to_front()
    fb.mark_active(dfm.url)
    run_btn = dfm.get_by_role("button", name="DFM check", exact=True)
    run_btn.first.wait_for(state="visible", timeout=120000)
    fb.wait_idle(dfm, timeout_sec=30, settle_sec=1.0)
    run_btn.first.click(timeout=10000)
    # Done when no check is still "Unanalyzed" (results table filled in).
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        time.sleep(2.0)
        rows = dfm.evaluate(SUMMARY_JS)
        if rows and not any(r.get("unanalyzed") for r in rows):
            break
    fb.wait_idle(dfm, timeout_sec=20, settle_sec=1.5)
    return dfm


def read_modal(page: Any) -> Optional[Dict[str, Any]]:
    return page.evaluate(MODAL_JS)


def open_details(page: Any, check: str) -> Dict[str, Any]:
    want = check.strip().lower()
    cur = read_modal(page)
    if cur:
        if cur["title"].lower().split(">")[-1].strip().startswith(want):
            return cur
        close_modal(page)
        time.sleep(0.5)
    ok = page.evaluate(
        r"""(want) => {
          const rows = [...document.querySelectorAll('tr,[role=row]')];
          const clean = (t) => (t || '').replace(/\s+/g, ' ').trim().toLowerCase();
          const row = rows.find(r => { const c = r.querySelector('td,[role=cell]'); return c && clean(c.innerText) === want; })
                   || rows.find(r => { const c = r.querySelector('td,[role=cell]'); return c && clean(c.innerText).startsWith(want); });
          if (!row) return 'nocheck';
          const b = [...row.querySelectorAll('button')].find(x => /details/i.test(x.innerText));
          if (!b) return 'nobutton';
          if (b.disabled) return 'disabled';
          b.click(); return 'ok';
        }""",
        want,
    )
    if ok != "ok":
        raise fb.FabError(
            f"Cannot open details for '{check}' ({ok}). Use names from `dfm-summary`; checks with 0/0/0 have no details."
        )
    time.sleep(1.0)
    m = read_modal(page)
    if not m:
        raise fb.FabError("Details dialog did not open.")
    return m


def close_modal(page: Any) -> None:
    page.evaluate(
        r"""() => { const m = [...document.querySelectorAll('[class*=eda-modal-container]')].find(e => /analysis\s*>/.test(e.innerText||'') && e.getBoundingClientRect().width > 50);
                   if (!m) return; const hdr = m.querySelector('[class*=modal-header]') || m;
                   const x = hdr.querySelector('[class*=close], [class*=Close]') || [...hdr.querySelectorAll('svg, i, span, button')].pop();
                   if (x) x.dispatchEvent(new MouseEvent('click', {bubbles: true})); }"""
    )
    time.sleep(0.4)


def _click_in_modal(page: Any, text_rx: str, kind: str = "tr") -> bool:
    """Real mouse click on the first element in the analysis dialog matching text_rx."""
    modal = page.locator("[class*=eda-modal-container]").filter(
        has_text=re.compile(r"analysis\s*>")
    )
    cands = modal.locator(kind)
    rx = re.compile(text_rx, re.I)
    for i in range(cands.count()):
        el = cands.nth(i)
        try:
            txt = re.sub(
                r"[\s\u00a0]+", " ", el.inner_text(timeout=2000)
            ).strip()
        except Exception:
            continue
        if rx.search(txt):
            target = (
                el.locator("td").first
                if kind == "tr" and el.locator("td").count()
                else el
            )
            target.scroll_into_view_if_needed(timeout=3000)
            target.click(timeout=5000)
            return True
    return False


def _canvas_box(page: Any) -> Optional[Dict[str, float]]:
    return page.evaluate(
        r"""() => { const cs = [...document.querySelectorAll('canvas')].map(c => c.getBoundingClientRect()).filter(r => r.width > 200 && r.height > 200);
                   cs.sort((a,b) => b.width*b.height - a.width*a.height); const r = cs[0];
                   return r ? {x: r.x, y: r.y, width: r.width, height: r.height} : null; }"""
    )


def _cursor_xy(page: Any) -> Optional[Dict[str, float]]:
    txt = page.evaluate(
        r"""() => { const m = (document.body.innerText||'').match(/X:\s*(-?[\d.]+)\s*mm\s*Y:\s*(-?[\d.]+)\s*mm/); return m ? [m[1], m[2]] : null; }"""
    )
    if not txt:
        return None
    return {"x_mm": float(txt[0]), "y_mm": float(txt[1])}


def _set_modal_hidden(page: Any, hidden: bool) -> None:
    """Hide the analysis dialog for a clean board screenshot. Tag the host so restore
    works (innerText of a hidden element is empty, so it can't be found by text).
    """
    page.evaluate(
        r"""(hidden) => {
          if (hidden) {
            for (const e of document.querySelectorAll('[class*=eda-modal-container]')) {
              if (/analysis\s*>/.test(e.innerText||'')) { e.parentElement.setAttribute('data-cp-hidden', '1'); e.parentElement.style.visibility = 'hidden'; }
            }
          } else {
            for (const h of document.querySelectorAll('[data-cp-hidden]')) { h.style.visibility = ''; h.removeAttribute('data-cp-hidden'); }
          }
        }""",
        hidden,
    )


def item_location_and_shot(page: Any, out: Path) -> Dict[str, Any]:
    """After an item is selected (auto-fit centres it), read board XY at canvas centre and screenshot."""
    time.sleep(1.2)
    box = _canvas_box(page)
    info: Dict[str, Any] = {}
    if not box:
        return info
    _set_modal_hidden(page, True)
    try:
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        # The readout only updates on mousemove and the auto-fit pan can still be
        # animating, so sample until three consecutive reads agree.
        loc, prev, stable = None, None, 0
        deadline = time.time() + 6.0
        while time.time() < deadline:
            page.mouse.move(cx + 1, cy)
            page.mouse.move(cx, cy)
            time.sleep(0.35)
            loc = _cursor_xy(page)
            same = (
                loc
                and prev
                and abs(loc["x_mm"] - prev["x_mm"]) < 0.02
                and abs(loc["y_mm"] - prev["y_mm"]) < 0.02
            )
            stable = stable + 1 if same else 0
            if stable >= 2:
                break
            prev = loc
        if loc:
            info["board_xy_mm"] = loc
        clip = {
            "x": max(box["x"], cx - 300),
            "y": max(box["y"], cy - 220),
            "width": min(600, box["width"]),
            "height": min(440, box["height"]),
        }
        page.evaluate(
            r"""([x, y]) => { const d = document.createElement('div'); d.id = 'cp-dfm-marker';
                 Object.assign(d.style, {position: 'fixed', left: (x - 22) + 'px', top: (y - 22) + 'px', width: '44px', height: '44px',
                   border: '3px solid #ff2d55', borderRadius: '50%', zIndex: 2147483647, pointerEvents: 'none', boxShadow: '0 0 0 2px #fff'});
                 document.body.appendChild(d); }""",
            [cx, cy],
        )
        info["screenshot"] = fb.screenshot(page, out, clip=clip)
    finally:
        page.evaluate(
            "() => document.getElementById('cp-dfm-marker')?.remove()"
        )
        _set_modal_hidden(page, False)
    return info


def details(
    page: Any,
    check: str,
    shots_dir: Path,
    levels: List[str],
    max_items: int = 8,
    shots: bool = True,
    pcb_path: Optional[Path] = None,
) -> Dict[str, Any]:
    m = open_details(page, check)
    result: Dict[str, Any] = {
        "check": m["title"],
        "description": m["description"],
        "alert_thresholds": m["alert_thresholds"],
        "layers": [],
    }
    want_levels = {lvl.lower() for lvl in levels}
    budget = max_items
    for layer in list(m["layers"]):
        if not any(layer.get(lvl, 0) for lvl in want_levels):
            result["layers"].append(
                {
                    **layer,
                    "items": [],
                    "skipped": "no items at requested levels",
                }
            )
            continue
        _click_in_modal(
            page,
            "^" + re.escape(layer["layer"]) + r"\s*\(",
            "[class*=list-item]",
        )
        time.sleep(0.8)
        cur = read_modal(page) or {}
        items = [
            it
            for it in cur.get("items", [])
            if it["level"].lower() in want_levels
        ]
        layer_out = {**layer, "items": []}
        for it in items:
            entry = dict(it)
            entry.pop("selected", None)
            if budget > 0 and shots:
                _click_in_modal(page, rf"^{it['no']}\s", "tr")
                slug = re.sub(
                    r"[^a-z0-9]+",
                    "-",
                    f"{check}-{layer['layer']}-{it['no']}".lower(),
                ).strip("-")
                entry.update(
                    item_location_and_shot(
                        page, shots_dir / f"{fb.stamp()}-dfm-{slug}.png"
                    )
                )
                if pcb_path and entry.get("board_xy_mm"):
                    try:
                        xy = entry["board_xy_mm"]
                        entry["kicad"] = kl.locate(
                            pcb_path, xy["x_mm"], xy["y_mm"]
                        )
                    except Exception as exc:  # parsing is best effort
                        entry["kicad"] = {"error": str(exc)}
                budget -= 1
            layer_out["items"].append(entry)
        result["layers"].append(layer_out)
    close_modal(page)
    if budget <= 0:
        result["note"] = (
            f"Screenshots capped at {max_items} items; raise --max-items to see more."
        )
    return result


def save_report(
    project_dir: Path, site: str, summary: Dict[str, Any], dfm_url: str
) -> str:
    d = fb.artifacts_dir(project_dir, site) / "dfm"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{fb.stamp()}-summary.json"
    f.write_text(json.dumps({"url": dfm_url, **summary}, indent=2))
    (d / "latest-summary.json").write_text(
        json.dumps({"url": dfm_url, **summary}, indent=2)
    )
    return str(f)


def diff_summaries(
    prev: Dict[str, Any], cur: Dict[str, Any]
) -> List[Dict[str, Any]]:
    def key(r: Dict[str, Any]) -> str:
        return f"{r.get('section')}|{r.get('check')}"

    p = {key(r): r for r in prev.get("all_checks", [])}
    out = []
    for r in cur.get("all_checks", []):
        o = p.get(key(r))
        if not o:
            continue
        dd = (
            r.get("danger", 0) - o.get("danger", 0),
            r.get("warning", 0) - o.get("warning", 0),
        )
        if dd != (0, 0):
            out.append(
                {
                    "check": r.get("check"),
                    "danger": f"{o.get('danger',0)}→{r.get('danger',0)}",
                    "warning": f"{o.get('warning',0)}→{r.get('warning',0)}",
                }
            )
    return out
