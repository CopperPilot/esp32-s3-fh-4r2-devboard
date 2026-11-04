#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""Map fab-viewer board coordinates back to KiCad objects.

Fab viewers (JLCDFM, placement previews) report positions in Gerber
coordinates. With a lower-left aux origin export, Gerber (x, y) maps to
KiCad (aux_x + x, aux_y - y). This module parses the .kicad_pcb text
directly (no pcbnew needed) and finds the nearest via / pad / footprint.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def find_pcb(project_dir: Path) -> Optional[Path]:
    cands = [
        p
        for p in project_dir.rglob("*.kicad_pcb")
        if ".copperpilot" not in p.parts and "-backups" not in str(p)
    ]
    cands.sort(key=lambda p: (len(p.parts), p.name))
    return cands[0] if cands else None


def _blocks(text: str, head: str) -> List[str]:
    """Return balanced s-expression blocks starting with `(head `."""
    out = []
    rx = re.compile(r"\(" + re.escape(head) + r"[\s)]")
    i = 0
    while True:
        m = rx.search(text, i)
        if not m:
            break
        i = m.start()
        depth = 0
        j = i
        in_str = False
        while j < len(text):
            c = text[j]
            if c == '"' and text[j - 1] != "\\":
                in_str = not in_str
            elif not in_str:
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
            j += 1
        out.append(text[i : j + 1])
        i = j + 1
    return out


@lru_cache(maxsize=4)
def load_board(pcb_path: str) -> Dict[str, Any]:
    text = Path(pcb_path).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\(aux_axis_origin ([\d.\-]+) ([\d.\-]+)\)", text)
    aux = (float(m.group(1)), float(m.group(2))) if m else None
    vias = []
    for v in _blocks(text, "via"):
        a = re.search(r"\(at ([\d.\-]+) ([\d.\-]+)", v)
        sz = re.search(r"\(size ([\d.]+)", v)
        dr = re.search(r"\(drill ([\d.]+)", v)
        if a:
            vias.append(
                {
                    "x": float(a.group(1)),
                    "y": float(a.group(2)),
                    "size": float(sz.group(1)) if sz else None,
                    "drill": float(dr.group(1)) if dr else None,
                }
            )
    pads = []
    fps = []
    for fp in _blocks(text, "footprint"):
        a = re.search(r"\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)", fp)
        ref = re.search(r'\(property "Reference" "([^"]+)"', fp) or re.search(
            r'\(fp_text reference "?([^"\s)]+)', fp
        )
        layer = re.search(r'\(layer "([^"]+)"\)', fp)
        if not a:
            continue
        fx, fy = float(a.group(1)), float(a.group(2))
        rot = float(a.group(3) or 0)
        r = ref.group(1) if ref else "?"
        fps.append(
            {
                "ref": r,
                "x": fx,
                "y": fy,
                "rot": rot,
                "layer": layer.group(1) if layer else None,
            }
        )
        th = math.radians(rot)
        for pd in _blocks(fp, "pad"):
            pm = re.match(r'\(pad "?([^"\s]*)"?\s+(\w+)\s+(\w+)', pd)
            pa = re.search(r"\(at ([\d.\-]+) ([\d.\-]+)", pd)
            ps = re.search(r"\(size ([\d.]+) ([\d.]+)", pd)
            if not (pm and pa):
                continue
            px, py = float(pa.group(1)), float(pa.group(2))
            ax = fx + px * math.cos(th) + py * math.sin(th)
            ay = fy - px * math.sin(th) + py * math.cos(th)
            pads.append(
                {
                    "ref": r,
                    "pad": pm.group(1),
                    "type": pm.group(2),
                    "x": ax,
                    "y": ay,
                    "size": (
                        [float(ps.group(1)), float(ps.group(2))]
                        if ps
                        else None
                    ),
                }
            )
    return {"aux": aux, "vias": vias, "pads": pads, "footprints": fps}


def gerber_to_kicad(
    board: Dict[str, Any], gx: float, gy: float
) -> Tuple[float, float]:
    ox, oy = board["aux"] or (0.0, 0.0)
    return ox + gx, oy - gy


def kicad_to_gerber(
    board: Dict[str, Any], kx: float, ky: float
) -> Tuple[float, float]:
    ox, oy = board["aux"] or (0.0, 0.0)
    return kx - ox, oy - ky


def locate(
    pcb_path: Path, gx: float, gy: float, radius: float = 1.5
) -> Dict[str, Any]:
    b = load_board(str(pcb_path))
    kx, ky = gerber_to_kicad(b, gx, gy)

    def near(items: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
        scored = sorted(
            ((math.hypot(i["x"] - kx, i["y"] - ky), i) for i in items),
            key=lambda t: t[0],
        )
        return [
            dict(
                i, x=round(i["x"], 3), y=round(i["y"], 3), dist_mm=round(d, 2)
            )
            for d, i in scored[:n]
            if d <= radius
        ]

    out: Dict[str, Any] = {"kicad_xy_mm": [round(kx, 3), round(ky, 3)]}
    if not b["aux"]:
        out["warning"] = (
            "Board has no aux origin; assuming Gerber origin == KiCad origin."
        )
    v = near(b["vias"], 2)
    p = near(b["pads"], 3)
    if v:
        out["nearest_vias"] = v
    if p:
        out["nearest_pads"] = [
            {
                "ref": i["ref"],
                "pad": i["pad"],
                "type": i["type"],
                "xy": [i["x"], i["y"]],
                "dist_mm": i["dist_mm"],
            }
            for i in p
        ]
    return out
