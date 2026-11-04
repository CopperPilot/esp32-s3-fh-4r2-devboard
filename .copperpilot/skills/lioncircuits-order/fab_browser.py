#!/usr/bin/env python3
#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""Shared browser core for CopperPilot fab-house skills.

Attaches Playwright to a real Chrome over the Chrome DevTools Protocol (CDP).
By default it uses a dedicated CopperPilot Chrome profile so logins persist and
the agent never touches the user's personal tabs.

Every command prints exactly one JSON object on stdout.

This file is vendored identically into each fab skill folder.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

DEFAULT_CDP_PORT = int(os.environ.get("COPPERPILOT_CDP_PORT", "9333"))
DEFAULT_PROFILE_DIR = Path(
    os.environ.get(
        "COPPERPILOT_CHROME_PROFILE",
        str(Path.home() / ".copperpilot" / "chrome-profile"),
    )
)

# Text on controls the agent must never activate. Matching is
# case-insensitive against the element's visible text, aria-label, title and
# value. Override nothing here: payment is always a human action.
BLOCKED_ACTION_PATTERNS = [
    r"\bpay\s*now\b",
    r"\bpay\b\s*[₹$€]",
    r"\bproceed\s+to\s+(pay|payment|checkout)\b",
    r"\b(secure\s+)?check\s*out\b",
    r"\bplace\s+(the\s+)?order\b",
    r"\bsubmit\s+order\b",
    r"\bconfirm\s+(and\s+)?pay\b",
    r"\bmake\s+payment\b",
    r"\bbuy\s+now\b",
]
_BLOCKED_RE = re.compile("|".join(BLOCKED_ACTION_PATTERNS), re.IGNORECASE)

BUSY_TEXT_RE = re.compile(
    r"(uploading|processing|loading|fetching|getting quotation|"
    r"performing|initializing|analy[sz]ing|calculating|please wait|"
    r"downloading quotation)",
    re.IGNORECASE,
)

INTERACTIVE_ROLES = (
    "button",
    "link",
    "textbox",
    "checkbox",
    "radio",
    "combobox",
    "option",
    "tab",
    "menuitem",
    "spinbutton",
    "switch",
    "slider",
    "searchbox",
    "listbox",
    "row",
    "cell",
)


class FabError(Exception):
    """Error that should be reported as structured JSON."""

    def __init__(self, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.extra = extra


class BlockedActionError(FabError):
    pass


@dataclass
class Result:
    """Uniform JSON envelope returned by every command."""

    command: str
    site: str
    ok: bool = True
    status: str = "ok"
    url: Optional[str] = None
    title: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    observations: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    needs_human: Optional[Dict[str, Any]] = None
    next_actions: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)
    elapsed_sec: Optional[float] = None

    def to_json(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "ok": self.ok,
            "status": self.status,
            "command": self.command,
            "site": self.site,
        }
        if self.url:
            out["url"] = self.url
        if self.title:
            out["title"] = self.title
        if self.needs_human:
            out["needs_human"] = self.needs_human
        if self.data:
            out["data"] = self.data
        if self.observations:
            out["observations"] = self.observations
        if self.warnings:
            out["warnings"] = self.warnings
        if self.next_actions:
            out["next_actions"] = self.next_actions
        if self.artifacts:
            out["artifacts"] = self.artifacts
        if self.elapsed_sec is not None:
            out["elapsed_sec"] = round(self.elapsed_sec, 2)
        return out


def emit(payload: Dict[str, Any]) -> None:
    sys.stdout.write(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    )
    sys.stdout.write("\n")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Chrome discovery / launch
# ---------------------------------------------------------------------------


def chrome_binary_candidates() -> List[str]:
    env = os.environ.get("COPPERPILOT_CHROME_BIN")
    cands: List[str] = [env] if env else []
    system = platform.system()
    if system == "Darwin":
        cands += [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            str(
                Path.home()
                / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ),
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
    elif system == "Windows":
        for base in (
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ):
            if base:
                cands.append(
                    str(Path(base) / "Google/Chrome/Application/chrome.exe")
                )
    else:
        for name in (
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
        ):
            found = shutil.which(name)
            if found:
                cands.append(found)
    return [c for c in cands if c]


def find_chrome() -> Optional[str]:
    for cand in chrome_binary_candidates():
        if Path(cand).exists():
            return cand
    return None


def cdp_version(port: int = DEFAULT_CDP_PORT) -> Optional[Dict[str, Any]]:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/json/version", timeout=2
        ) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def launch_chrome(
    port: int = DEFAULT_CDP_PORT,
    profile_dir: Path = DEFAULT_PROFILE_DIR,
    urls: Optional[List[str]] = None,
    wait_sec: float = 20.0,
) -> Dict[str, Any]:
    """Start the dedicated CopperPilot Chrome profile with CDP enabled."""
    existing = cdp_version(port)
    if existing:
        return {
            "launched": False,
            "already_running": True,
            "version": existing,
        }
    binary = find_chrome()
    if not binary:
        raise FabError(
            "Google Chrome was not found. Install Chrome or set COPPERPILOT_CHROME_BIN.",
            candidates=chrome_binary_candidates(),
        )
    profile_dir.mkdir(parents=True, exist_ok=True)
    args = [
        binary,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=ChromeWhatsNewUI",
    ] + list(urls or [])
    kwargs: Dict[str, Any] = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }
    if platform.system() == "Windows":
        kwargs["creationflags"] = (
            0x00000008 | 0x00000200
        )  # DETACHED | NEW_GROUP
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(args, **kwargs)  # noqa: S603 - fixed binary + args
    deadline = time.time() + wait_sec
    while time.time() < deadline:
        ver = cdp_version(port)
        if ver:
            return {
                "launched": True,
                "binary": binary,
                "profile_dir": str(profile_dir),
                "port": port,
                "version": ver,
            }
        time.sleep(0.5)
    raise FabError(
        f"Chrome did not expose CDP on port {port} within {wait_sec}s. "
        "Another Chrome may already own this profile without debugging; "
        "quit that window and retry.",
        profile_dir=str(profile_dir),
    )


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


@dataclass
class Session:
    pw: Any
    browser: Any
    context: Any
    port: int

    def pages(self) -> List[Any]:
        return list(self.context.pages)


