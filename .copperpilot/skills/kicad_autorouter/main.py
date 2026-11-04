#!/usr/bin/env python3
"""KiCad FreeRouting autorouter skill installed by CopperPilot."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Literal, Optional

Platform = Literal["win", "mac", "linux"]

DEFAULT_SKILL_MAIN_PY = ".copperpilot/skills/kicad_autorouter/main.py"

DEFAULT_FREEROUTING_VERSION = "2.2.4"
MIN_JAVA_MAJOR = 25


def default_freerouting_url(version: str = DEFAULT_FREEROUTING_VERSION) -> str:
    return (
        f"https://github.com/freerouting/freerouting/releases/download/"
        f"v{version}/freerouting-{version}.jar"
    )


def default_freerouting_jar_name(
    version: str = DEFAULT_FREEROUTING_VERSION,
) -> str:
    return f"freerouting-{version}.jar"


def default_skill_cache_dir(project_dir: Path) -> Path:
    return project_dir / ".copperpilot" / "skills" / "kicad_autorouter" / "cache"


def pcbnew_sys_path_candidates(platform: Platform) -> List[Path]:
    """Candidate directories to prepend to sys.path for importing pcbnew."""
    env = os.environ.get("KICAD_PYTHON_SITE_PACKAGES")
    candidates: List[Path] = []
    if env:
        candidates.append(Path(env))

    if platform == "mac":
        candidates.extend(
            [
                Path(
                    "/Applications/KiCad/KiCad.app/Contents/Frameworks/"
                    "Python.framework/Versions/Current/lib/python3.11/"
                    "site-packages"
                ),
                Path(
                    "/Applications/KiCad/KiCad.app/Contents/Frameworks/"
                    "Python.framework/Versions/3.11/lib/python3.11/"
                    "site-packages"
                ),
            ]
        )
    elif platform == "win":
        candidates.extend(
            [
                Path(r"C:\Program Files\KiCad\10.0\bin\Lib\site-packages"),
                Path(r"C:\Program Files\KiCad\9.0\bin\Lib\site-packages"),
            ]
        )
    else:
        candidates.extend(
            [
                Path("/usr/lib/kicad/lib/python3/dist-packages"),
                Path("/usr/lib/kicad/lib/python3/site-packages"),
                Path("/usr/share/kicad/scripting/plugins"),
            ]
        )
    return candidates


def kicad_bundled_python_candidates(platform: Platform) -> List[Path]:
    """Candidate KiCad-bundled Python executables for importing pcbnew."""
    env = os.environ.get("KICAD_PYTHON")
    candidates: List[Path] = []
    if env:
        candidates.append(Path(env))

    if platform == "mac":
        framework_root = Path(
            "/Applications/KiCad/KiCad.app/Contents/Frameworks/"
            "Python.framework/Versions"
        )
        version_dirs = ["Current", "3.11", "3.10", "3.9"]
        for version in version_dirs:
            base = framework_root / version / "bin"
            candidates.extend(
                [
                    base / "python3",
                    base / "python3.11",
                    base / "python3.10",
                    base / "python3.9",
                ]
            )
    elif platform == "win":
        for version in ("10.0", "9.0", "8.0"):
            candidates.extend(
                [
                    Path(rf"C:\Program Files\KiCad\{version}\bin\python.exe"),
                    Path(rf"C:\Program Files\KiCad\{version}\bin\python3.exe"),
                ]
            )
    else:
        candidates.extend(
            [
                Path("/usr/bin/python3"),
                Path("/usr/share/kicad/bin/python3"),
                Path("/usr/share/kicad/bin/python"),
            ]
        )

    deduped: List[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def kicad_cli_candidates(platform: Platform) -> List[str]:
    """Candidate kicad-cli executables for local post-route actions."""
    if platform == "mac":
        return [
            "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
            "/opt/homebrew/bin/kicad-cli",
            "/usr/local/bin/kicad-cli",
            "kicad-cli",
        ]
    if platform == "win":
        return [
            r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe",
            r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe",
            r"C:\Program Files\KiCad\8.0\bin\kicad-cli.exe",
            "kicad-cli.exe",
            "kicad-cli",
        ]
    return [
        "/usr/bin/kicad-cli",
        "/usr/local/bin/kicad-cli",
        "/app/bin/kicad-cli",
        "kicad-cli",
    ]


def resolve_project_path(
    value: Optional[str | Path],
    project_dir: Path,
) -> Optional[Path]:
    """Resolve a user path relative to project_dir unless already absolute."""
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return (project_dir / path).resolve()


def quote_shell_arg(value: str) -> str:
    if not value:
        return '""'
    if any(ch.isspace() for ch in value) or '"' in value:
        return '"' + value.replace('"', '\\"') + '"'
    return value


def build_skill_command(
    python_executable: Path,
    *,
    subcommand: str,
    platform: Platform,
    script_path: str = DEFAULT_SKILL_MAIN_PY,
    project_dir: Optional[str] = None,
    pcb_path: Optional[str] = None,
    java_bin: str = "java",
) -> str:
    parts = [
        quote_shell_arg(str(python_executable)),
        quote_shell_arg(script_path),
    ]
    parts.append(subcommand)
    parts.extend(["--platform", platform])
    if subcommand == "route":
        parts.extend(["--project-dir", quote_shell_arg(project_dir or ".")])
        if pcb_path is not None:
            parts.extend(["--pcb", quote_shell_arg(pcb_path)])
    if java_bin != "java":
        parts.extend(["--java-bin", quote_shell_arg(java_bin)])
    return " ".join(parts)


def get_platform_defaults(
    platform: Platform,
    *,
    freerouting_version: str = DEFAULT_FREEROUTING_VERSION,
) -> Dict[str, str]:
    return {
        "platform": platform,
        "freerouting_version": freerouting_version,
        "freerouting_url": default_freerouting_url(freerouting_version),
        "freerouting_jar_name": default_freerouting_jar_name(freerouting_version),
        "skill_cache_dir": ".copperpilot/skills/kicad_autorouter/cache",
        "pcbnew_site_paths": ", ".join(
            str(path) for path in pcbnew_sys_path_candidates(platform)
        ),
        "kicad_bundled_python_paths": ", ".join(
            str(path) for path in kicad_bundled_python_candidates(platform)
        ),
        "java_bin": "java",
    }

import contextlib
import importlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

BoardUpdateStrategy = Literal["greedy", "global", "hybrid"]
ItemSelectionStrategy = Literal["sequential", "random", "prioritized"]
FreeRoutingLogLevel = Literal[
    "ALL",
    "CONFIG",
    "FINE",
    "FINER",
    "FINEST",
    "INFO",
    "OFF",
    "SEVERE",
    "WARNING",
]


@dataclass
class FreeRoutingOptions:
    """Structured FreeRouting CLI options for headless autorouting."""

    headless: bool = True
    autorouter_passes: Optional[int] = None
    post_route_passes: Optional[int] = None
    fanout: bool = False
    threads: Optional[int] = None
    optimization_threshold: Optional[float] = None
    board_update_strategy: Optional[BoardUpdateStrategy] = None
    hybrid_ratio: Optional[float] = None
    item_selection_strategy: Optional[ItemSelectionStrategy] = None
    ignore_net_classes: List[str] = field(default_factory=list)
    rules_file: Optional[Path] = None
    save_intermediate: bool = False
    language: Optional[str] = None
    dialog_timeout: Optional[int] = None
    disable_analytics: bool = False
    disable_logging: bool = False
    log_level: Optional[FreeRoutingLogLevel] = None
    trace: bool = False
    experimental: bool = False
    extra_args: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "headless": self.headless,
            "fanout": self.fanout,
            "save_intermediate": self.save_intermediate,
            "disable_analytics": self.disable_analytics,
            "disable_logging": self.disable_logging,
            "trace": self.trace,
            "experimental": self.experimental,
            "ignore_net_classes": list(self.ignore_net_classes),
            "extra_args": list(self.extra_args),
        }
        if self.autorouter_passes is not None:
            payload["autorouter_passes"] = self.autorouter_passes
        if self.post_route_passes is not None:
            payload["post_route_passes"] = self.post_route_passes
        if self.threads is not None:
            payload["threads"] = self.threads
        if self.optimization_threshold is not None:
            payload["optimization_threshold"] = self.optimization_threshold
        if self.board_update_strategy is not None:
            payload["board_update_strategy"] = self.board_update_strategy
        if self.hybrid_ratio is not None:
            payload["hybrid_ratio"] = self.hybrid_ratio
        if self.item_selection_strategy is not None:
            payload["item_selection_strategy"] = self.item_selection_strategy
        if self.rules_file is not None:
            payload["rules_file"] = str(self.rules_file)
        if self.language is not None:
            payload["language"] = self.language
        if self.dialog_timeout is not None:
            payload["dialog_timeout"] = self.dialog_timeout
        if self.log_level is not None:
            payload["log_level"] = self.log_level
        return payload


def build_freerouting_command(
    *,
    java_bin: str,
    jar_path: Path,
    dsn_path: Path,
    ses_path: Path,
    options: Optional[FreeRoutingOptions] = None,
) -> Tuple[List[str], Dict[str, Any], List[str]]:
    """Compose the FreeRouting Java command.

    Returns cmd, options payload, and warnings.
    """
    opts = options or FreeRoutingOptions()
    warnings: List[str] = []
    cmd: List[str] = [java_bin]

    if opts.headless:
        cmd.append("-Djava.awt.headless=true")

    cmd.extend(["-jar", str(jar_path)])

    if opts.headless:
        cmd.append("--gui.enabled=false")

    cmd.extend(["-de", str(dsn_path)])

    if opts.rules_file is not None:
        cmd.extend(["-dr", str(opts.rules_file)])

    cmd.extend(["-do", str(ses_path)])

    if opts.fanout:
        cmd.append("-fo")

    if opts.autorouter_passes is not None:
        cmd.extend(["-ap", str(opts.autorouter_passes)])

    if opts.post_route_passes is not None:
        cmd.extend(["-pp", str(opts.post_route_passes)])

    if opts.threads is not None:
        cmd.extend(["-mt", str(opts.threads)])

    if opts.optimization_threshold is not None:
        cmd.extend(["-oit", str(opts.optimization_threshold)])

    if opts.board_update_strategy is not None:
        cmd.extend(["-us", opts.board_update_strategy])

    if opts.hybrid_ratio is not None:
        cmd.extend(["-hr", str(opts.hybrid_ratio)])

    if opts.item_selection_strategy is not None:
        cmd.extend(["-is", opts.item_selection_strategy])

    for net_class in opts.ignore_net_classes:
        cmd.extend(["-inc", net_class])
        warnings.append(
            f"Net class '{net_class}' excluded from autorouting via -inc. "
            "FreeRouting CLI excludes net classes; it cannot route only "
            "individual nets or pads."
        )

    if opts.save_intermediate:
        cmd.append("-im")

    if opts.language is not None:
        cmd.extend(["-l", opts.language])

    if opts.dialog_timeout is not None:
        cmd.extend(["-dct", str(opts.dialog_timeout)])

    if opts.disable_analytics:
        cmd.append("-da")

    if opts.disable_logging:
        cmd.append("-dl")

    if opts.log_level is not None:
        cmd.extend(["-ll", opts.log_level])

    if opts.trace:
        cmd.append("-trace")

    if opts.experimental:
        cmd.append("-test")

    extras, extra_warnings = sanitize_extra_freerouting_args(opts.extra_args)
    warnings.extend(extra_warnings)
    cmd.extend(extras)

    return cmd, opts.to_dict(), warnings


_PROTECTED_EXTRA_FLAGS = ("-dr", "--rules-file")


def sanitize_extra_freerouting_args(
    extras: Optional[Sequence[str]],
) -> Tuple[List[str], List[str]]:
    """Drop protected physical-rule flags from JAR passthrough."""
    allowed: List[str] = []
    warnings: List[str] = []
    items = [str(item) for item in (extras or [])]
    skip_next = False
    for index, token in enumerate(items):
        if skip_next:
            skip_next = False
            continue
        lowered = token.lower()
        blocked = any(
            lowered == flag or lowered.startswith(f"{flag}=")
            for flag in _PROTECTED_EXTRA_FLAGS
        )
        if blocked:
            warnings.append(
                "Dropped protected extra FreeRouting arg "
                f"{token!r}; use named --rules-file only after "
                "ask_user_question (physical constraints)."
            )
            if "=" not in token and index + 1 < len(items):
                nxt = items[index + 1]
                if not nxt.startswith("-"):
                    skip_next = True
            continue
        allowed.append(token)
    return allowed, warnings


class FreeRoutingError(RuntimeError):
    """FreeRouting failed; ``summary`` keeps command, tails, telemetry."""

    def __init__(self, message: str, summary: Dict[str, Any]):
        super().__init__(message)
        self.summary = summary


def parse_freerouting_stdout(stdout_text: str) -> Dict[str, Any]:
    """Extract pass/score/unrouted metrics from FreeRouting INFO stdout."""
    text = stdout_text or ""
    metrics: Dict[str, Any] = {
        "started_unrouted": None,
        "final_score": None,
        "final_unrouted": 0,
        "total_passes": 0,
        "cpu_seconds": None,
        "peak_heap_mb": None,
        "pass_history": [],
        "board_unchanged": False,
    }
    start_match = re.search(r"started with (\d+) unrouted nets", text)
    if start_match:
        metrics["started_unrouted"] = int(start_match.group(1))
    pass_matches = re.findall(
        r"pass #(\d+) completed in ([\d.]+) s, score of ([\d.]+)"
        r"(?: \((\d+) unrouted\))?",
        text,
    )
    for p_num, p_time, p_score, p_unrouted in pass_matches:
        metrics["pass_history"].append(
            {
                "pass": int(p_num),
                "time_sec": float(p_time),
                "score": float(p_score),
                "unrouted": int(p_unrouted) if p_unrouted else 0,
            }
        )
    final_match = re.search(
        r"finished after (\d+) passes, final score: ([\d.]+), using "
        r"([\d.]+) CPU seconds, ([\d.]+) MB peak heap",
        text,
    )
    if final_match:
        metrics["total_passes"] = int(final_match.group(1))
        metrics["final_score"] = float(final_match.group(2))
        metrics["cpu_seconds"] = float(final_match.group(3))
        metrics["peak_heap_mb"] = float(final_match.group(4))
    if metrics["pass_history"]:
        metrics["final_unrouted"] = metrics["pass_history"][-1]["unrouted"]
    elif metrics["started_unrouted"] is not None:
        metrics["final_unrouted"] = metrics["started_unrouted"]
    if re.search(r"Board state has not changed since pass", text):
        metrics["board_unchanged"] = True
    return metrics


def _decode_captured(blob: Any) -> str:
    if blob is None:
        return ""
    if isinstance(blob, bytes):
        return blob.decode("utf-8", errors="replace")
    return str(blob)


def _freerouting_proc_summary(
    *,
    cmd: List[str],
    options_payload: Dict[str, Any],
    option_warnings: List[str],
    returncode: Optional[int],
    stdout_text: str,
    stderr_text: str,
    elapsed: float,
) -> Dict[str, Any]:
    telemetry = parse_freerouting_stdout(stdout_text)
    return {
        "command": cmd,
        "freerouting_options": options_payload,
        "option_warnings": option_warnings,
        "returncode": returncode,
        "stdout_tail": (stdout_text or "")[-4000:],
        "stderr_tail": (stderr_text or "")[-4000:],
        "elapsed_sec": elapsed,
        "freerouting_telemetry": telemetry,
    }


def build_next_actions(
    telemetry: Optional[Dict[str, Any]] = None,
    *,
    timed_out: bool = False,
) -> List[str]:
    """Suggest allowed retunes; never auto-relax KiCad geometry."""
    tel = telemetry or {}
    history: List[Dict[str, Any]] = list(tel.get("pass_history") or [])
    final_unrouted = int(tel.get("final_unrouted") or 0)
    final_score = tel.get("final_score")
    actions: List[str] = [
        "Java exit 0 / status routed means SES imported or the process "
        "finished, not 100% connected. Inspect freerouting_telemetry, "
        "then run run_drc and list_nets.",
    ]
    if timed_out:
        actions.append(
            "Subprocess --timeout-sec elapsed. Re-run with a larger "
            "--timeout-sec and/or fewer --autorouter-passes; keep headless."
        )
    scores = [float(item.get("score") or 0) for item in history]
    if tel.get("board_unchanged") or (
        final_score is not None and float(final_score) <= 0.01 and final_unrouted > 0
    ):
        actions.append(
            "Telemetry looks geometrically infeasible (score ~0 or board "
            "unchanged). Stop mutating. RCA then ask_user_question with "
            "DFM-backed numbers. Do not silently enlarge Edge.Cuts or "
            "relax KiCad rules."
        )
    elif len(scores) >= 3:
        oscillating = False
        for index in range(2, len(scores)):
            if (
                abs(scores[index] - scores[index - 2]) < 1.0
                and abs(scores[index] - scores[index - 1]) > 20
            ):
                oscillating = True
                break
        rising = all(
            scores[index] + 0.01 >= scores[index - 1] for index in range(1, len(scores))
        )
        if oscillating and final_unrouted > 0:
            actions.append(
                "Score oscillation / rip-up thrashing: retry with "
                "--item-selection-strategy random. Engine-only extras "
                "(via/ripup costs) are allowed if the JAR accepts them."
            )
        elif rising and final_unrouted > 0:
            actions.append(
                "Pass starvation: score still rising with unrouted nets. "
                "Increase --autorouter-passes and --timeout-sec."
            )
        elif final_unrouted > 0 and len(set(round(s, 1) for s in scores[-3:])) == 1:
            actions.append(
                "Early plateau on incomplete routing: try "
                "--board-update-strategy hybrid, --hybrid-ratio, and "
                "--fanout."
            )
    if final_unrouted == 0 and history:
        actions.append(
            "Telemetry shows 0 unrouted nets. If DRC still fails, add "
            "--post-route-passes; do not invent copper."
        )
    elif final_unrouted > 0:
        actions.append(
            "Retune allowed flags in order: strategy "
            "(-us/-is/-hr), then --fanout/--threads, then "
            "--autorouter-passes/--timeout-sec/--post-route-passes."
        )
    actions.append(
        "Do not relax KiCad rules, --rules-file, Edge.Cuts, stackup, or "
        "via/track geometry as a routing lever without exhausted "
        "hyperparameter retries, RCA, DFM evidence, and ask_user_question."
    )
    return actions


@dataclass
class AutorouteResult:
    status: str
    pcb_path: str
    dsn_path: str
    ses_path: str
    jar_path: str
    output_pcb_path: str
    segment_count_before: int
    segment_count_after: int
    timings_sec: Dict[str, float] = field(default_factory=dict)
    commands: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    native_stdout_tail: Optional[str] = None
    native_stderr_tail: Optional[str] = None
    drc_summary: Optional[Dict[str, Any]] = None
    refill_zones: Optional[Dict[str, Any]] = None
    freerouting_telemetry: Optional[Dict[str, Any]] = None
    next_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "status": self.status,
            "pcb_path": self.pcb_path,
            "dsn_path": self.dsn_path,
            "ses_path": self.ses_path,
            "jar_path": self.jar_path,
            "output_pcb_path": self.output_pcb_path,
            "segment_count_before": self.segment_count_before,
            "segment_count_after": self.segment_count_after,
            "timings_sec": self.timings_sec,
            "commands": self.commands,
            "warnings": self.warnings,
            "notes": self.notes,
            "next_actions": list(self.next_actions),
        }
        if self.native_stdout_tail:
            payload["native_stdout_tail"] = self.native_stdout_tail
        if self.native_stderr_tail:
            payload["native_stderr_tail"] = self.native_stderr_tail
        if self.drc_summary is not None:
            payload["drc_summary"] = self.drc_summary
        if self.refill_zones is not None:
            payload["refill_zones"] = self.refill_zones
        if self.freerouting_telemetry is not None:
            payload["freerouting_telemetry"] = self.freerouting_telemetry
        return payload


def count_pcb_segments(pcb_path: Path) -> int:
    text = pcb_path.read_text(encoding="utf-8", errors="replace")
    return len(re.findall(r"^\s*\(segment\b", text, flags=re.MULTILINE))


def _prepend_sys_paths(candidates: Sequence[Path]) -> List[str]:
    added: List[str] = []
    for candidate in candidates:
        path_str = str(candidate.expanduser())
        if path_str not in sys.path and candidate.exists():
            sys.path.insert(0, path_str)
            added.append(path_str)
    return added


def import_pcbnew(platform: Platform) -> Tuple[Any, List[str], List[str]]:
    """Import pcbnew, probing platform-specific KiCad Python paths first."""
    tried: List[str] = []
    warnings: List[str] = []
    first_error: Optional[ImportError] = None

    _prepend_sys_paths(pcbnew_sys_path_candidates(platform))
    tried.extend(str(path) for path in pcbnew_sys_path_candidates(platform))

    try:
        return importlib.import_module("pcbnew"), tried, warnings
    except ImportError as exc:
        first_error = exc
        warnings.append(f"Initial pcbnew import failed: {exc}")

    # Some installs only expose pcbnew when launched with KiCad's
    # bundled python.
    for candidate in pcbnew_sys_path_candidates(platform):
        if not candidate.exists():
            continue
        warnings.append(
            "pcbnew is not importable from the current Python interpreter. "
            "Run this skill with KiCad's bundled Python when available."
        )
        break

    guidance = (
        "KiCad pcbnew module is unavailable. Install KiCad and run this "
        "script with KiCad's bundled Python, or set "
        "KICAD_PYTHON_SITE_PACKAGES to the "
        "directory containing pcbnew. Do not pip install pcbnew. "
        "KiCad 10 removed `kicad-cli pcb export specctradsn`; use "
        "pcbnew.ExportSpecctraDSN instead."
    )
    raise RuntimeError(guidance) from first_error


def _python_can_import_pcbnew(
    python_executable: Path,
    platform: Platform,
) -> Tuple[bool, str]:
    """Return whether a Python executable can import pcbnew."""
    if not python_executable.is_file():
        return False, "executable not found"

    site_paths = [
        str(path.expanduser())
        for path in pcbnew_sys_path_candidates(platform)
        if path.exists()
    ]
    probe = (
        "import importlib, sys\n"
        f"paths = {site_paths!r}\n"
        "for path in paths:\n"
        "    if path not in sys.path:\n"
        "        sys.path.insert(0, path)\n"
        "importlib.import_module('pcbnew')\n"
        "print('ok')\n"
    )
    proc = subprocess.run(
        [str(python_executable), "-c", probe],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if proc.returncode == 0 and "ok" in proc.stdout:
        return True, "import ok"
    detail = (proc.stderr or proc.stdout or "import failed").strip()
    return False, detail[-500:]


def discover_recommended_python(
    platform: Platform,
) -> Tuple[Optional[Path], List[Dict[str, str]]]:
    """Find the first KiCad bundled Python that can import pcbnew."""
    probes: List[Dict[str, str]] = []
    for candidate in kicad_bundled_python_candidates(platform):
        ok, detail = _python_can_import_pcbnew(candidate, platform)
        probes.append(
            {
                "python": str(candidate),
                "available": str(ok).lower(),
                "detail": detail,
            }
        )
        if ok:
            return candidate, probes
    return None, probes


def _diagnose_guidance_notes(
    *,
    platform: Platform,
    pcbnew_ok: bool,
    recommended_python: Optional[Path],
) -> List[str]:
    notes = [
        "Run route only after Java and KiCad pcbnew are available.",
        "Use fill_pcb_zones after importing SES routes.",
        "KiCad 10 removed `kicad-cli pcb export specctradsn`; this skill uses "
        "pcbnew.ExportSpecctraDSN and pcbnew.ImportSpecctraSES.",
    ]
    if not pcbnew_ok:
        notes.append(
            "The current Python interpreter cannot import pcbnew. "
            "Run diagnose first and use recommended_python when provided."
        )
        if platform == "mac" and recommended_python is not None:
            notes.append(
                "On macOS, prefer KiCad bundled Python at " f"{recommended_python}."
            )
    return notes


def tail_text(text: str, limit: int = 4000) -> str:
    if not text:
        return ""
    return text[-limit:]


@contextlib.contextmanager
def capture_native_streams():
    """Capture native stdout/stderr emitted during pcbnew operations."""
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(
        stderr_capture
    ):
        yield stdout_capture, stderr_capture


_JAVA_VERSION = re.compile(r'version "(?:1\.)?(\d+)')


def resolve_java_bin(java_bin: str = "java") -> str:
    """Prefer CopperPilot's managed Java when the caller left the default."""
    explicit = (java_bin or "").strip() or "java"
    if explicit != "java":
        return explicit
    managed = os.environ.get("COPPERPILOT_JAVA", "").strip()
    return managed or "java"


