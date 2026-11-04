#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""Make sure Playwright is importable, creating a private runtime if needed.

The skill runs under whatever Python the agent uses (CopperPilot ships a
standalone CPython 3.12). Playwright is installed once into
~/.copperpilot/fab_runtime/venv (override: COPPERPILOT_FAB_RUNTIME) and the
skill re-executes itself there. No browser binaries are downloaded: the skill
drives the user's installed Chrome over CDP.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLAYWRIGHT_SPEC = "playwright==1.64.1"
EXTRA_SPECS = ["openpyxl>=3.1"]
RUNTIME_DIR = Path(
    os.environ.get(
        "COPPERPILOT_FAB_RUNTIME",
        str(Path.home() / ".copperpilot" / "fab_runtime"),
    )
)
_REEXEC_FLAG = "COPPERPILOT_FAB_REEXEC"


def _venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def _have_playwright() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
    except Exception:
        return False
    return True


def ensure_runtime(script: Path) -> None:
    """Return if Playwright imports; otherwise build the runtime and re-exec."""
    if _have_playwright():
        return
    if os.environ.get(_REEXEC_FLAG):
        _fail("Playwright still not importable inside the fab runtime.")
    venv = RUNTIME_DIR / "venv"
    py = _venv_python(venv)
    if not py.exists():
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        _run([sys.executable, "-m", "venv", str(venv)], "create venv")
    check = subprocess.run(
        [str(py), "-c", "import playwright.sync_api"],
        capture_output=True,
    )
    if check.returncode != 0:
        _run(
            [
                str(py),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-q",
                PLAYWRIGHT_SPEC,
                *EXTRA_SPECS,
            ],
            "pip install playwright",
        )
    env = dict(os.environ)
    env[_REEXEC_FLAG] = "1"
    proc = subprocess.run([str(py), str(script), *sys.argv[1:]], env=env)
    sys.exit(proc.returncode)


def _run(cmd: list, what: str) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        _fail(
            f"Runtime bootstrap failed during {what}.",
            stderr=proc.stderr[-2000:],
        )


def _fail(message: str, **extra: object) -> None:
    payload = {
        "ok": False,
        "status": "error",
        "command": "bootstrap",
        "data": {"error": message, "runtime_dir": str(RUNTIME_DIR), **extra},
        "next_actions": [
            "Check network access to PyPI, or pre-install with: "
            f"python -m pip install '{PLAYWRIGHT_SPEC}' openpyxl",
        ],
    }
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    sys.exit(2)