@contextmanager
def session(
    port: int = DEFAULT_CDP_PORT, auto_launch: bool = True
) -> Iterator[Session]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - launcher installs it
        raise FabError(
            "Python package 'playwright' is not installed in this interpreter. "
            "Run the skill through main.py, which bootstraps its runtime."
        ) from exc
    if not cdp_version(port):
        if not auto_launch:
            raise FabError(
                f"No Chrome with remote debugging on port {port}. Run `browser-start`."
            )
        launch_chrome(port)
    pw = sync_playwright().start()
    try:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = (
            browser.contexts[0] if browser.contexts else browser.new_context()
        )
        yield Session(pw=pw, browser=browser, context=context, port=port)
    finally:
        # Never close Chrome itself: it is the user's long-lived session.
        try:
            pw.stop()
        except Exception:
            pass


def list_tabs(sess: Session) -> List[Dict[str, Any]]:
    tabs = []
    for idx, page in enumerate(sess.pages()):
        try:
            title = page.title()
        except Exception:
            title = ""
        tabs.append({"index": idx, "url": page.url, "title": title})
    return tabs


def tag_page(page: Any, role: str) -> None:
    """Mark a tab as the one this skill drives for `role` (survives same-site navigation)."""
    try:
        page.evaluate("(r) => { window.name = 'cp:' + r; }", role)
    except Exception:
        pass


def page_role(page: Any) -> str:
    try:
        return page.evaluate("() => window.name || ''")
    except Exception:
        return ""


ACTIVE_PAGE_FILE = (
    Path.home() / ".copperpilot" / "fab_runtime" / "active_page.json"
)


def mark_active(url: Optional[str]) -> None:
    """Record which page the skill is driving (screen recorders follow it)."""
    if not url:
        return
    try:
        ACTIVE_PAGE_FILE.write_text(
            json.dumps({"url": url, "ts": time.time()})
        )
    except Exception:
        pass


MIN_VIEWPORT_WIDTH = 1280
_PENDING_WARNINGS: List[str] = []


def ensure_desktop_width(
    page: Any, min_width: int = MIN_VIEWPORT_WIDTH
) -> None:
    """Fab sites switch to a mobile layout below ~1024px that hides quote options."""
    try:
        dims = page.evaluate(
            "() => ({ inner: window.innerWidth, outer: window.outerWidth })"
        )
        if dims["inner"] >= min_width:
            return
        cdp = page.context.new_cdp_session(page)
        win = cdp.send("Browser.getWindowForTarget")
        bounds = win.get("bounds", {})
        if bounds.get("windowState") not in (None, "normal"):
            cdp.send(
                "Browser.setWindowBounds",
                {
                    "windowId": win["windowId"],
                    "bounds": {"windowState": "normal"},
                },
            )
        width = min_width + max(0, dims["outer"] - dims["inner"])
        cdp.send(
            "Browser.setWindowBounds",
            {"windowId": win["windowId"], "bounds": {"width": width}},
        )
        time.sleep(0.8)
        _PENDING_WARNINGS.append(
            f"Chrome window was {dims['inner']}px wide (mobile layout); widened it to {min_width}px."
        )
    except Exception:
        pass


def find_role_page(
    sess: Session, role: str, url_pattern: str, open_url: Optional[str] = None
) -> Any:
    """Prefer the tab tagged cp:<role>; else the most recent URL match (then tag it)."""
    rx = re.compile(url_pattern)
    cands = [p for p in sess.pages() if rx.search(p.url or "")]
    tagged = [p for p in cands if page_role(p) == f"cp:{role}"]
    page = tagged[-1] if tagged else (cands[-1] if cands else None)
    if page is None and open_url:
        page = sess.context.new_page()
        page.goto(open_url, wait_until="domcontentloaded", timeout=60000)
    if page is None:
        raise FabError(
            f"No tab for {role}.",
            url_pattern=url_pattern,
            tabs=list_tabs(sess),
        )
    tag_page(page, role)
    try:
        page.bring_to_front()
    except Exception:
        pass
    ensure_desktop_width(page)
    mark_active(page.url)
    return page


def dialog_buttons(page: Any) -> Dict[str, Any]:
    """Visible Element-UI / MUI / ARIA dialog: its text and button labels."""
    return page.evaluate(
        r"""() => {
          const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 2 && r.height > 2 && getComputedStyle(e).visibility !== 'hidden'; };
          const ds = [...document.querySelectorAll('.el-dialog, .el-message-box, [role=dialog], .MuiDialog-paper')].filter(vis);
          if (!ds.length) return {};
          const d = ds[ds.length - 1];
          const btns = [...d.querySelectorAll('button, a.btn, .el-button')].filter(vis).map(b => (b.innerText || '').trim()).filter(t => t && !/^(close|×)$/i.test(t));
          return { text: (d.innerText || '').replace(/\s+\n/g, '\n').trim().slice(0, 600), buttons: [...new Set(btns)] };
        }"""
    )


ACK_ONLY = re.compile(
    r"^(confirm|ok|okay|got it|i know|understood|close)$", re.I
)


def settle_dialog(page: Any) -> Optional[Dict[str, Any]]:
    """Acknowledge purely informational dialogs; return decisions for anything else."""
    d = dialog_buttons(page)
    if not d.get("buttons"):
        return None
    if all(ACK_ONLY.match(b) for b in d["buttons"]):
        btn = (
            page.locator(
                ".el-dialog, .el-message-box, [role=dialog], .MuiDialog-paper"
            )
            .get_by_text(
                re.compile(r"^\s*" + re.escape(d["buttons"][0]) + r"\s*$")
            )
            .last
        )
        try:
            btn.click(timeout=5000)
            time.sleep(0.6)
        except Exception:
            pass
        return {
            "acknowledged_dialog": d["text"][:300],
            "clicked": d["buttons"][0],
        }
    return {
        "decision_required": {"dialog": d["text"], "options": d["buttons"]}
    }


