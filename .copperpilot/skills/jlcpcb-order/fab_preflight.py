#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""Offline checks on fab files before uploading them anywhere.

No browser needed. Catches the cheap mistakes (missing outline/drill,
wrong BOM headers, BOM↔CPL designator drift) before they cost an upload
round-trip and a confusing website error.
"""

from __future__ import annotations

import csv
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

LAYER_PATTERNS = [
    ("top_copper", r"(f[_.]cu|\.gtl$|top[_ ]?(copper|layer))"),
    ("bottom_copper", r"(b[_.]cu|\.gbl$|bottom[_ ]?(copper|layer))"),
    ("inner_copper", r"(in\d+[_.]cu|\.g\d+$|\.gp\d$)"),
    ("top_mask", r"(f[_.]mask|\.gts$)"),
    ("bottom_mask", r"(b[_.]mask|\.gbs$)"),
    ("top_silk", r"(f[_.]silk|\.gto$)"),
    ("bottom_silk", r"(b[_.]silk|\.gbo$)"),
    ("top_paste", r"(f[_.]paste|\.gtp$)"),
    ("bottom_paste", r"(b[_.]paste|\.gbp$)"),
    ("outline", r"(edge[_.]cuts|\.gm1$|\.gko$|outline)"),
    ("drill", r"(\.drl$|\.xln$|\.txt$|\.exc$|drill)"),
    ("job", r"\.gbrjob$"),
]

SITE_BOM_HEADERS = {
    "jlcpcb": {
        "required": [["comment", "value"], ["designator"], ["footprint"]],
        "recommended": [["jlcpcb part", "lcsc", "lcsc part", "jlcpcb part #"]],
    },
    "lioncircuits": {
        "required": [
            ["item number", "item"],
            ["designator"],
            ["unit quantity", "quantity", "qty"],
            ["description"],
        ],
        "recommended": [
            ["manufacturer part number", "mpn"],
            ["footprint"],
            ["value"],
            ["assembly instructions"],
        ],
    },
}
CPL_HEADERS = {
    "required": [
        ["designator"],
        ["mid x", "posx", "x"],
        ["mid y", "posy", "y"],
        ["layer", "side"],
        ["rotation", "rot"],
    ],
}


def _issue(
    severity: str, code: str, message: str, **extra: Any
) -> Dict[str, Any]:
    out = {"severity": severity, "code": code, "message": message}
    out.update(extra)
    return out


def read_table(path: Path) -> List[Dict[str, str]]:
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        try:
            import openpyxl  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("openpyxl needed to read .xlsx") from exc
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        header = [str(h).strip() if h is not None else "" for h in rows[0]]
        return [
            {
                header[i]: ("" if v is None else str(v)).strip()
                for i, v in enumerate(r)
                if i < len(header)
            }
            for r in rows[1:]
            if any(v not in (None, "") for v in r)
        ]
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return [
        {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        for row in csv.DictReader(text.splitlines())
    ]


def _find_col(headers: List[str], aliases: List[str]) -> Optional[str]:
    norm = {h: re.sub(r"[^a-z0-9# ]", "", h.lower()).strip() for h in headers}
    for alias in aliases:
        for h, n in norm.items():
            if n == alias:
                return h
    for alias in aliases:
        for h, n in norm.items():
            if n.startswith(alias):
                return h
    return None


def split_designators(value: str) -> List[str]:
    out: List[str] = []
    for tok in re.split(r"[,\s;]+", value or ""):
        tok = tok.strip()
        if not tok:
            continue
        m = re.fullmatch(r"([A-Za-z_]+)(\d+)-\1?(\d+)", tok)
        if m:
            pre, a, b = m.group(1), int(m.group(2)), int(m.group(3))
            out.extend(f"{pre}{i}" for i in range(a, b + 1))
        else:
            out.append(tok)
    return out


def check_gerber_zip(path: Path) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    if not path.is_file():
        return {
            "file": str(path),
            "issues": [_issue("error", "missing", "Gerber archive not found")],
        }
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return {
            "file": str(path),
            "issues": [_issue("error", "bad_zip", "Not a valid zip archive")],
        }
    names = [n for n in zf.namelist() if not n.endswith("/")]
    found: Dict[str, List[str]] = {}
    unknown = []
    for n in names:
        base = Path(n).name.lower()
        hit = False
        for kind, rx in LAYER_PATTERNS:
            if re.search(rx, base):
                found.setdefault(kind, []).append(n)
                hit = True
                break
        if not hit:
            unknown.append(n)
    if any("/" in n for n in names):
        issues.append(
            _issue(
                "warning",
                "nested_dirs",
                "Files are inside sub-folders; some fabs expect a flat zip.",
                files=names[:5],
            )
        )
    for kind, sev in (
        ("top_copper", "error"),
        ("outline", "error"),
        ("drill", "error"),
        ("top_mask", "warning"),
        ("bottom_mask", "warning"),
    ):
        if kind not in found:
            issues.append(
                _issue(
                    sev,
                    f"no_{kind}",
                    f"No {kind.replace('_', ' ')} layer found in the archive.",
                )
            )
    job: Dict[str, Any] = {}
    if "job" in found:
        try:
            data = json.loads(
                zf.read(found["job"][0]).decode("utf-8", errors="replace")
            )
            spec = data.get("GeneralSpecs", {})
            size = spec.get("Size", {})
            job = {
                "layer_count": spec.get("LayerNumber"),
                "board_thickness_mm": spec.get("BoardThickness"),
                "size_mm": [size.get("X"), size.get("Y")],
                "finish": spec.get("Finish"),
            }
        except Exception as exc:
            issues.append(
                _issue("info", "job_unreadable", f"gbrjob unreadable: {exc}")
            )
    copper = (
        len(found.get("top_copper", []))
        + len(found.get("bottom_copper", []))
        + len(found.get("inner_copper", []))
    )
    if job.get("layer_count") and copper and int(job["layer_count"]) != copper:
        issues.append(
            _issue(
                "warning",
                "layer_mismatch",
                f"gbrjob says {job['layer_count']} layers but {copper} copper files found.",
            )
        )
    return {
        "file": str(path),
        "size_bytes": path.stat().st_size,
        "files": len(names),
        "layers": {k: [Path(v).name for v in vs] for k, vs in found.items()},
        "unrecognized": unknown,
        "copper_layers": copper,
        "job": job or None,
        "issues": issues,
    }


def check_bom(path: Path, site: str) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    rows = read_table(path)
    if not rows:
        return {
            "file": str(path),
            "issues": [_issue("error", "empty", "BOM has no rows")],
        }
    headers = list(rows[0].keys())
    spec = SITE_BOM_HEADERS[site]
    cols: Dict[str, Optional[str]] = {}
    for aliases in spec["required"]:
        col = _find_col(headers, aliases)
        cols[aliases[0]] = col
        if not col:
            issues.append(
                _issue(
                    "error",
                    "missing_column",
                    f"Required column '{aliases[0]}' missing.",
                    headers=headers,
                )
            )
    for aliases in spec["recommended"]:
        col = _find_col(headers, aliases)
        cols[aliases[0]] = col
        if not col:
            issues.append(
                _issue(
                    "warning",
                    "missing_column",
                    f"Recommended column '{aliases[0]}' missing.",
                )
            )
    designators: List[str] = []
    dup: List[str] = []
    no_pn: List[str] = []
    qty_mismatch: List[Dict[str, Any]] = []
    dcol = cols.get("designator")
    pn_col = cols.get("jlcpcb part") or cols.get("manufacturer part number")
    qcol = cols.get("unit quantity")
    for r in rows:
        refs = split_designators(r.get(dcol, "")) if dcol else []
        for d in refs:
            if d in designators:
                dup.append(d)
            designators.append(d)
        if pn_col and not r.get(pn_col):
            no_pn.append(r.get(dcol or "", "?"))
        if qcol and r.get(qcol):
            try:
                q = int(float(r[qcol]))
                if q != len(refs):
                    qty_mismatch.append(
                        {
                            "designators": r.get(dcol or ""),
                            "quantity": q,
                            "count": len(refs),
                        }
                    )
            except ValueError:
                qty_mismatch.append(
                    {
                        "designators": r.get(dcol or ""),
                        "quantity": r[qcol],
                        "count": len(refs),
                    }
                )
    if dup:
        issues.append(
            _issue(
                "error",
                "duplicate_designator",
                "Designators listed twice.",
                designators=sorted(set(dup)),
            )
        )
    if no_pn:
        issues.append(
            _issue(
                "warning",
                "missing_part_number",
                f"{len(no_pn)} line(s) without a part number ({pn_col}).",
                lines=no_pn[:20],
            )
        )
    if qty_mismatch:
        issues.append(
            _issue(
                "error",
                "qty_mismatch",
                "Quantity column disagrees with designator count.",
                lines=qty_mismatch[:20],
            )
        )
    return {
        "file": str(path),
        "site": site,
        "lines": len(rows),
        "parts": len(designators),
        "columns": cols,
        "designators": designators,
        "issues": issues,
    }


def check_cpl(path: Path) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    rows = read_table(path)
    if not rows:
        return {
            "file": str(path),
            "issues": [_issue("error", "empty", "CPL has no rows")],
        }
    headers = list(rows[0].keys())
    cols = {}
    for aliases in CPL_HEADERS["required"]:
        col = _find_col(headers, aliases)
        cols[aliases[0]] = col
        if not col:
            issues.append(
                _issue(
                    "error",
                    "missing_column",
                    f"CPL column '{aliases[0]}' missing.",
                    headers=headers,
                )
            )
    sides: Dict[str, int] = {}
    bad = []
    seen = set()
    dups = []
    designators = []
    for r in rows:
        d = r.get(cols.get("designator") or "", "")
        designators.append(d)
        if d in seen:
            dups.append(d)
        seen.add(d)
        side = (r.get(cols.get("layer") or "", "") or "").lower()
        side = (
            "top"
            if side.startswith(("t", "f"))
            else "bottom" if side.startswith("b") else side or "?"
        )
        sides[side] = sides.get(side, 0) + 1
        for k in ("mid x", "mid y", "rotation"):
            c = cols.get(k)
            if c:
                try:
                    float(str(r.get(c, "")).replace("mm", ""))
                except ValueError:
                    bad.append(
                        {"designator": d, "column": c, "value": r.get(c)}
                    )
    if dups:
        issues.append(
            _issue(
                "error",
                "duplicate_designator",
                "CPL has duplicate designators.",
                designators=dups,
            )
        )
    if bad:
        issues.append(
            _issue(
                "error",
                "non_numeric",
                "Non-numeric coordinates/rotation.",
                rows=bad[:10],
            )
        )
    return {
        "file": str(path),
        "parts": len(rows),
        "sides": sides,
        "columns": cols,
        "designators": designators,
        "issues": issues,
    }


def cross_check(
    bom: Dict[str, Any], cpl: Dict[str, Any]
) -> List[Dict[str, Any]]:
    b = set(bom.get("designators", []))
    c = set(cpl.get("designators", []))
    issues = []
    only_bom = sorted(b - c)
    only_cpl = sorted(c - b)
    if only_bom:
        issues.append(
            _issue(
                "error",
                "bom_not_in_cpl",
                "Parts in BOM have no placement (fab will not place them).",
                designators=only_bom,
            )
        )
    if only_cpl:
        issues.append(
            _issue(
                "warning",
                "cpl_not_in_bom",
                "Placements without BOM line (treated as DNP / not assembled).",
                designators=only_cpl,
            )
        )
    return issues


def preflight(
    site: str,
    gerber: Optional[str] = None,
    bom: Optional[str] = None,
    cpl: Optional[str] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {"site": site}
    issues: List[Dict[str, Any]] = []
    if gerber:
        g = check_gerber_zip(Path(gerber).expanduser().resolve())
        out["gerber"] = g
        issues += [dict(i, file="gerber") for i in g["issues"]]
    b = c = None
    if bom:
        b = check_bom(Path(bom).expanduser().resolve(), site)
        issues += [dict(i, file="bom") for i in b["issues"]]
        out["bom"] = {k: v for k, v in b.items() if k != "designators"}
    if cpl:
        c = check_cpl(Path(cpl).expanduser().resolve())
        issues += [dict(i, file="cpl") for i in c["issues"]]
        out["cpl"] = {k: v for k, v in c.items() if k != "designators"}
    if b and c:
        issues += [dict(i, file="bom+cpl") for i in cross_check(b, c)]
    out["issues"] = issues
    out["errors"] = sum(1 for i in issues if i["severity"] == "error")
    out["warnings"] = sum(1 for i in issues if i["severity"] == "warning")
    out["verdict"] = (
        "fail"
        if out["errors"]
        else ("pass_with_warnings" if out["warnings"] else "pass")
    )
    return out