def java_major_from_output(text: str) -> Optional[int]:
    match = _JAVA_VERSION.search(text or "")
    if not match:
        return None
    return int(match.group(1))


def ensure_java(java_bin: str = "java") -> str:
    java_bin = resolve_java_bin(java_bin)
    resolved = shutil.which(java_bin) or java_bin
    proc = subprocess.run(
        [resolved, "-version"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Java runtime check failed for '{java_bin}'. "
            f"Java {MIN_JAVA_MAJOR}+ is required."
        )
    major = java_major_from_output((proc.stderr or "") + (proc.stdout or ""))
    if major is None or major < MIN_JAVA_MAJOR:
        found = "unknown" if major is None else str(major)
        raise RuntimeError(
            f"Java {MIN_JAVA_MAJOR}+ is required (found {found}) " f"for '{resolved}'."
        )
    return resolved


def _validate_downloaded_jar(dest: Path, url: str) -> None:
    if not dest.is_file() or dest.stat().st_size == 0:
        raise RuntimeError(
            f"Downloaded FreeRouting JAR from {url} was empty or missing."
        )


def _download_jar_with_urllib(
    dest: Path,
    *,
    url: str,
    timeout_sec: int,
) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CopperPilot-KiCad-Autorouter/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout_sec) as response:
        data = response.read()
    if not data:
        raise RuntimeError(f"Downloaded FreeRouting JAR from {url} was empty.")
    dest.write_bytes(data)