def find_page(
    sess: Session,
    url_pattern: Optional[str] = None,
    tab: Optional[int] = None,
    open_url: Optional[str] = None,
    bring_to_front: bool = True,
) -> Any:
    """Pick a tab by index, by URL regex (most recent match), or open one."""
    pages = sess.pages()
    page = None
    if tab is not None:
        if tab < 0 or tab >= len(pages):
            raise FabError(
                f"Tab index {tab} out of range (0..{len(pages) - 1})"
            )
        page = pages[tab]
    elif url_pattern:
        rx = re.compile(url_pattern)
        matches = [p for p in pages if rx.search(p.url or "")]
        if matches:
            page = matches[-1]
    if page is None and open_url:
        page = sess.context.new_page()
        page.goto(open_url, wait_until="domcontentloaded", timeout=60000)
    if page is None:
        raise FabError(
            "No matching browser tab.",
            url_pattern=url_pattern,
            tabs=list_tabs(sess),
        )
    if bring_to_front:
        try:
            page.bring_to_front()
        except Exception:
            pass
        ensure_desktop_width(page)
        mark_active(page.url)
    return page


# ---------------------------------------------------------------------------
# Page observation helpers
# ---------------------------------------------------------------------------

_OBSERVE_JS = r"""
() => {
  const vis = (el) => {
    if (!el || !el.getBoundingClientRect) return false;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return false;
    if (el.checkVisibility) {  // accounts for hidden/transparent ancestors
      return el.checkVisibility({ opacityProperty: true, visibilityProperty: true, contentVisibilityAuto: true });
    }
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || s.display === 'none' || Number(s.opacity) === 0) return false;
    return true;
  };
  const clean = (t) => (t || '').replace(/\s+\n/g, '\n').replace(/[ \t]+/g, ' ').trim();
  const uniq = (arr) => Array.from(new Set(arr.filter(Boolean)));
  const modalSel = [
    '[role=dialog]', '[role=alertdialog]', '[aria-modal=true]',
    '.el-dialog', '.el-message-box', '.ant-modal', '.MuiDialog-paper',
    '.modal-content', '.modal.show', '[class*=eda-modal-container]', '.v-dialog', '.ReactModal__Content', '.swal2-popup'
  ].join(',');
  const toastSel = [
    '[role=alert]', '[role=status]', '.el-message', '.el-notification', '.ant-message-notice',
    '.ant-notification-notice', '.Toastify__toast', '.MuiSnackbar-root', '.MuiAlert-message',
    '.toast', '.notistack-Snackbar', '.go3958317564', '[class*=toast]', '[class*=Toast]',
    '[class*=snackbar]', '[class*=notification]'
  ].join(',');
  const modals = uniq(Array.from(document.querySelectorAll(modalSel))
    .filter(vis).map((el) => clean(el.innerText).slice(0, 1500)));
  const toasts = uniq(Array.from(document.querySelectorAll(toastSel))
    .filter(vis).map((el) => clean(el.innerText).slice(0, 300)))
    .filter((t) => t.length > 0 && t.length < 300);
  const busyRe = /(please wait|^(uploading|processing|loading|fetching|getting quotation|performing|initializing|retrieving|analy[sz]ing|calculating|downloading quotation)\b[^\n]{0,60}?(\.{2,}|…|\d+\s*%))/i;
  const busy = [];
  for (const el of document.querySelectorAll('body *')) {
    if (el.children.length > 3) continue;
    const t = (el.innerText || '').trim();
    if (!t || t.length > 80 || !busyRe.test(t)) continue;
    if (!vis(el)) continue;
    busy.push(clean(t));
    if (busy.length > 5) break;
  }
  const spinners = Array.from(document.querySelectorAll(
    '.el-loading-mask, .ant-spin-spinning, .MuiCircularProgress-root, [class*=spinner], [class*=loading]'
  )).filter(vis).length;
  return { modals, toasts, busy: uniq(busy), spinners };
}
"""


def observe(page: Any) -> Dict[str, Any]:
    try:
        obs = page.evaluate(_OBSERVE_JS)
    except Exception as exc:  # navigation in flight
        return {"error": f"observe failed: {exc}"}
    out: Dict[str, Any] = {}
    if obs.get("modals"):
        out["modals"] = obs["modals"][:4]
    if obs.get("toasts"):
        out["toasts"] = obs["toasts"][:6]
    if obs.get("busy"):
        out["busy"] = obs["busy"]
    if obs.get("spinners"):
        out["spinners"] = obs["spinners"]
    return out


