#!/usr/bin/env python3
"""KiCad library search skill installed by CopperPilot."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Literal, Optional, Sequence

Platform = Literal["win", "mac", "linux"]


def default_symbol_dir(platform: Platform) -> Path:
    env = os.environ.get("KICAD10_SYMBOL_DIR")
    if env:
        return Path(env)
    if platform == "mac":
        return Path(
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
        )
    if platform == "win":
        return Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols")
    return Path("/usr/share/kicad/symbols")


def default_footprint_dir(platform: Platform) -> Path:
    env = os.environ.get("KICAD10_FOOTPRINT_DIR")
    if env:
        return Path(env)
    if platform == "mac":
        return Path(
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
        )
    if platform == "win":
        return Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
    return Path("/usr/share/kicad/footprints")


def default_model_dir(platform: Platform) -> Path:
    env = os.environ.get("KICAD10_3DMODEL_DIR")
    if env:
        return Path(env)
    if platform == "mac":
        return Path(
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels"
        )
    if platform == "win":
        return Path(r"C:\Program Files\KiCad\10.0\share\kicad\3dmodels")
    return Path("/usr/share/kicad/3dmodels")


def _dedupe_paths(paths: Iterable[Path]) -> List[Path]:
    seen: set[str] = set()
    out: List[Path] = []
    for raw in paths:
        resolved = raw.expanduser()
        key = str(resolved.resolve()) if resolved.exists() else str(resolved)
        if key in seen:
            continue
        seen.add(key)
        out.append(resolved)
    return out


def project_local_symbol_paths(project_dir: Path) -> List[Path]:
    root = project_dir.resolve()
    paths: List[Path] = []
    for path in sorted(root.glob("*.kicad_sym")):
        paths.append(path)
    return paths


def project_local_footprint_dirs(project_dir: Path) -> List[Path]:
    root = project_dir.resolve()
    return sorted(root.glob("*.pretty"))


def project_local_model_dirs(project_dir: Path) -> List[Path]:
    root = project_dir.resolve()
    model_root = root / "libs" / "3dmodels"
    if model_root.is_dir():
        return [model_root]
    return []


def resolve_symbol_roots(
    platform: Platform,
    *,
    project_dir: Path,
    include_project_local: bool,
    extra_dirs: Optional[Sequence[str]] = None,
) -> tuple[List[Path], List[str]]:
    """Return symbol file paths and warning strings."""
    warnings: List[str] = []
    paths: List[Path] = []

    stock = default_symbol_dir(platform)
    if stock.is_dir():
        paths.extend(sorted(stock.glob("*.kicad_sym")))
    else:
        warnings.append(f"Stock symbol directory not found: {stock}")

    if extra_dirs:
        for raw in extra_dirs:
            candidate = Path(raw).expanduser()
            if candidate.is_file() and candidate.suffix == ".kicad_sym":
                paths.append(candidate)
            elif candidate.is_dir():
                paths.extend(sorted(candidate.rglob("*.kicad_sym")))
            else:
                warnings.append(f"Symbol path not found: {candidate}")

    if include_project_local:
        paths.extend(project_local_symbol_paths(project_dir))

    return _dedupe_paths(paths), warnings


def resolve_footprint_roots(
    platform: Platform,
    *,
    project_dir: Path,
    include_project_local: bool,
    extra_dirs: Optional[Sequence[str]] = None,
    prefer_extra_dirs: bool = True,
) -> tuple[List[Path], List[str]]:
    """Resolve footprint library roots.

    When ``prefer_extra_dirs`` is True (default), explicit and project-local
    roots are searched before stock libraries so deterministic fixtures and
    project overrides win over mismatched stock versions.
    """
    warnings: List[str] = []
    extra: List[Path] = []
    project_local: List[Path] = []
    stock_dirs: List[Path] = []

    stock = default_footprint_dir(platform)
    if stock.is_dir():
        stock_dirs.extend(sorted(stock.glob("*.pretty")))
    else:
        warnings.append(f"Stock footprint directory not found: {stock}")

    if extra_dirs:
        for raw in extra_dirs:
            candidate = Path(raw).expanduser()
            if candidate.suffix == ".pretty" and candidate.is_dir():
                extra.append(candidate)
            elif candidate.is_dir():
                extra.extend(sorted(candidate.rglob("*.pretty")))
            else:
                warnings.append(f"Footprint path not found: {candidate}")

    if include_project_local:
        project_local.extend(project_local_footprint_dirs(project_dir))

    if prefer_extra_dirs:
        dirs = extra + project_local + stock_dirs
    else:
        dirs = stock_dirs + extra + project_local

    return _dedupe_paths(dirs), warnings


def resolve_model_roots(
    platform: Platform,
    *,
    project_dir: Path,
    include_project_local: bool,
    extra_dirs: Optional[Sequence[str]] = None,
) -> tuple[List[Path], List[str]]:
    warnings: List[str] = []
    roots: List[Path] = []

    if extra_dirs:
        for raw in extra_dirs:
            candidate = Path(raw).expanduser()
            if candidate.is_dir():
                roots.append(candidate)
            else:
                warnings.append(f"3D model path not found: {candidate}")

    if include_project_local:
        roots.extend(project_local_model_dirs(project_dir))

    # Explicit and project-local roots are intent-bearing and must not be
    # crowded out by a large stock library before max_results is reached.
    stock = default_model_dir(platform)
    if stock.is_dir():
        roots.append(stock)
    else:
        warnings.append(f"Stock 3D model directory not found: {stock}")

    return _dedupe_paths(roots), warnings

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence


SearchKind = Literal["symbol", "footprint", "model", "all"]
MODEL_EXTENSIONS = {".step", ".stp", ".wrl", ".stl"}


@dataclass
class SearchResult:
    kind: str
    library: str
    name: str
    path: str
    score: float
    identifier: str
    description: str = ""
    keywords: str = ""
    tags: str = ""
    model_path: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "kind": self.kind,
            "library": self.library,
            "name": self.name,
            "path": self.path,
            "score": self.score,
            "identifier": self.identifier,
        }
        if self.description:
            payload["description"] = self.description
        if self.keywords:
            payload["keywords"] = self.keywords
        if self.tags:
            payload["tags"] = self.tags
        if self.model_path:
            payload["model_path"] = self.model_path
        if self.extra:
            payload.update(self.extra)
        if self.kind == "footprint":
            payload["library_path"] = self.path
            payload["footprint_id"] = self.name
        elif self.kind == "symbol":
            payload["library_path"] = self.path
            payload["symbol_id"] = self.name
        return payload


def _split_query_words(query: str) -> List[str]:
    words: List[str] = []
    for space_sep in query.lower().split():
        for pipe_sep in space_sep.split("|"):
            for col_sep in pipe_sep.split(":"):
                token = col_sep.strip()
                if token:
                    words.append(token)
    return words


def _calculate_name_score(
    name: str,
    query_lower: str,
    query_words: Sequence[str],
    *,
    short_name_bonus: int = 2,
) -> float:
    score = 0.0
    name_lower = name.lower()

    if query_lower == name_lower:
        score += 20.0

    name_matched = False
    for word in query_words:
        if word == name_lower:
            score += 25.0
            name_matched = True
            break

    if len(name_lower) <= short_name_bonus:
        for word in query_words:
            if word == name_lower:
                score += 15.0
                break

    if not name_matched and query_words and query_words[0] == name_lower:
        score += 10.0
        name_matched = True

    if not name_matched and query_lower in name_lower:
        score += 10.0

    return score


def _read_limited_text(path: Path, max_bytes: int) -> str:
    size = path.stat().st_size
    if size <= max_bytes:
        return path.read_text(encoding="utf-8", errors="replace")
    with path.open("rb") as handle:
        data = handle.read(max_bytes)
    return data.decode("utf-8", errors="replace")


def _extract_property(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1) if match else ""


def _timed_out(start: float, timeout_ms: Optional[int]) -> bool:
    if timeout_ms is None:
        return False
    return (time.perf_counter() - start) * 1000.0 >= timeout_ms


def search_symbols_in_files(
    query: str,
    symbol_files: Sequence[Path],
    *,
    max_results: int = 20,
    timeout_ms: Optional[int] = 30000,
    max_file_bytes: int = 5_000_000,
) -> List[SearchResult]:
    query_lower = query.lower()
    query_words = _split_query_words(query)
    start = time.perf_counter()
    scored: List[tuple[SearchResult, float]] = []

    for symbol_file in symbol_files:
        if _timed_out(start, timeout_ms):
            break
        try:
            content = _read_limited_text(symbol_file, max_file_bytes)
        except OSError:
            continue

        lib_name = symbol_file.stem
        content_lower = content.lower()
        if query_words and not all(
            word in content_lower for word in query_words
        ):
            continue

        for match in re.finditer(
            r'\(symbol\s+"([^"]+)"(.*?)(?=\n\s*\(symbol|\n\)|\Z)',
            content,
            re.DOTALL,
        ):
            if _timed_out(start, timeout_ms):
                break
            symbol_name = match.group(1)
            symbol_block = match.group(2)
            description = _extract_property(
                symbol_block, r'(?:ki_description|Description)\s+"([^"]*)"'
            )
            keywords = _extract_property(
                symbol_block, r'ki_keywords\s+"([^"]*)"'
            )
            fp_filters = _extract_property(
                symbol_block,
                r'(?:ki_fp_filters|kifpfilters)\s+"([^"]*)"',
            )
            haystack = " ".join(
                [symbol_name, lib_name, description, keywords, fp_filters]
            ).lower()

            score = _calculate_name_score(
                symbol_name, query_lower, query_words, short_name_bonus=2
            )
            if description and query_lower in description.lower():
                score += 3.0
            if keywords and query_lower in keywords.lower():
                score += 2.0
            if fp_filters and query_lower in fp_filters.lower():
                score += 2.0
            for word in query_words:
                if word in haystack:
                    score += 1.0

            if score <= 0:
                continue

            result = SearchResult(
                kind="symbol",
                library=lib_name,
                name=symbol_name,
                path=str(symbol_file),
                score=score,
                identifier=f"{lib_name}:{symbol_name}",
                description=description,
                keywords=keywords,
                extra={"footprint_filters": fp_filters} if fp_filters else {},
            )
            scored.append((result, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    return [item[0] for item in scored[:max_results]]


def search_footprints_in_dirs(
    query: str,
    footprint_dirs: Sequence[Path],
    *,
    max_results: int = 20,
    timeout_ms: Optional[int] = 30000,
    max_file_bytes: int = 500_000,
) -> List[SearchResult]:
    query_lower = query.lower()
    query_words = _split_query_words(query)
    start = time.perf_counter()
    scored: List[tuple[SearchResult, float]] = []

    for lib_dir in footprint_dirs:
        if _timed_out(start, timeout_ms):
            break
        lib_name = lib_dir.name.replace(".pretty", "")
        try:
            filenames = [
                path
                for path in lib_dir.iterdir()
                if path.suffix == ".kicad_mod"
            ]
        except OSError:
            continue

        filenames_text = " ".join(path.name for path in filenames).lower()
        if query_words and not any(
            word in filenames_text for word in query_words
        ):
            header_match = False
        else:
            header_match = True

        for file_path in filenames:
            if _timed_out(start, timeout_ms):
                break
            footprint_name = file_path.stem
            filename_lower = footprint_name.lower()
            filename_match_count = sum(
                1 for word in query_words if word in filename_lower
            )

            try:
                if filename_match_count >= len(query_words):
                    content = _read_limited_text(file_path, max_file_bytes)
                elif filename_match_count > 0 or header_match:
                    content = _read_limited_text(file_path, max_file_bytes)
                    header = content[:400].lower()
                    if query_words and not any(
                        word in header for word in query_words
                    ):
                        continue
                else:
                    continue
            except OSError:
                continue

            description = _extract_property(content, r'\(descr\s+"([^"]*)"')
            tags = _extract_property(content, r'\(tags\s+"([^"]*)"')
            models = " ".join(re.findall(r'\(model\s+"([^"]*)"', content))
            pads = " ".join(
                re.findall(r'\(pad\s+"?([^"\s)]+)"?', content)[:20]
            )
            haystack = " ".join(
                [
                    footprint_name,
                    lib_name,
                    description,
                    tags,
                    models,
                    pads,
                ]
            ).lower()

            score = _calculate_name_score(
                footprint_name, query_lower, query_words, short_name_bonus=4
            )
            if description and query_lower in description.lower():
                score += 3.0
            if tags and query_lower in tags.lower():
                score += 2.0
            for word in query_words:
                if word in haystack:
                    score += 1.0

            if score <= 0:
                continue

            model_path = models.split()[0] if models else ""
            result = SearchResult(
                kind="footprint",
                library=lib_name,
                name=footprint_name,
                path=str(file_path),
                score=score,
                identifier=f"{lib_name}:{footprint_name}",
                description=description,
                tags=tags,
                model_path=model_path,
            )
            scored.append((result, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    return [item[0] for item in scored[:max_results]]


def search_models_in_roots(
    query: str,
    model_roots: Sequence[Path],
    *,
    max_results: int = 20,
    timeout_ms: Optional[int] = 30000,
) -> List[SearchResult]:
    query_lower = query.lower()
    query_words = _split_query_words(query)
    start = time.perf_counter()
    scored: List[tuple[SearchResult, float]] = []

    for root in model_roots:
        if _timed_out(start, timeout_ms):
            break
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if _timed_out(start, timeout_ms):
                break
            if not path.is_file():
                continue
            if path.suffix.lower() not in MODEL_EXTENSIONS:
                continue
            try:
                rel_path = path.relative_to(root)
                rel_text = str(rel_path)
            except ValueError:
                rel_text = path.name
            haystack = rel_text.lower()
            if query_words and not any(
                word in haystack for word in query_words
            ):
                continue

            library = path.parent.name
            if library.endswith(".3dshapes"):
                library = library[: -len(".3dshapes")]

            score = _calculate_name_score(
                path.stem, query_lower, query_words, short_name_bonus=6
            )
            for word in query_words:
                if word in haystack:
                    score += 1.0

            if score <= 0:
                continue

            identifier = f"${{KIPRJMOD}}/libs/3dmodels/{rel_text}"
            if "libs/3dmodels" not in str(root):
                identifier = f"${{KICAD10_3DMODEL_DIR}}/{rel_text}"

            result = SearchResult(
                kind="model",
                library=library,
                name=path.name,
                path=str(path),
                score=score,
                identifier=identifier,
                model_path=str(path),
            )
            scored.append((result, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    return [item[0] for item in scored[:max_results]]


def build_summary(
    query: str,
    kind: str,
    results: Sequence[SearchResult],
) -> str:
    if not results:
        return f"No {kind} matches found for '{query}'."
    top = results[:3]
    parts = [f"{item.identifier}" for item in top]
    suffix = ""
    if len(results) > 3:
        suffix = f" (+{len(results) - 3} more)"
    return (
        f"Found {len(results)} {kind} result(s) for '{query}': "
        + ", ".join(parts)
        + suffix
    )


def run_search(
    *,
    kind: SearchKind,
    query: str,
    platform: Platform,
    project_dir: str = ".",
    include_project_local: bool = True,
    symbol_dirs: Optional[Sequence[str]] = None,
    footprint_dirs: Optional[Sequence[str]] = None,
    model_dirs: Optional[Sequence[str]] = None,
    max_results: int = 20,
    timeout_ms: int = 30000,
    max_file_bytes: int = 5_000_000,
) -> Dict[str, Any]:
    start = time.perf_counter()
    project_path = Path(project_dir).expanduser().resolve()
    warnings: List[str] = []
    searched_roots: Dict[str, List[str]] = {
        "symbols": [],
        "footprints": [],
        "models": [],
    }
    all_results: List[SearchResult] = []

    per_kind = max_results if kind != "all" else max(5, max_results // 3 or 5)

    if kind in {"symbol", "all"}:
        symbol_files, symbol_warnings = resolve_symbol_roots(
            platform,
            project_dir=project_path,
            include_project_local=include_project_local,
            extra_dirs=symbol_dirs,
        )
        warnings.extend(symbol_warnings)
        searched_roots["symbols"] = [str(path) for path in symbol_files[:50]]
        symbol_results = search_symbols_in_files(
            query,
            symbol_files,
            max_results=per_kind if kind == "symbol" else per_kind,
            timeout_ms=timeout_ms,
            max_file_bytes=max_file_bytes,
        )
        all_results.extend(symbol_results)

    if kind in {"footprint", "all"}:
        footprint_lib_dirs, footprint_warnings = resolve_footprint_roots(
            platform,
            project_dir=project_path,
            include_project_local=include_project_local,
            extra_dirs=footprint_dirs,
        )
        warnings.extend(footprint_warnings)
        searched_roots["footprints"] = [
            str(path) for path in footprint_lib_dirs[:50]
        ]
        footprint_results = search_footprints_in_dirs(
            query,
            footprint_lib_dirs,
            max_results=per_kind if kind == "footprint" else per_kind,
            timeout_ms=timeout_ms,
            max_file_bytes=min(max_file_bytes, 500_000),
        )
        all_results.extend(footprint_results)

    if kind in {"model", "all"}:
        model_roots, model_warnings = resolve_model_roots(
            platform,
            project_dir=project_path,
            include_project_local=include_project_local,
            extra_dirs=model_dirs,
        )
        warnings.extend(model_warnings)
        searched_roots["models"] = [str(path) for path in model_roots[:50]]
        model_results = search_models_in_roots(
            query,
            model_roots,
            max_results=per_kind if kind == "model" else per_kind,
            timeout_ms=timeout_ms,
        )
        all_results.extend(model_results)

    if kind == "all":
        all_results.sort(key=lambda item: item.score, reverse=True)
        all_results = all_results[:max_results]

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    result_dicts = [item.to_dict() for item in all_results]
    summary_kind = kind if kind != "all" else "library"
    return {
        "summary": build_summary(query, summary_kind, all_results),
        "query": query,
        "kind": kind,
        "platform": platform,
        "project_dir": str(project_path),
        "searched_roots": searched_roots,
        "results": result_dicts,
        "warnings": warnings,
        "elapsed_ms": elapsed_ms,
    }

import argparse
import json
import sys
from typing import List, Optional, Sequence



def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search KiCad symbol, footprint, and 3D model libraries."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser(
        "search", help="Search installed and project-local KiCad libraries."
    )
    search.add_argument(
        "--kind",
        choices=["symbol", "footprint", "model", "all"],
        default="all",
        help="Library kind to search.",
    )
    search.add_argument("--query", required=True, help="Search query.")
    search.add_argument(
        "--platform",
        choices=["win", "mac", "linux"],
        required=True,
        help="Host platform for default KiCad install paths.",
    )
    search.add_argument(
        "--project-dir",
        default=".",
        help="Project root used for project-local libraries.",
    )
    search.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="Maximum number of results to return.",
    )
    search.add_argument(
        "--timeout-ms",
        type=int,
        default=30000,
        help="Soft timeout budget in milliseconds.",
    )
    search.add_argument(
        "--max-file-bytes",
        type=int,
        default=5_000_000,
        help="Maximum bytes to read from a single library file.",
    )
    search.add_argument(
        "--symbol-dir",
        action="append",
        default=[],
        help="Extra symbol file or directory to search.",
    )
    search.add_argument(
        "--footprint-dir",
        action="append",
        default=[],
        help="Extra footprint .pretty directory to search.",
    )
    search.add_argument(
        "--model-dir",
        action="append",
        default=[],
        help="Extra 3D model root directory to search.",
    )
    search.add_argument(
        "--no-project-local",
        action="store_true",
        help="Skip project-local symbol, footprint, and model libraries.",
    )

    selftest = subparsers.add_parser(
        "selftest",
        help="Validate standalone script imports, parser wiring, and defaults.",
    )
    selftest.add_argument(
        "--platform",
        choices=["win", "mac", "linux"],
        required=True,
        help="Host platform for default KiCad install paths.",
    )
    selftest.add_argument(
        "--project-dir",
        default=".",
        help="Project root used for project-local library resolution checks.",
    )
    return parser


def run_selftest(platform: Platform, project_dir: str) -> dict:
    payload = run_search(
        kind="symbol",
        query="__copperpilot_selftest__",
        platform=platform,
        project_dir=project_dir,
        include_project_local=False,
        symbol_dirs=[],
        footprint_dirs=[],
        model_dirs=[],
        max_results=1,
        timeout_ms=1000,
        max_file_bytes=1024,
    )
    return {
        "success": True,
        "platform": platform,
        "project_dir": project_dir,
        "defaults": {
            "symbol_dir": str(default_symbol_dir(platform)),
            "footprint_dir": str(default_footprint_dir(platform)),
            "model_dir": str(default_model_dir(platform)),
        },
        "search_ok": isinstance(payload, dict)
        and payload.get("kind") == "symbol",
    }


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "selftest":
        payload = run_selftest(args.platform, args.project_dir)
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0 if payload.get("success") else 1

    if args.command != "search":
        parser.error(f"Unsupported command: {args.command}")
        return 2

    payload = run_search(
        kind=args.kind,
        query=args.query,
        platform=args.platform,
        project_dir=args.project_dir,
        include_project_local=not args.no_project_local,
        symbol_dirs=_non_empty(args.symbol_dir),
        footprint_dirs=_non_empty(args.footprint_dir),
        model_dirs=_non_empty(args.model_dir),
        max_results=args.max_results,
        timeout_ms=args.timeout_ms,
        max_file_bytes=args.max_file_bytes,
    )
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _non_empty(values: List[str]) -> Optional[List[str]]:
    cleaned = [value for value in values if value]
    return cleaned or None


def main() -> None:
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