def _download_jar_with_curl(
    dest: Path,
    *,
    url: str,
    timeout_sec: int,
) -> None:
    curl = shutil.which("curl")
    if curl is None:
        raise RuntimeError("curl is not available on PATH")
    proc = subprocess.run(
        [
            curl,
            "-L",
            "--fail",
            "--silent",
            "--show-error",
            "--output",
            str(dest),
            url,
        ],
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"curl download failed with exit code {proc.returncode}: "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )


def _download_jar_with_wget(
    dest: Path,
    *,
    url: str,
    timeout_sec: int,
) -> None:
    wget = shutil.which("wget")
    if wget is None:
        raise RuntimeError("wget is not available on PATH")
    proc = subprocess.run(
        [wget, "-O", str(dest), url],
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"wget download failed with exit code {proc.returncode}: "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )


def download_freerouting_jar(
    dest: Path,
    *,
    url: str,
    timeout_sec: int = 120,
) -> Tuple[Path, Optional[str]]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 0:
        return dest, None

    errors: List[str] = []
    for downloader_name, downloader in (
        ("urllib", _download_jar_with_urllib),
        ("curl", _download_jar_with_curl),
        ("wget", _download_jar_with_wget),
    ):
        try:
            if dest.exists():
                dest.unlink()
            downloader(dest, url=url, timeout_sec=timeout_sec)
            _validate_downloaded_jar(dest, url)
            return dest, downloader_name
        except Exception as exc:  # noqa: BLE001 - try next downloader
            errors.append(f"{downloader_name}: {exc}")
            if dest.exists():
                try:
                    dest.unlink()
                except OSError:
                    pass

    raise RuntimeError(
        f"Failed to download FreeRouting JAR from {url}. "
        f"Tried urllib, curl, and wget. Details: {' | '.join(errors)}"
    )