def wait_idle(
    page: Any,
    timeout_sec: float = 60.0,
    settle_sec: float = 1.0,
    collect: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Wait until no busy overlay/text is visible for `settle_sec`.

    Toasts seen while waiting are accumulated into `collect['toasts_seen']`.
    """
    deadline = time.time() + timeout_sec
    quiet_since: Optional[float] = None
    seen_toasts: List[str] = []
    seen_busy: List[str] = []
    last: Dict[str, Any] = {}
    while time.time() < deadline:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        last = observe(page)
        for t in last.get("toasts", []):
            if t not in seen_toasts:
                seen_toasts.append(t)
        for b in last.get("busy", []):
            # Collapse progress text ("Uploading… 42%") into one entry.
            norm = re.sub(r"\s*\d+(\.\d+)?\s*(%|s\b)|\s*\n.*", "", b).strip()
            if norm and norm not in seen_busy:
                seen_busy.append(norm)
        busy = bool(last.get("busy"))
        if not busy:
            quiet_since = quiet_since or time.time()
            if time.time() - quiet_since >= settle_sec:
                break
        else:
            quiet_since = None
        time.sleep(0.4)
    timed_out = time.time() >= deadline
    info = {
        "timed_out": timed_out,
        "busy_seen": seen_busy,
        "toasts_seen": seen_toasts,
        "final": last,
    }
    if collect is not None:
        collect.setdefault("toasts_seen", [])
        for t in seen_toasts:
            if t not in collect["toasts_seen"]:
                collect["toasts_seen"].append(t)
    return info


# ---------------------------------------------------------------------------
# Snapshot with persistent refs
# ---------------------------------------------------------------------------

_REF_LINE_RE = re.compile(r"\[ref=(e\d+)\]")


def snapshot(
    page: Any,
    scope: Optional[str] = None,
    max_chars: int = 20000,
    grep: Optional[str] = None,
    interactive_only: bool = False,
    depth: Optional[int] = None,
) -> Dict[str, Any]:
    """Return a Playwright AI aria snapshot whose refs survive this process.

    Each `[ref=eN]` element is stamped with `data-cp-ref="eN"` so later
    commands (a new process) can address it with `--ref eN`. Refs are only
    valid until the page re-renders that element; take a fresh snapshot after
    navigation or large UI changes.
    """
    root = page.locator(scope).first if scope else page
    kwargs: Dict[str, Any] = {"mode": "ai"}
    if depth:
        kwargs["depth"] = depth
    text = root.aria_snapshot(**kwargs)
    lines = text.splitlines()
    # Clear stale stamps from a previous snapshot.
    try:
        page.evaluate(
            "() => document.querySelectorAll('[data-cp-ref]').forEach(e => e.removeAttribute('data-cp-ref'))"
        )
    except Exception:
        pass
    refs: List[str] = []
    for line in lines:
        m = _REF_LINE_RE.search(line)
        if not m:
            continue
        stripped = line.strip().lstrip("- ")
        role = stripped.split(" ", 1)[0].rstrip(":")
        if (
            role in INTERACTIVE_ROLES
            or "[cursor=pointer]" in line
            or role == "generic"
        ):
            refs.append(m.group(1))
    stamped = 0
    for ref in refs:
        try:
            page.locator(f"aria-ref={ref}").evaluate(
                "(el, r) => el.setAttribute('data-cp-ref', r)",
                ref,
                timeout=500,
            )
            stamped += 1
        except Exception:
            continue
    if interactive_only:
        keep = []
        for line in lines:
            stripped = line.strip().lstrip("- ")
            role = stripped.split(" ", 1)[0].rstrip(":")
            if (
                role in INTERACTIVE_ROLES
                or "[cursor=pointer]" in line
                or role
                in (
                    "heading",
                    "dialog",
                    "alert",
                )
            ):
                keep.append(line)
        lines = keep
    if grep:
        rx = re.compile(grep, re.IGNORECASE)
        lines = [ln for ln in lines if rx.search(ln)]
    body = "\n".join(lines)
    truncated = len(body) > max_chars
    if truncated:
        body = (
            body[:max_chars]
            + "\n… [truncated: use --scope/--grep/--interactive-only]"
        )
    return {
        "snapshot": body,
        "refs_stamped": stamped,
        "truncated": truncated,
        "chars": len(body),
    }


def resolve(
    page: Any,
    ref: Optional[str] = None,
    selector: Optional[str] = None,
    text: Optional[str] = None,
    role: Optional[str] = None,
    name: Optional[str] = None,
    exact: bool = False,
    nth: int = 0,
) -> Any:
    """Turn agent-friendly addressing into a Playwright locator."""
    if ref:
        loc = page.locator(f"[data-cp-ref='{ref}']")
        if loc.count() == 0:
            raise FabError(
                f"Ref {ref} is stale (element re-rendered or page changed). Take a new snapshot."
            )
        return loc.first
    if role:
        if name:
            nrx = re.compile(
                (
                    (r"^\s*" + re.escape(name) + r"\s*$")
                    if exact
                    else re.escape(name)
                ),
                re.I,
            )
            loc = page.get_by_role(role, name=nrx)
        else:
            loc = page.get_by_role(role)
    elif text:
        # Case-insensitive: sites often uppercase labels with CSS.
        rx = re.compile(
            (
                (r"^\s*" + re.escape(text) + r"\s*$")
                if exact
                else re.escape(text)
            ),
            re.I,
        )
        loc = page.get_by_text(rx)
    elif selector:
        loc = page.locator(selector)
    else:
        raise FabError("Provide one of --ref, --selector, --text, or --role.")
    count = loc.count()
    if count == 0:
        raise FabError(
            "No element matched.",
            selector=selector,
            text=text,
            role=role,
            name=name,
        )
    # Prefer a visible match.
    visible = [i for i in range(count) if _safe_visible(loc.nth(i))]
    if visible:
        idx = visible[min(nth, len(visible) - 1)]
        return loc.nth(idx)
    return loc.nth(min(nth, count - 1))


def _safe_visible(loc: Any) -> bool:
    try:
        return bool(loc.is_visible())
    except Exception:
        return False


def element_label(loc: Any) -> str:
    try:
        return loc.evaluate(
            """(el) => [el.innerText, el.value, el.getAttribute('aria-label'), el.getAttribute('title')]
                 .filter(Boolean).join(' | ').replace(/\\s+/g, ' ').trim().slice(0, 200)"""
        )
    except Exception:
        return ""


# (url regex, label regex): words that only mean "start checkout" on certain pages.
BLOCKED_IN_CONTEXT = [
    (
        re.compile(r"lioncircuits\.com/cart"),
        re.compile(r"^\s*proceed\b", re.I),
    ),
    (
        re.compile(r"jlcpcb\.com/shopcart"),
        re.compile(r"^\s*(secure\s+)?check\s*out", re.I),
    ),
]


def guard_click(loc: Any, allow: bool = False) -> str:
    label = element_label(loc)
    try:
        url = loc.page.url
    except Exception:
        url = ""
    if not allow and any(
        u.search(url) and l.search(label or "") for u, l in BLOCKED_IN_CONTEXT
    ):
        raise BlockedActionError(
            "Blocked: on the cart page this control starts checkout/payment. Payment is always a human step.",
            element=label,
        )
    if not allow and _BLOCKED_RE.search(label or ""):
        raise BlockedActionError(
            "Blocked: this control initiates payment/checkout. Payment is always a human step.",
            element=label,
        )
    return label


def is_blocked_label(label: str) -> bool:
    return bool(_BLOCKED_RE.search(label or ""))


# ---------------------------------------------------------------------------
# Generic actions
# ---------------------------------------------------------------------------


def click(
    page: Any, loc: Any, wait_sec: float = 15.0, force: bool = False
) -> Dict[str, Any]:
    label = guard_click(loc)
    loc.scroll_into_view_if_needed(timeout=5000)
    loc.click(timeout=10000, force=force)
    collect: Dict[str, Any] = {}
    idle = wait_idle(
        page, timeout_sec=wait_sec, settle_sec=0.8, collect=collect
    )
    return {"clicked": label, "idle": _compact_idle(idle)}


def fill(
    page: Any, loc: Any, value: str, press_enter: bool = False
) -> Dict[str, Any]:
    loc.scroll_into_view_if_needed(timeout=5000)
    loc.fill(value, timeout=10000)
    if press_enter:
        loc.press("Enter")
    loc.dispatch_event("change")
    loc.dispatch_event("blur")
    idle = wait_idle(page, timeout_sec=10, settle_sec=0.6)
    return {"filled": value, "idle": _compact_idle(idle)}


def upload(
    page: Any,
    files: List[str],
    loc: Optional[Any] = None,
    trigger: Optional[Any] = None,
    wait_sec: float = 120.0,
) -> Dict[str, Any]:
    """Upload files either into an <input type=file> or via a chooser trigger."""
    paths = [str(Path(f).expanduser().resolve()) for f in files]
    for p in paths:
        if not Path(p).is_file():
            raise FabError(f"File not found: {p}")
    if trigger is not None:
        guard_click(trigger)
        with page.expect_file_chooser(timeout=15000) as fc:
            trigger.click(timeout=10000)
        fc.value.set_files(paths)
    else:
        target = (
            loc if loc is not None else page.locator("input[type=file]").first
        )
        target.set_input_files(paths, timeout=15000)
    collect: Dict[str, Any] = {}
    idle = wait_idle(
        page, timeout_sec=wait_sec, settle_sec=1.5, collect=collect
    )
    return {"uploaded": paths, "idle": _compact_idle(idle)}


def screenshot(
    page: Any,
    out_path: Path,
    selector: Optional[str] = None,
    full_page: bool = False,
    clip: Optional[Dict[str, float]] = None,
) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if selector:
        page.locator(selector).first.screenshot(
            path=str(out_path), timeout=20000, scale="css"
        )
    else:
        kwargs: Dict[str, Any] = {
            "path": str(out_path),
            "full_page": full_page,
            "timeout": 30000,
            "scale": "css",
        }
        if clip:
            kwargs["clip"] = clip
        page.screenshot(**kwargs)
    return str(out_path)


def extract_tables(
    page: Any, selector: str = "table", max_rows: int = 500
) -> List[Dict[str, Any]]:
    """Extract HTML tables (or ARIA grids) into header-keyed rows."""
    js = r"""
    ([sel, maxRows]) => {
      const clean = (t) => (t || '').replace(/\s+/g, ' ').trim();
      const out = [];
      for (const tbl of document.querySelectorAll(sel)) {
        const r = tbl.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) continue;
        let rows = Array.from(tbl.querySelectorAll('tr, [role=row]'));
        if (!rows.length) continue;
        let header = [];
        const thead = tbl.querySelector('thead tr') || rows.find(r => r.querySelector('th,[role=columnheader]'));
        if (thead) header = Array.from(thead.querySelectorAll('th,td,[role=columnheader]')).map(c => clean(c.innerText));
        const body = [];
        for (const row of rows) {
          if (row === thead) continue;
          const cells = Array.from(row.querySelectorAll('td,[role=cell],[role=gridcell]')).map(c => clean(c.innerText));
          if (!cells.length) continue;
          if (header.length === cells.length) {
            const o = {}; header.forEach((h, i) => { o[h || ('col' + i)] = cells[i]; }); body.push(o);
          } else body.push(cells);
          if (body.length >= maxRows) break;
        }
        out.push({ header, rows: body, row_count: body.length });
      }
      return out;
    }
    """
    return page.evaluate(js, [selector, max_rows])


def _compact_idle(idle: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if idle.get("timed_out"):
        out["timed_out"] = True
    if idle.get("busy_seen"):
        out["busy_seen"] = idle["busy_seen"]
    if idle.get("toasts_seen"):
        out["toasts_seen"] = idle["toasts_seen"]
    final = idle.get("final") or {}
    if final.get("modals"):
        out["modals"] = final["modals"]
    return out


# ---------------------------------------------------------------------------
# Artifacts / state
# ---------------------------------------------------------------------------


def artifacts_dir(project_dir: Path, site: str) -> Path:
    d = project_dir / ".copperpilot" / "fab" / site
    d.mkdir(parents=True, exist_ok=True)
    return d


def stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def load_state(project_dir: Path, site: str) -> Dict[str, Any]:
    f = artifacts_dir(project_dir, site) / "state.json"
    if f.is_file():
        try:
            return json.loads(f.read_text())
        except Exception:
            return {}
    return {}


def save_state(project_dir: Path, site: str, state: Dict[str, Any]) -> None:
    f = artifacts_dir(project_dir, site) / "state.json"
    state = dict(state)
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    f.write_text(json.dumps(state, indent=2, default=str))


def log_event(project_dir: Path, site: str, event: Dict[str, Any]) -> None:
    f = artifacts_dir(project_dir, site) / "history.jsonl"
    event = dict(event)
    event["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with f.open("a") as fh:
        fh.write(json.dumps(event, default=str) + "\n")


PATH_ARGS = ("gerber", "bom", "cpl", "xy", "file", "out", "pcb")


def resolve_path_args(args: Any, project_dir: Path) -> None:
    """Relative file arguments resolve against --project-dir, not the shell cwd."""
    for name in PATH_ARGS:
        val = getattr(args, name, None)
        if not val:
            continue

        def fix(v: str) -> str:
            q = Path(v).expanduser()
            return str(q if q.is_absolute() else (project_dir / q).resolve())

        setattr(
            args,
            name,
            [fix(v) for v in val] if isinstance(val, list) else fix(val),
        )


HUMAN_GATES = [
    (
        "terms_consent",
        re.compile(
            r"updated our terms|privacy policy \*|accept & continue|terms of (use|service) .*agree",
            re.I,
        ),
    ),
    (
        "captcha",
        re.compile(
            r"captcha|verify (that )?you are (a )?human|slide to verify|i'?m not a robot",
            re.I,
        ),
    ),
    (
        "otp",
        re.compile(
            r"verification code|one[- ]time password|\botp\b|enter the code",
            re.I,
        ),
    ),
    (
        "login",
        re.compile(
            r"(sign|log) ?in to continue|session (has )?expired|please (sign|log) ?in",
            re.I,
        ),
    ),
    (
        "payment",
        re.compile(
            r"payment method|card number|pay now|razorpay|paypal", re.I
        ),
    ),
]


def human_gate(observations: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Detect dialogs only a human should answer (legal consent, captcha, OTP, login, payment)."""
    for text in (observations or {}).get("modals", []) or []:
        for reason, rx in HUMAN_GATES:
            if rx.search(text or ""):
                return {
                    "reason": reason,
                    "message": f"A {reason.replace('_', ' ')} dialog is open. Ask the user to handle it in the CopperPilot Chrome window, then retry.",
                    "dialog_excerpt": (text or "")[:300],
                }
    return None


