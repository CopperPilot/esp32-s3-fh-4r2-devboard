#!/usr/bin/env python3
#
# Copyright (c) 2026 AdityaNG
# All rights reserved.
#
"""CopperPilot skill: drive cart.jlcpcb.com + jlcdfm.com like a human user.

Run `python .copperpilot/skills/jlcpcb-order/main.py --help`.
Every command prints one JSON object.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from runtime_bootstrap import ensure_runtime  # noqa: E402

ensure_runtime(Path(__file__).resolve())

import fab_browser as fb  # noqa: E402
import jlc_actions as la  # noqa: E402

# Offline/meta commands run inline; every browser command goes through the job budget.
INLINE_COMMANDS = ("result", "preflight", "browser-start")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="jlcpcb-order",
        description="Drive JLCPCB (quote, DFM, PCBA BOM/CPL, placement, cart) through a real Chrome.",
    )
    ap.add_argument(
        "--project-dir",
        default=".",
        help="Project root for artifacts (.copperpilot/fab/jlcpcb)",
    )
    ap.add_argument(
        "--port", type=int, default=fb.DEFAULT_CDP_PORT, help="Chrome CDP port"
    )
    ap.add_argument(
        "--budget-sec",
        type=float,
        default=fb.DEFAULT_BUDGET_SEC,
        help="Long commands return status=in_progress + job id after this many seconds (CopperPilot backgrounds shell commands after ~25s). 0 = always wait.",
    )
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser(
        "result",
        help="Collect the final JSON of a long command that returned status=in_progress",
    )
    p.add_argument(
        "--job", help="Job id from the in_progress result (default: latest)"
    )
    p.add_argument("--wait-sec", type=float, default=20)
    fb.add_generic_subcommands(sub)
    la.add_subcommands(sub)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    project_dir = Path(args.project_dir).expanduser().resolve()
    fb.resolve_path_args(args, project_dir)
    if args.command == "result":
        fb.emit(fb.wait_job(project_dir, la.SITE, args.job, args.wait_sec))
        return 0
    if args.command not in INLINE_COMMANDS:
        code = fb.run_in_budget(
            la.SITE,
            args.command,
            project_dir,
            Path(__file__).resolve(),
            sys.argv[1:],
            args.budget_sec,
        )
        if code is not None:
            return code

    def body(res: fb.Result) -> None:
        if args.command == "browser-start":
            urls = args.url or [la.HOME_URL]
            res.data.update(fb.launch_chrome(args.port, urls=urls))
            return
        if la.handle_offline(args, res, project_dir):
            return
        with fb.session(args.port) as sess:
            if fb.handle_generic(
                args, res, sess, la.URL_MATCH, la.HOME_URL, project_dir
            ):
                return
            if la.handle(args, res, sess, project_dir):
                return
            raise fb.FabError(f"Unknown command {args.command}")

    return fb.run_command(la.SITE, args.command, body, project_dir)


if __name__ == "__main__":
    sys.exit(main())