def discover_kicad_cli(
    platform: Platform,
    explicit_path: Optional[str] = None,
) -> str:
    if explicit_path:
        return explicit_path
    for candidate in kicad_cli_candidates(platform):
        path = Path(candidate)
        if path.is_file():
            return str(path)
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError(
        "kicad-cli not found. Install KiCad or pass " "--kicad-cli-path explicitly."
    )


def summarize_drc_report(drc_data: Dict[str, Any]) -> Dict[str, Any]:
    violations = drc_data.get("violations", [])
    errors = sum(1 for item in violations if item.get("severity") == "error")
    warnings = sum(1 for item in violations if item.get("severity") == "warning")
    return {
        "report_type": "DRC",
        "total_violations": len(violations),
        "errors": errors,
        "warnings": warnings,
        "violations": violations,
        "kicad_version": drc_data.get("kicad_version", ""),
        "date": drc_data.get("date", ""),
        "unconnected_items": drc_data.get("unconnected_items", []),
    }


def run_kicad_cli_drc(
    *,
    platform: Platform,
    pcb_path: Path,
    project_dir: Path,
    cli_path: str,
    timeout_sec: int = 120,
) -> Dict[str, Any]:
    del platform
    drc_output = (
        default_skill_cache_dir(project_dir) / f"{pcb_path.stem}-post-route-drc.json"
    )
    drc_output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        cli_path,
        "pcb",
        "drc",
        "--format",
        "json",
        "--output",
        str(drc_output),
        str(pcb_path),
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    summary: Dict[str, Any] = {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout_tail": tail_text(proc.stdout),
        "stderr_tail": tail_text(proc.stderr),
        "output_path": str(drc_output),
    }
    if proc.returncode != 0:
        summary["status"] = "failed"
        return summary
    if not drc_output.is_file():
        summary["status"] = "failed"
        summary["error"] = f"DRC output not found at {drc_output}"
        return summary
    drc_data = json.loads(drc_output.read_text(encoding="utf-8"))
    summary.update(summarize_drc_report(drc_data))
    summary["status"] = "ok"
    return summary