JOB_ENV = "COPPERPILOT_FAB_JOB"
DEFAULT_BUDGET_SEC = float(os.environ.get("COPPERPILOT_FAB_BUDGET_SEC", "20"))


def jobs_dir(project_dir: Path, site: str) -> Path:
    d = artifacts_dir(project_dir, site) / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_in_budget(
    site: str,
    command: str,
    project_dir: Path,
    script: Path,
    argv: List[str],
    budget: float,
) -> Optional[int]:
    """Run this command in a detached worker; wait up to `budget` seconds for its result.

    CopperPilot's shell tool backgrounds anything that runs past ~25 s and only reports it
    at the end of the turn, so long browser actions return `in_progress` + a job id instead,
    and `result --job ID` collects the final JSON.
    Returns None when the caller should just run inline (we are the worker, or budget <= 0).
    """
    if os.environ.get(JOB_ENV) or budget <= 0:
        return None
    job = f"{time.strftime('%H%M%S')}-{command}-{os.getpid()}"
    jd = jobs_dir(project_dir, site)
    out = jd / f"{job}.json"
    env = dict(os.environ)
    env[JOB_ENV] = str(out)
    log = open(jd / f"{job}.log", "w")
    kwargs: Dict[str, Any] = {
        "stdout": log,
        "stderr": subprocess.STDOUT,
        "stdin": subprocess.DEVNULL,
        "env": env,
    }
    if platform.system() == "Windows":
        kwargs["creationflags"] = 0x00000008 | 0x00000200
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(
        [sys.executable, str(script), *argv], **kwargs
    )  # noqa: S603
    (jd / f"{job}.pid").write_text(str(proc.pid))
    (jd / "latest").write_text(job)
    deadline = time.time() + budget
    while time.time() < deadline:
        if out.is_file():
            try:
                payload = json.loads(out.read_text())
            except Exception:
                time.sleep(0.2)
                continue
            emit(payload)
            return 0 if payload.get("ok") else 1
        if proc.poll() is not None and not out.is_file():
            time.sleep(0.3)
            if not out.is_file():
                emit(_dead_job(jd, site, command, job))
                return 1
        time.sleep(0.2)
    emit(
        {
            "ok": True,
            "status": "in_progress",
            "command": command,
            "site": site,
            "job": job,
            "data": {
                "message": f"Still working (browser action > {int(budget)}s). The worker keeps running."
            },
            "next_actions": [
                f"Run `result --job {job} --wait-sec 20` (repeat until status != in_progress). Do not start another browser command meanwhile."
            ],
        }
    )
    return 0


