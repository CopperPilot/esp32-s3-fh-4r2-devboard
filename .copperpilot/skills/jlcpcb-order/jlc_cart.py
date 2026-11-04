#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""JLCPCB shopping cart: list and remove items. Checkout is never touched."""

from __future__ import annotations

import re
import time
from typing import Any, Dict

import fab_browser as fb

CART_URL = "https://cart.jlcpcb.com/shopcart/cart"

CART_JS = r"""
() => {
  const clean = (t) => (t || '').replace(/[\s ]+/g, ' ').trim();
  const groups = [];
  for (const g of document.querySelectorAll('.main-cart-list')) {
    if (g.getBoundingClientRect().height < 5) continue;
    const rows = [];
    for (const r of g.querySelectorAll('.main-cart-data')) {
      const name = r.querySelector('.main-cl-name');
      if (!name) continue;
      const lines = [...new Set((name.innerText || '').split('\n').map(clean))]
        .filter(t => t && !/^(Product Details|Edit Order|Customer #:?)/.test(t) && !/^Product Details/.test(t));
      const order = (name.innerText.match(/:\s*([A-Z0-9][A-Z0-9-]{6,})/) || [])[1] || null;
      rows.push({
        name: lines[0] || null, product: lines[1] || null, specs: lines.slice(2).join(' | ') || null,
        order_no: order,
        qty: clean((r.querySelector('.cart-quantity') || {}).innerText),
        build_time: clean((r.querySelector('.cart-build-time') || {}).innerText),
        price: clean((r.querySelector('.data-unit .price, .data-unit') || {}).innerText),
      });
    }
    if (rows.length) groups.push({ index: groups.length, rows });
  }
  const body = document.body.innerText || '';
  const m = body.match(/All \((\d+)\)/);
  return { count_label: m ? +m[1] : null, items: groups };
}
"""


def cart_page(sess: fb.Session) -> Any:
    page = fb.find_role_page(
        sess, "cart", r"cart\.jlcpcb\.com/shopcart", open_url=CART_URL
    )
    if "shopcart" not in page.url:
        page.goto(CART_URL, wait_until="domcontentloaded", timeout=60000)
    return page


def list_cart(page: Any, reload: bool = True) -> Dict[str, Any]:
    if reload:
        page.goto(CART_URL, wait_until="domcontentloaded", timeout=60000)
    try:
        page.locator(
            ".main-cart-list, :text('Your cart is empty')"
        ).first.wait_for(timeout=20000)
    except Exception:
        pass
    time.sleep(1.0)
    return page.evaluate(CART_JS)


def remove_items(
    page: Any, match: str, dry_run: bool = False
) -> Dict[str, Any]:
    """Remove cart groups whose text contains `match` (order no, file name...)."""
    if not match or len(match) < 3:
        raise fb.FabError(
            "--match must be at least 3 characters (an order number like Y11-3027426A is best)."
        )
    before = list_cart(page)
    rx = re.compile(re.escape(match), re.I)
    targets = [
        g
        for g in before["items"]
        if any(
            rx.search(" ".join(str(v) for v in r.values() if v))
            for r in g["rows"]
        )
    ]
    if dry_run or not targets:
        return {
            "matched": targets,
            "removed": 0,
            "dry_run": dry_run,
            "cart_before": before,
        }
    removed = 0
    for _ in targets:
        groups = page.locator(".main-cart-list").filter(has_text=rx)
        if not groups.count():
            break
        icon = groups.first.locator("i.icon-remove_icon").first
        icon.scroll_into_view_if_needed(timeout=5000)
        icon.click(timeout=5000)
        time.sleep(0.8)
        confirm = page.locator(
            ".el-popover:visible, .el-message-box:visible, .el-dialog:visible"
        ).get_by_role(
            "button",
            name=re.compile(r"^\s*(confirm|ok|yes|delete|remove)\s*$", re.I),
        )
        if confirm.count():
            confirm.first.click(timeout=5000)
        time.sleep(1.5)
        fb.wait_idle(page, timeout_sec=20, settle_sec=1.0)
        removed += 1
    after = list_cart(page)
    return {"matched": targets, "removed": removed, "cart_after": after}