def run_kicad_cli_refill_zones(
    *,
    platform: Platform,
    pcb_path: Path,
    cli_path: str,
    timeout_sec: int = 120,
) -> Dict[str, Any]:
    del platform
    cmd = [
        cli_path,
        "pcb",
        "drc",
        "--refill-zones",
        "--save-board",
        str(pcb_path),
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    return {
        "status": "ok" if proc.returncode == 0 else "failed",
        "command": cmd,
        "returncode": proc.returncode,
        "stdout_tail": tail_text(proc.stdout),
        "stderr_tail": tail_text(proc.stderr),
    }


def export_specctra_dsn(pcbnew_mod: Any, board_path: Path, dsn_path: Path) -> None:
    board = pcbnew_mod.LoadBoard(str(board_path))
    dsn_path.parent.mkdir(parents=True, exist_ok=True)

    export_fn = getattr(pcbnew_mod, "ExportSpecctraDSN", None)
    if export_fn is None:
        raise RuntimeError(
            "pcbnew.ExportSpecctraDSN is unavailable in this KiCad build. "
            "KiCad 10 removed `kicad-cli pcb export specctradsn`; use the "
            "pcbnew Python API instead."
        )

    try:
        ok = export_fn(board, str(dsn_path))
    except TypeError:
        ok = export_fn(str(dsn_path))

    if ok is False:
        raise RuntimeError(f"pcbnew.ExportSpecctraDSN failed for {board_path}")

    if not dsn_path.is_file() or dsn_path.stat().st_size == 0:
        raise RuntimeError(f"DSN export did not produce a non-empty file at {dsn_path}")


def run_freerouting(
    *,
    java_bin: str,
    jar_path: Path,
    dsn_path: Path,
    ses_path: Path,
    timeout_sec: int,
    options: Optional[FreeRoutingOptions] = None,
) -> Dict[str, Any]:
    ses_path.parent.mkdir(parents=True, exist_ok=True)
    cmd, options_payload, option_warnings = build_freerouting_command(
        java_bin=java_bin,
        jar_path=jar_path,
        dsn_path=dsn_path,
        ses_path=ses_path,
        options=options,
    )
    started = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        stdout_text = _decode_captured(exc.stdout)
        stderr_text = _decode_captured(exc.stderr)
        summary = _freerouting_proc_summary(
            cmd=cmd,
            options_payload=options_payload,
            option_warnings=option_warnings,
            returncode=None,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            elapsed=elapsed,
        )
        summary["timed_out"] = True
        raise FreeRoutingError(
            f"FreeRouting timed out after {timeout_sec}s "
            "(subprocess --timeout-sec; not FreeRouting -t).",
            summary,
        ) from exc
    elapsed = time.monotonic() - started
    summary = _freerouting_proc_summary(
        cmd=cmd,
        options_payload=options_payload,
        option_warnings=option_warnings,
        returncode=proc.returncode,
        stdout_text=proc.stdout or "",
        stderr_text=proc.stderr or "",
        elapsed=elapsed,
    )
    if proc.returncode != 0:
        raise FreeRoutingError(
            "FreeRouting failed with exit code "
            f"{proc.returncode}. stderr tail: {(proc.stderr or '')[-1000:]}",
            summary,
        )
    if not ses_path.is_file() or ses_path.stat().st_size == 0:
        raise FreeRoutingError(
            f"FreeRouting did not produce a non-empty SES at {ses_path}",
            summary,
        )
    return summary


def import_specctra_ses(
    pcbnew_mod: Any,
    board_path: Path,
    ses_path: Path,
    output_pcb_path: Path,
) -> None:
    board = pcbnew_mod.LoadBoard(str(board_path))
    import_fn = getattr(pcbnew_mod, "ImportSpecctraSES", None)
    if import_fn is None:
        raise RuntimeError(
            "pcbnew.ImportSpecctraSES is unavailable in this KiCad build. "
            "KiCad 10 removed `kicad-cli pcb export specctradsn`; use the "
            "pcbnew Python API instead."
        )

    import_fn(board, str(ses_path))
    output_pcb_path.parent.mkdir(parents=True, exist_ok=True)
    pcbnew_mod.SaveBoard(str(output_pcb_path), board)


def resolve_artifact_paths(
    *,
    pcb_path: Path,
    project_dir: Path,
    dsn_path: Optional[Path],
    ses_path: Optional[Path],
    jar_path: Optional[Path],
    freerouting_version: str,
    cache_dir: Optional[Path],
) -> Tuple[Path, Path, Path]:
    stem = pcb_path.stem
    scratch = cache_dir or default_skill_cache_dir(project_dir)
    resolved_dsn = dsn_path or (scratch / f"{stem}.dsn")
    resolved_ses = ses_path or (scratch / f"{stem}.ses")
    resolved_jar = jar_path or (
        scratch / default_freerouting_jar_name(freerouting_version)
    )
    return resolved_dsn, resolved_ses, resolved_jar


def run_autoroute(
    *,
    platform: Platform,
    pcb_path: Path,
    project_dir: Path,
    output_pcb_path: Optional[Path] = None,
    dsn_path: Optional[Path] = None,
    ses_path: Optional[Path] = None,
    jar_path: Optional[Path] = None,
    freerouting_version: str = "2.2.4",
    freerouting_url: Optional[str] = None,
    java_bin: str = "java",
    timeout_sec: int = 600,
    keep_artifacts: bool = True,
    cache_dir: Optional[Path] = None,
    freerouting_options: Optional[FreeRoutingOptions] = None,
    run_drc: bool = False,
    refill_zones: bool = False,
    kicad_cli_path: Optional[str] = None,
    kicad_cli_timeout_sec: int = 120,
) -> AutorouteResult:
    pcb_path = pcb_path.resolve()
    project_dir = project_dir.resolve()
    if not pcb_path.is_file():
        raise FileNotFoundError(str(pcb_path))

    resolved_dsn, resolved_ses, resolved_jar = resolve_artifact_paths(
        pcb_path=pcb_path,
        project_dir=project_dir,
        dsn_path=dsn_path,
        ses_path=ses_path,
        jar_path=jar_path,
        freerouting_version=freerouting_version,
        cache_dir=cache_dir,
    )
    output_path = (output_pcb_path or pcb_path).resolve()
    url = freerouting_url or default_freerouting_url(freerouting_version)

    timings: Dict[str, float] = {}
    commands: List[Dict[str, Any]] = []
    warnings: List[str] = []
    notes: List[str] = []

    segment_before = count_pcb_segments(pcb_path)

    t0 = time.monotonic()
    pcbnew_mod, _, import_warnings = import_pcbnew(platform)
    warnings.extend(import_warnings)
    timings["import_pcbnew_sec"] = time.monotonic() - t0

    t0 = time.monotonic()
    resolved_java = ensure_java(java_bin)
    timings["java_check_sec"] = time.monotonic() - t0

    t0 = time.monotonic()
    resolved_jar, downloader = download_freerouting_jar(
        resolved_jar,
        url=url,
        timeout_sec=min(timeout_sec, 120),
    )
    timings["download_jar_sec"] = time.monotonic() - t0
    notes.append(f"Using FreeRouting JAR at {resolved_jar}")
    if downloader is not None:
        notes.append(f"Downloaded FreeRouting JAR using {downloader}.")

    t0 = time.monotonic()
    export_specctra_dsn(pcbnew_mod, pcb_path, resolved_dsn)
    timings["export_dsn_sec"] = time.monotonic() - t0

    t0 = time.monotonic()
    route_summary = run_freerouting(
        java_bin=resolved_java,
        jar_path=resolved_jar,
        dsn_path=resolved_dsn,
        ses_path=resolved_ses,
        timeout_sec=timeout_sec,
        options=freerouting_options,
    )
    timings["freerouting_sec"] = route_summary["elapsed_sec"]
    commands.append(route_summary)
    warnings.extend(route_summary.get("option_warnings", []))
    telemetry = route_summary.get("freerouting_telemetry") or {}
    next_actions = build_next_actions(telemetry)

    t0 = time.monotonic()
    import_specctra_ses(pcbnew_mod, pcb_path, resolved_ses, output_path)
    timings["import_ses_sec"] = time.monotonic() - t0

    segment_after = count_pcb_segments(output_path)
    notes.append(
        "After import, run fill_pcb_zones / kicad-cli pcb drc --refill-zones "
        "to regenerate copper pours."
    )
    notes.append(
        "status: routed means SES imported, not 100% connected. "
        "segment_count_* is not connectivity. Inspect "
        "freerouting_telemetry (final_unrouted, pass_history) "
        "before waiting on later DRC."
    )

    drc_summary: Optional[Dict[str, Any]] = None
    refill_zones_summary: Optional[Dict[str, Any]] = None
    if refill_zones or run_drc:
        try:
            resolved_cli = discover_kicad_cli(platform, kicad_cli_path)
        except RuntimeError as exc:
            warnings.append(str(exc))
            resolved_cli = None

        if resolved_cli is not None and refill_zones:
            t0 = time.monotonic()
            refill_zones_summary = run_kicad_cli_refill_zones(
                platform=platform,
                pcb_path=output_path,
                cli_path=resolved_cli,
                timeout_sec=kicad_cli_timeout_sec,
            )
            timings["refill_zones_sec"] = time.monotonic() - t0
            commands.append(refill_zones_summary)
            if refill_zones_summary.get("status") != "ok":
                warnings.append(
                    "Zone refill failed; inspect refill_zones in the " "route JSON."
                )

        if resolved_cli is not None and run_drc:
            t0 = time.monotonic()
            drc_summary = run_kicad_cli_drc(
                platform=platform,
                pcb_path=output_path,
                project_dir=project_dir,
                cli_path=resolved_cli,
                timeout_sec=kicad_cli_timeout_sec,
            )
            timings["post_route_drc_sec"] = time.monotonic() - t0
            commands.append(drc_summary)
            if drc_summary.get("status") != "ok":
                warnings.append(
                    "Post-route DRC failed; inspect drc_summary in the " "route JSON."
                )

    if not keep_artifacts:
        for artifact in (resolved_dsn, resolved_ses):
            try:
                artifact.unlink(missing_ok=True)
            except OSError as exc:
                warnings.append(f"Could not delete artifact {artifact}: {exc}")

    return AutorouteResult(
        status="routed",
        pcb_path=str(pcb_path),
        dsn_path=str(resolved_dsn),
        ses_path=str(resolved_ses),
        jar_path=str(resolved_jar),
        output_pcb_path=str(output_path),
        segment_count_before=segment_before,
        segment_count_after=segment_after,
        timings_sec=timings,
        commands=commands,
        warnings=warnings,
        notes=notes,
        drc_summary=drc_summary,
        refill_zones=refill_zones_summary,
        freerouting_telemetry=telemetry,
        next_actions=next_actions,
    )


def diagnose_environment(
    *,
    platform: Platform,
    java_bin: str = "java",
    script_path: str = DEFAULT_SKILL_MAIN_PY,
    pcb_path: Optional[str] = None,
    project_dir: str = ".",
) -> Dict[str, Any]:
    java_ok = False
    java_detail = ""
    try:
        resolved = ensure_java(java_bin)
        java_ok = True
        java_detail = resolved
    except Exception as exc:  # noqa: BLE001 - diagnostic surface
        java_detail = str(exc)

    pcbnew_ok = False
    pcbnew_detail = ""
    tried_paths: List[str] = []
    try:
        _, tried_paths, _ = import_pcbnew(platform)
        pcbnew_ok = True
        pcbnew_detail = "import ok"
    except Exception as exc:  # noqa: BLE001 - diagnostic surface
        pcbnew_detail = str(exc)
        tried_paths = [str(path) for path in pcbnew_sys_path_candidates(platform)]

    recommended_python: Optional[Path] = None
    python_probes: List[Dict[str, str]] = []
    if not pcbnew_ok:
        recommended_python, python_probes = discover_recommended_python(platform)

    recommended_python_str = (
        str(recommended_python) if recommended_python is not None else None
    )
    recommended_diagnose_command = None
    recommended_route_command = None
    if recommended_python is not None:
        recommended_diagnose_command = build_skill_command(
            recommended_python,
            subcommand="diagnose",
            platform=platform,
            script_path=script_path,
            java_bin=java_bin,
        )
        recommended_route_command = build_skill_command(
            recommended_python,
            subcommand="route",
            platform=platform,
            script_path=script_path,
            project_dir=project_dir,
            pcb_path=pcb_path,
            java_bin=java_bin,
        )

    return {
        "status": "ok" if java_ok and pcbnew_ok else "missing_dependencies",
        "platform": platform,
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "java_available": java_ok,
        "java_detail": java_detail,
        "java_required": MIN_JAVA_MAJOR,
        "pcbnew_available": pcbnew_ok,
        "pcbnew_detail": pcbnew_detail,
        "pcbnew_site_paths": tried_paths,
        "recommended_python": recommended_python_str,
        "recommended_diagnose_command": recommended_diagnose_command,
        "recommended_route_command": recommended_route_command,
        "python_probes": python_probes,
        "notes": _diagnose_guidance_notes(
            platform=platform,
            pcbnew_ok=pcbnew_ok,
            recommended_python=recommended_python,
        ),
    }

import argparse
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run KiCad Specctra DSN export, FreeRouting, and SES import on "
            "the user's machine."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    route = subparsers.add_parser(
        "route",
        help="Export DSN, run FreeRouting, and import SES into the PCB.",
        description=(
            "Export Specctra DSN, run FreeRouting, and import SES. "
            "Headless by default "
            "(-Djava.awt.headless=true, --gui.enabled=false). "
            "Missing JARs are auto-downloaded and cached. "
            "--timeout-sec is the Java subprocess wall-clock bound, "
            "not FreeRouting -t. Java exit 0 / status routed means SES "
            "imported, not 100% connected; inspect "
            "freerouting_telemetry. Engine knobs "
            "(--autorouter-passes, strategies, fanout, threads) may be "
            "iterated freely. --rules-file is a protected physical "
            "constraint. --hybrid-ratio is a float (-hr)."
        ),
    )
    route.add_argument(
        "--platform",
        choices=["win", "mac", "linux"],
        required=True,
        help="Host platform for pcbnew path probing.",
    )
    route.add_argument(
        "--pcb",
        required=True,
        help=(
            "Path to the .kicad_pcb file. Relative paths resolve against "
            "--project-dir, not the shell CWD."
        ),
    )
    route.add_argument(
        "--project-dir",
        default=".",
        help="Project root used for cache/artifact paths and relative inputs.",
    )
    route.add_argument(
        "--output-pcb",
        default=None,
        help="Optional output PCB path. Defaults to overwriting --pcb.",
    )
    route.add_argument(
        "--dsn",
        default=None,
        help="Optional DSN output path. Defaults to skill cache directory.",
    )
    route.add_argument(
        "--ses",
        default=None,
        help="Optional SES output path. Defaults to skill cache directory.",
    )
    route.add_argument(
        "--jar-path",
        default=None,
        help="Optional FreeRouting JAR path. Defaults to cached skill JAR.",
    )
    route.add_argument(
        "--freerouting-version",
        default="2.2.4",
        help="FreeRouting release version used for default JAR naming/URL.",
    )
    route.add_argument(
        "--freerouting-url",
        default=None,
        help="Override FreeRouting JAR download URL.",
    )
    route.add_argument(
        "--java-bin",
        default=os.environ.get("COPPERPILOT_JAVA", "java"),
        help="Java executable used to run FreeRouting.",
    )
    route.add_argument(
        "--timeout-sec",
        type=int,
        default=600,
        help=(
            "Java subprocess wall-clock timeout in seconds (default 600). "
            "Not FreeRouting -t."
        ),
    )
    route.add_argument(
        "--cache-dir",
        default=None,
        help="Optional cache directory for DSN/SES/JAR artifacts.",
    )
    route.add_argument(
        "--keep-artifacts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep DSN/SES artifacts after a successful route.",
    )
    route.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Run FreeRouting headless (default). Use --no-headless only for "
            "local GUI debugging."
        ),
    )
    route.add_argument(
        "--autorouter-passes",
        type=int,
        default=None,
        metavar="N",
        help="FreeRouting -ap max autorouter passes.",
    )
    route.add_argument(
        "--post-route-passes",
        type=int,
        default=None,
        metavar="N",
        help="FreeRouting -pp max post-route optimization passes.",
    )
    route.add_argument(
        "--fanout",
        action="store_true",
        default=False,
        help="Enable FreeRouting -fo pre-route fanout.",
    )
    route.add_argument(
        "--threads",
        type=int,
        default=None,
        metavar="N",
        help="FreeRouting -mt threads for post-route optimization.",
    )
    route.add_argument(
        "--optimization-threshold",
        type=float,
        default=None,
        metavar="RATIO",
        help="FreeRouting -oit optimization improvement threshold.",
    )
    route.add_argument(
        "--board-update-strategy",
        choices=["greedy", "global", "hybrid"],
        default=None,
        help="FreeRouting -us board update strategy.",
    )
    route.add_argument(
        "--hybrid-ratio",
        type=float,
        default=None,
        metavar="RATIO",
        help=(
            "FreeRouting -hr hybrid ratio as a float "
            "(requires --board-update-strategy hybrid)."
        ),
    )
    route.add_argument(
        "--item-selection-strategy",
        choices=["sequential", "random", "prioritized"],
        default=None,
        help="FreeRouting -is item selection strategy.",
    )
    route.add_argument(
        "--ignore-net-class",
        action="append",
        default=[],
        dest="ignore_net_classes",
        metavar="CLASS",
        help=(
            "FreeRouting -inc: exclude a net class from autorouting. "
            "Repeatable. Does not select individual nets."
        ),
    )
    route.add_argument(
        "--rules-file",
        default=None,
        help=(
            "FreeRouting -dr design rules file. Protected physical "
            "constraint; do not set without ask_user_question."
        ),
    )
    route.add_argument(
        "--save-intermediate",
        action="store_true",
        default=False,
        help="FreeRouting -im: save intermediate routing checkpoints.",
    )
    route.add_argument(
        "--language",
        default=None,
        help="FreeRouting -l language code.",
    )
    route.add_argument(
        "--dialog-timeout",
        type=int,
        default=None,
        metavar="SEC",
        help="FreeRouting -dct dialog timeout in seconds.",
    )
    route.add_argument(
        "--disable-analytics",
        action="store_true",
        default=False,
        help="FreeRouting -da: disable analytics.",
    )
    route.add_argument(
        "--disable-logging",
        action="store_true",
        default=False,
        help="FreeRouting -dl: disable logging.",
    )
    route.add_argument(
        "--log-level",
        choices=[
            "ALL",
            "CONFIG",
            "FINE",
            "FINER",
            "FINEST",
            "INFO",
            "OFF",
            "SEVERE",
            "WARNING",
        ],
        default=None,
        help="FreeRouting -ll log level.",
    )
    route.add_argument(
        "--trace",
        action="store_true",
        default=False,
        help="FreeRouting -trace: enable debug trace verbosity.",
    )
    route.add_argument(
        "--experimental",
        action="store_true",
        default=False,
        help="FreeRouting -test: enable experimental mode.",
    )
    route.add_argument(
        "--extra-freerouting-arg",
        action="append",
        default=[],
        dest="extra_freerouting_args",
        metavar="ARG",
        help=(
            "Passthrough token appended after the headless/-de/-do "
            "skeleton. Repeatable. -dr/--rules-file extras are dropped."
        ),
    )
    route.add_argument(
        "--run-drc",
        action="store_true",
        default=False,
        help=(
            "After SES import, run kicad-cli pcb drc and include drc_summary "
            "with unconnected_items in the JSON result."
        ),
    )
    route.add_argument(
        "--refill-zones",
        action="store_true",
        default=False,
        help=(
            "After SES import, run kicad-cli pcb drc --refill-zones "
            "--save-board before optional post-route DRC."
        ),
    )
    route.add_argument(
        "--kicad-cli-path",
        default=None,
        help=("Optional explicit kicad-cli path for --run-drc and " "--refill-zones."),
    )
    route.add_argument(
        "--kicad-cli-timeout-sec",
        type=int,
        default=120,
        help="Timeout for optional kicad-cli post-route actions.",
    )

    diagnose = subparsers.add_parser(
        "diagnose",
        help="Check Java and pcbnew availability without modifying the board.",
    )
    diagnose.add_argument(
        "--platform",
        choices=["win", "mac", "linux"],
        required=True,
        help="Host platform for pcbnew path probing.",
    )
    diagnose.add_argument(
        "--java-bin",
        default=os.environ.get("COPPERPILOT_JAVA", "java"),
        help="Java executable to probe.",
    )
    diagnose.add_argument(
        "--script-path",
        default=None,
        help=(
            "Path to this skill's main.py for recommended command output. "
            "Defaults to the invoked script path."
        ),
    )
    diagnose.add_argument(
        "--project-dir",
        default=".",
        help="Project root used when building recommended route command.",
    )
    diagnose.add_argument(
        "--pcb",
        default=None,
        help="Optional PCB path used when building recommended route command.",
    )
    return parser