def _job_alive(jd: Path, job: str) -> bool:
    pf = jd / f"{job}.pid"
    if not pf.is_file():
        return True
    try:
        os.kill(int(pf.read_text().strip()), 0)
    except (OSError, ValueError):
        return False
    return True


def _dead_job(jd: Path, site: str, command: str, job: str) -> Dict[str, Any]:
    lf = jd / f"{job}.log"
    return {
        "ok": False,
        "status": "error",
        "command": command,
        "site": site,
        "job": job,
        "data": {
            "error": "The worker exited without a result.",
            "log_tail": lf.read_text()[-1200:] if lf.is_file() else "",
        },
        "next_actions": [
            "Run `observe` / `screenshot` to see the page state, then retry the command once."
        ],
    }


def wait_job(
    project_dir: Path, site: str, job: Optional[str], wait_sec: float
) -> Dict[str, Any]:
    jd = jobs_dir(project_dir, site)
    if not job:
        latest = jd / "latest"
        if not latest.is_file():
            raise FabError("No background job recorded.")
        job = latest.read_text().strip()
    out = jd / f"{job}.json"
    deadline = time.time() + wait_sec
    while time.time() < deadline:
        if out.is_file():
            try:
                return json.loads(out.read_text())
            except Exception:
                pass
        elif not _job_alive(jd, job):
            time.sleep(0.5)
            if not out.is_file():
                return _dead_job(jd, site, "result", job)
        time.sleep(0.5)
    log_tail = ""
    lf = jd / f"{job}.log"
    if lf.is_file():
        log_tail = lf.read_text()[-600:]
    return {
        "ok": True,
        "status": "in_progress",
        "command": "result",
        "site": site,
        "job": job,
        "data": {"message": "Still running.", "log_tail": log_tail},
        "next_actions": [f"Run `result --job {job} --wait-sec 20` again."],
    }


def run_command(
    site: str,
    command: str,
    fn: Callable[[Result], None],
    project_dir: Optional[Path] = None,
) -> int:
    res = Result(command=command, site=site)
    t0 = time.time()
    code = 0
    try:
        fn(res)
    except BlockedActionError as exc:
        res.ok = False
        res.status = "blocked"
        res.data.update({"error": str(exc), **exc.extra})
        res.needs_human = {
            "reason": "payment_or_checkout",
            "message": "Payment/checkout is a human step. Ask the user to complete it in the browser.",
        }
        code = 3
    except FabError as exc:
        res.ok = False
        res.status = "error"
        res.data.update({"error": str(exc), **exc.extra})
        code = 1
    except (
        Exception
    ) as exc:  # surface Playwright errors as JSON, not tracebacks
        res.ok = False
        res.status = "error"
        msg = str(exc).splitlines()
        res.data.update(
            {"error": f"{type(exc).__name__}: {msg[0] if msg else exc}"}
        )
        if len(msg) > 1:
            res.data["error_detail"] = "\n".join(msg[1:12])
        code = 1
    res.warnings.extend(w for w in _PENDING_WARNINGS if w not in res.warnings)
    _PENDING_WARNINGS.clear()
    gate = human_gate(res.observations)
    if gate and not res.needs_human:
        res.needs_human = gate
        if res.status == "ok":
            res.status = "needs_human"
    res.elapsed_sec = time.time() - t0
    mark_active(res.url)
    payload = res.to_json()
    if project_dir is not None:
        try:
            log_event(
                project_dir,
                site,
                {
                    "command": command,
                    "argv": sys.argv[1:],
                    "status": res.status,
                    "url": res.url,
                    "error": res.data.get("error"),
                },
            )
        except Exception:
            pass
    emit(payload)
    job_out = os.environ.get(JOB_ENV)
    if job_out:
        try:
            Path(job_out).write_text(
                json.dumps(payload, indent=2, ensure_ascii=False, default=str)
            )
        except Exception:
            pass
    return code


