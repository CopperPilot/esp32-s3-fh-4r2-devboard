#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""Lion Circuits projects: list, create (Gerber upload), open."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import fab_browser as fb

BASE = "https://order.lioncircuits.com"
PROJECTS_URL = f"{BASE}/viewProjects"


def billing(page: Any) -> Dict[str, Any]:
    return page.evaluate(
        r"""() => { const t = document.body.innerText || ''; const m = t.match(/BILLING ID\s*\n\s*(\d{6,})/i);
                   return { selected_billing_id: m ? m[1] : null }; }"""
    )


def list_projects(page: Any) -> List[Dict[str, Any]]:
    if "viewProjects" not in page.url:
        page.goto(PROJECTS_URL, wait_until="domcontentloaded", timeout=60000)
    try:
        page.locator("table tr").nth(1).wait_for(timeout=20000)
    except Exception:
        pass
    fb.wait_idle(page, timeout_sec=20)
    rows = fb.extract_tables(page, "table", 200)
    out = []
    for t in rows:
        for r in t["rows"]:
            if isinstance(r, dict) and r.get("PID"):
                out.append({k: v for k, v in r.items() if k and k != "col0"})
    return out


def create_project(
    page: Any,
    name: str,
    gerber: str,
    layers: Optional[int],
    description: Optional[str],
    wait_sec: float = 180,
) -> Dict[str, Any]:
    path = Path(gerber)
    if not path.is_file():
        raise fb.FabError(f"Gerber archive not found: {path}")
    projects_before = list_projects(page)
    page.get_by_role(
        "button", name=re.compile(r"^\s*New Project\s*$", re.I)
    ).first.click(timeout=10000)
    dlg = page.locator("[role=dialog]").first
    dlg.wait_for(timeout=10000)
    dlg.get_by_role("textbox", name=re.compile("Project Name", re.I)).fill(
        name
    )
    if description:
        dlg.get_by_role("textbox", name=re.compile("Description", re.I)).fill(
            description
        )
    if layers:
        combo = dlg.get_by_role("combobox").first
        if (combo.inner_text() or "").strip() != str(layers):
            combo.click(timeout=5000)
            page.get_by_role(
                "option", name=re.compile(rf"^\s*{layers}\s*$")
            ).first.click(timeout=5000)
    dlg.locator("input[type=file]").set_input_files(str(path), timeout=15000)
    # Wait for the TOP/BOTTOM preview (or an error).
    try:
        dlg.get_by_text(re.compile(r"^\s*TOP\s*$")).first.wait_for(
            timeout=60000
        )
    except Exception:
        pass
    preview_shot = None
    try:
        preview_shot = fb.screenshot(page, Path(page.context._cp_shots) / f"{fb.stamp()}-lion-preview.png", selector="[role=dialog]")  # type: ignore[attr-defined]
    except Exception:
        pass
    btn = dlg.get_by_role("button", name=re.compile(r"^\s*Proceed\s*$", re.I))
    if btn.is_disabled():
        raise fb.FabError(
            "Proceed is disabled: name, layers or Gerber upload missing/invalid.",
            dialog=dlg.inner_text()[:600],
        )
    btn.click(timeout=10000)
    collect: Dict[str, Any] = {}
    deadline = time.time() + wait_sec
    pid = None
    while time.time() < deadline:
        fb.wait_idle(page, timeout_sec=10, settle_sec=1.0, collect=collect)
        m = re.search(r"/projectdetails/(\d+)", page.url)
        if m:
            pid = m.group(1)
            break
        if any(
            "problem" in t.lower() or "error" in t.lower()
            for t in collect.get("toasts_seen", [])
        ):
            break
        time.sleep(1)
    fb.wait_idle(page, timeout_sec=30, settle_sec=1.5, collect=collect)
    return {
        "pid": pid,
        "url": page.url,
        "toasts_seen": collect.get("toasts_seen", []),
        "preview_screenshot": preview_shot,
        "projects_before": projects_before,
    }