def _resolve_route_paths(
    args: argparse.Namespace,
) -> Dict[str, Optional[Path]]:
    project_dir = Path(args.project_dir).resolve()
    return {
        "project_dir": project_dir,
        "pcb_path": resolve_project_path(args.pcb, project_dir),
        "output_pcb_path": resolve_project_path(args.output_pcb, project_dir),
        "dsn_path": resolve_project_path(args.dsn, project_dir),
        "ses_path": resolve_project_path(args.ses, project_dir),
        "jar_path": resolve_project_path(args.jar_path, project_dir),
        "cache_dir": resolve_project_path(args.cache_dir, project_dir),
        "rules_file": resolve_project_path(args.rules_file, project_dir),
    }


def _freerouting_options_from_args(
    args: argparse.Namespace,
    *,
    rules_file: Optional[Path],
) -> FreeRoutingOptions:
    return FreeRoutingOptions(
        headless=args.headless,
        autorouter_passes=args.autorouter_passes,
        post_route_passes=args.post_route_passes,
        fanout=args.fanout,
        threads=args.threads,
        optimization_threshold=args.optimization_threshold,
        board_update_strategy=args.board_update_strategy,
        hybrid_ratio=args.hybrid_ratio,
        item_selection_strategy=args.item_selection_strategy,
        ignore_net_classes=list(args.ignore_net_classes),
        rules_file=rules_file,
        save_intermediate=args.save_intermediate,
        language=args.language,
        dialog_timeout=args.dialog_timeout,
        disable_analytics=args.disable_analytics,
        disable_logging=args.disable_logging,
        log_level=args.log_level,
        trace=args.trace,
        experimental=args.experimental,
        extra_args=list(args.extra_freerouting_args),
    )