# ---------------------------------------------------------------------------
# Generic CLI wiring shared by both skills
# ---------------------------------------------------------------------------


def add_generic_subcommands(sub: Any) -> None:
    """Register browser-level commands usable on any page."""

    p = sub.add_parser(
        "browser-start", help="Launch/attach the dedicated CopperPilot Chrome"
    )
    p.add_argument("--url", action="append", default=[])

    sub.add_parser("tabs", help="List open tabs")

    def target(p: Any) -> None:
        p.add_argument("--tab", type=int, help="Tab index from `tabs`")
        p.add_argument(
            "--url-match", help="Regex on tab URL (default: this site's tabs)"
        )

    def locate(p: Any) -> None:
        p.add_argument(
            "--ref", help="Ref from the latest `snapshot` (e.g. e42)"
        )
        p.add_argument("--selector", help="CSS / Playwright selector")
        p.add_argument("--text", help="Visible text")
        p.add_argument("--role", help="ARIA role, use with --name")
        p.add_argument("--name", help="Accessible name for --role")
        p.add_argument("--exact", action="store_true")
        p.add_argument(
            "--nth", type=int, default=0, help="Pick the nth visible match"
        )

    p = sub.add_parser("goto", help="Navigate the site tab to a URL")
    target(p)
    p.add_argument("url")
    p.add_argument("--new-tab", action="store_true")

    p = sub.add_parser(
        "snapshot", help="Accessibility snapshot with clickable refs"
    )
    target(p)
    p.add_argument("--scope", help="CSS selector to limit the snapshot")
    p.add_argument("--grep", help="Regex filter on snapshot lines")
    p.add_argument("--interactive-only", action="store_true")
    p.add_argument("--max-chars", type=int, default=20000)
    p.add_argument("--depth", type=int)

    p = sub.add_parser(
        "observe", help="Modals, toasts, and busy indicators on the page"
    )
    target(p)

    p = sub.add_parser(
        "text", help="Visible innerText of the page or a selector"
    )
    target(p)
    p.add_argument("--selector", default="body")
    p.add_argument("--max-chars", type=int, default=15000)

    p = sub.add_parser("tables", help="Extract HTML tables as JSON rows")
    target(p)
    p.add_argument("--selector", default="table")
    p.add_argument("--max-rows", type=int, default=500)

    p = sub.add_parser(
        "screenshot", help="Save a screenshot (page, element or clip)"
    )
    target(p)
    p.add_argument("--selector")
    p.add_argument("--full-page", action="store_true")
    p.add_argument("--clip", help="x,y,width,height in CSS px")
    p.add_argument("--name", default="shot")

    p = sub.add_parser(
        "click", help="Click an element (payment controls are blocked)"
    )
    target(p)
    locate(p)
    p.add_argument("--wait-sec", type=float, default=15.0)
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("fill", help="Fill an input")
    target(p)
    locate(p)
    p.add_argument("--value", required=True)
    p.add_argument("--enter", action="store_true")

    p = sub.add_parser("select", help="Choose an option in a native <select>")
    target(p)
    locate(p)
    p.add_argument("--option", required=True, help="Option label or value")

    p = sub.add_parser(
        "press", help="Press a key (e.g. Escape, Enter, PageDown)"
    )
    target(p)
    p.add_argument("key")

    p = sub.add_parser(
        "scroll", help="Scroll the page or an element into view"
    )
    target(p)
    locate(p)
    p.add_argument("--dy", type=int, default=800)

    p = sub.add_parser("hover", help="Hover an element (reveals tooltips)")
    target(p)
    locate(p)

    p = sub.add_parser(
        "upload",
        help="Upload file(s) into a file input or via a chooser button",
    )
    target(p)
    locate(p)
    p.add_argument("--file", action="append", required=True)
    p.add_argument(
        "--via-chooser",
        action="store_true",
        help="Click the located element and answer the file chooser",
    )
    p.add_argument("--wait-sec", type=float, default=120.0)

    p = sub.add_parser(
        "wait", help="Wait for text/selector, or for busy indicators to clear"
    )
    target(p)
    p.add_argument("--text")
    p.add_argument("--selector")
    p.add_argument(
        "--gone", action="store_true", help="Wait for it to disappear instead"
    )
    p.add_argument(
        "--idle", action="store_true", help="Wait until no busy overlays"
    )
    p.add_argument("--timeout-sec", type=float, default=60.0)

    p = sub.add_parser(
        "eval", help="Evaluate JavaScript in the page (read-only by default)"
    )
    target(p)
    p.add_argument("script", help="JS expression or arrow function")
    p.add_argument("--allow-mutation", action="store_true")

    p = sub.add_parser(
        "reload", help="Reload the tab (the sites are flaky SPAs)"
    )
    target(p)


_MUTATING_JS_RE = re.compile(
    r"\.(click|submit|dispatchEvent|remove)\s*\(|\.value\s*=|innerHTML\s*=",
    re.I,
)