def _attach_native_diagnostics(
    payload: Dict[str, Any],
    stdout_capture: io.StringIO,
    stderr_capture: io.StringIO,
) -> None:
    stdout_tail = tail_text(stdout_capture.getvalue())
    stderr_tail = tail_text(stderr_capture.getvalue())
    if stdout_tail:
        payload["native_stdout_tail"] = stdout_tail
    if stderr_tail:
        payload["native_stderr_tail"] = stderr_tail


def _print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.command == "diagnose":
        script_path = args.script_path
        if script_path is None:
            script_path = str(Path(sys.argv[0]).resolve())
        with capture_native_streams() as (stdout_capture, stderr_capture):
            payload = diagnose_environment(
                platform=args.platform,
                java_bin=args.java_bin,
                script_path=script_path,
                pcb_path=args.pcb,
                project_dir=args.project_dir,
            )
        _attach_native_diagnostics(payload, stdout_capture, stderr_capture)
        _print_json(payload)
        return 0 if payload["status"] == "ok" else 2

    if args.command == "route":
        paths = _resolve_route_paths(args)
        pcb_path = paths["pcb_path"]
        project_dir = paths["project_dir"]
        if pcb_path is None or project_dir is None:
            raise ValueError("--pcb and --project-dir are required for route")
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        try:
            with capture_native_streams() as (stdout_capture, stderr_capture):
                result = run_autoroute(
                    platform=args.platform,
                    pcb_path=pcb_path,
                    project_dir=project_dir,
                    output_pcb_path=paths["output_pcb_path"],
                    dsn_path=paths["dsn_path"],
                    ses_path=paths["ses_path"],
                    jar_path=paths["jar_path"],
                    freerouting_version=args.freerouting_version,
                    freerouting_url=args.freerouting_url,
                    java_bin=args.java_bin,
                    timeout_sec=args.timeout_sec,
                    keep_artifacts=args.keep_artifacts,
                    cache_dir=paths["cache_dir"],
                    freerouting_options=_freerouting_options_from_args(
                        args,
                        rules_file=paths["rules_file"],
                    ),
                    run_drc=args.run_drc,
                    refill_zones=args.refill_zones,
                    kicad_cli_path=args.kicad_cli_path,
                    kicad_cli_timeout_sec=args.kicad_cli_timeout_sec,
                )
        except FreeRoutingError as exc:
            summary = dict(exc.summary)
            telemetry = summary.get("freerouting_telemetry") or {}
            error_payload: Dict[str, Any] = {
                "status": "error",
                "error": str(exc),
                "commands": [summary],
                "freerouting_telemetry": telemetry,
                "next_actions": build_next_actions(
                    telemetry,
                    timed_out=bool(summary.get("timed_out")),
                ),
            }
            _attach_native_diagnostics(error_payload, stdout_capture, stderr_capture)
            _print_json(error_payload)
            return 1
        except Exception as exc:  # noqa: BLE001 - CLI boundary
            error_payload = {
                "status": "error",
                "error": str(exc),
                "next_actions": build_next_actions(),
            }
            _attach_native_diagnostics(error_payload, stdout_capture, stderr_capture)
            _print_json(error_payload)
            return 1

        payload = result.to_dict()
        _attach_native_diagnostics(payload, stdout_capture, stderr_capture)
        _print_json(payload)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