def handle_generic(
    args: Any,
    res: Result,
    sess: Session,
    default_url_match: str,
    default_open_url: str,
    project_dir: Path,
) -> bool:
    """Run a generic command. Returns False if `args.command` is not generic."""
    cmd = args.command
    if cmd == "tabs":
        res.data["tabs"] = list_tabs(sess)
        return True

    def page_for() -> Any:
        tab = getattr(args, "tab", None)
        url_match = getattr(args, "url_match", None)
        if tab is None and not url_match:
            # Default to the tab the previous command used (e.g. the one just snapshotted),
            # so `snapshot --tab 0` followed by `click --ref eN` hits the same page.
            last = load_state(project_dir, res.site).get("last_page")
            if last:
                for idx, pg in enumerate(sess.pages()):
                    if pg.url == last.get("url") or (
                        last.get("role") and page_role(pg) == last.get("role")
                    ):
                        tab = idx
                        break
        return find_page(
            sess,
            url_pattern=url_match or default_url_match,
            tab=tab,
            open_url=default_open_url,
        )

    def loc_for(page: Any) -> Any:
        return resolve(
            page,
            ref=getattr(args, "ref", None),
            selector=getattr(args, "selector", None),
            text=getattr(args, "text", None),
            role=getattr(args, "role", None),
            name=getattr(args, "name", None),
            exact=getattr(args, "exact", False),
            nth=getattr(args, "nth", 0),
        )

    if cmd == "goto":
        if args.new_tab:
            page = sess.context.new_page()
        else:
            page = page_for()
        page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
        res.data["idle"] = _compact_idle(wait_idle(page, timeout_sec=30))
    elif cmd == "snapshot":
        page = page_for()
        res.data.update(
            snapshot(
                page,
                scope=args.scope,
                max_chars=args.max_chars,
                grep=args.grep,
                interactive_only=args.interactive_only,
                depth=args.depth,
            )
        )
    elif cmd == "observe":
        page = page_for()
        res.observations = observe(page)
    elif cmd == "text":
        page = page_for()
        txt = page.locator(args.selector).first.inner_text(timeout=10000)
        txt = re.sub(r"\n{3,}", "\n\n", txt)
        res.data["text"] = txt[: args.max_chars]
        res.data["truncated"] = len(txt) > args.max_chars
    elif cmd == "tables":
        page = page_for()
        res.data["tables"] = extract_tables(page, args.selector, args.max_rows)
    elif cmd == "screenshot":
        page = page_for()
        clip = None
        if args.clip:
            x, y, w, h = [float(v) for v in args.clip.split(",")]
            clip = {"x": x, "y": y, "width": w, "height": h}
        out = (
            artifacts_dir(project_dir, res.site)
            / "shots"
            / f"{stamp()}-{args.name}.png"
        )
        res.artifacts["screenshot"] = screenshot(
            page,
            out,
            selector=args.selector,
            full_page=args.full_page,
            clip=clip,
        )
    elif cmd == "click":
        page = page_for()
        res.data.update(
            click(
                page, loc_for(page), wait_sec=args.wait_sec, force=args.force
            )
        )
        page = _maybe_new_page(sess, page)
    elif cmd == "fill":
        page = page_for()
        res.data.update(
            fill(page, loc_for(page), args.value, press_enter=args.enter)
        )
    elif cmd == "select":
        page = page_for()
        loc = loc_for(page)
        try:
            loc.select_option(label=args.option, timeout=5000)
        except Exception:
            loc.select_option(value=args.option, timeout=5000)
        res.data["selected"] = args.option
        res.data["idle"] = _compact_idle(wait_idle(page, timeout_sec=15))
    elif cmd == "press":
        page = page_for()
        page.keyboard.press(args.key)
        res.data["idle"] = _compact_idle(wait_idle(page, timeout_sec=10))
    elif cmd == "scroll":
        page = page_for()
        if any(
            getattr(args, k, None) for k in ("ref", "selector", "text", "role")
        ):
            loc_for(page).scroll_into_view_if_needed(timeout=5000)
        else:
            page.mouse.wheel(0, args.dy)
            time.sleep(0.5)
        res.data["scroll_y"] = page.evaluate("() => window.scrollY")
    elif cmd == "hover":
        page = page_for()
        loc_for(page).hover(timeout=5000)
        time.sleep(0.8)
    elif cmd == "upload":
        page = page_for()
        has_loc = any(
            getattr(args, k, None) for k in ("ref", "selector", "text", "role")
        )
        if args.via_chooser:
            res.data.update(
                upload(
                    page,
                    args.file,
                    trigger=loc_for(page),
                    wait_sec=args.wait_sec,
                )
            )
        else:
            res.data.update(
                upload(
                    page,
                    args.file,
                    loc=loc_for(page) if has_loc else None,
                    wait_sec=args.wait_sec,
                )
            )
    elif cmd == "wait":
        page = page_for()
        t_ms = int(args.timeout_sec * 1000)
        if args.text:
            state = "hidden" if args.gone else "visible"
            page.get_by_text(args.text).first.wait_for(
                state=state, timeout=t_ms
            )
        elif args.selector:
            state = "hidden" if args.gone else "visible"
            page.locator(args.selector).first.wait_for(
                state=state, timeout=t_ms
            )
        res.data["idle"] = _compact_idle(
            wait_idle(page, timeout_sec=args.timeout_sec)
        )
    elif cmd == "eval":
        page = page_for()
        if _MUTATING_JS_RE.search(args.script) and not args.allow_mutation:
            raise FabError(
                "Script looks mutating. Prefer click/fill commands (they enforce the payment guard). "
                "Pass --allow-mutation if this is intentional and not payment-related."
            )
        if _BLOCKED_RE.search(args.script):
            raise BlockedActionError(
                "Script references payment/checkout controls."
            )
        script = args.script.strip()
        if not (
            script.startswith("(")
            or script.startswith("function")
            or "=>" in script
        ):
            script = f"() => ({script})"
        res.data["value"] = page.evaluate(script)
    elif cmd == "reload":
        page = page_for()
        page.reload(wait_until="domcontentloaded", timeout=60000)
        res.data["idle"] = _compact_idle(wait_idle(page, timeout_sec=45))
    else:
        return False
    try:
        page = page_for()
        res.url = page.url
        res.title = page.title()
        if cmd not in ("observe",):
            res.observations = observe(page)
        remember_page(project_dir, res.site, page)
    except Exception:
        pass
    return True


def remember_page(project_dir: Path, site: str, page: Any) -> None:
    st = load_state(project_dir, site)
    st["last_page"] = {"url": page.url, "role": page_role(page)}
    save_state(project_dir, site, st)


def _maybe_new_page(sess: Session, page: Any) -> Any:
    pages = sess.pages()
    return pages[-1] if pages and pages[-1] is not page else page
