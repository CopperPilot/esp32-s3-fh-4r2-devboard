---
required_inputs: [platform, pcb_path, optional project_dir and artifact overrides]
artifact_outputs: [structured JSON route result with DSN/SES/JAR paths and segment counts]
---

# Skill: kicad_autorouter

## Objective
Run the external FreeRouting workflow on the user's machine:
export Specctra DSN with KiCad `pcbnew`, run `java -jar freerouting.jar`,
import the resulting SES back into the PCB, and report structured results.

**Headless by default:** route runs with `-Djava.awt.headless=true` and
`--gui.enabled=false` so FreeRouting does not launch a GUI. Use
`--no-headless` only when explicitly debugging locally with the
FreeRouting GUI.

## Platform defaults (mac)
- FreeRouting version: `2.2.4`
- FreeRouting URL: `https://github.com/freerouting/freerouting/releases/download/v2.2.4/freerouting-2.2.4.jar`
- Skill cache dir: `.copperpilot/skills/kicad_autorouter/cache`
- pcbnew site paths: `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.11/site-packages, /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages`
- Java binary: `java`

## Prerequisites
- KiCad installed with the `pcbnew` Python module available.
- Java 25+ reachable as `java`. CopperPilot onboarding installs this
  runtime; do not download another JDK when `java -version` is already 25+.
- Do **not** `pip install pcbnew`; use KiCad's bundled Python when needed.
- KiCad 10 removed `kicad-cli pcb export specctradsn`. This skill exports DSN
  with `pcbnew.ExportSpecctraDSN` and imports SES with
  `pcbnew.ImportSpecctraSES`.
- If JAR download fails (common when KiCad bundled Python has SSL issues),
  the skill automatically retries with system `curl`/`wget`, or you can
  pre-cache the JAR manually and pass `--jar-path` to a local copy.

## Path resolution
Relative paths such as `--pcb board.kicad_pcb` resolve against `--project-dir`,
not the shell current working directory. Absolute paths are preserved as-is.

## Clean JSON output
The CLI captures native `pcbnew`/wxWidgets debug output and prints only JSON to
stdout. Inspect `native_stdout_tail` / `native_stderr_tail` in the result when
diagnosing local environment noise.

## Post-route convenience flags
Optional local follow-up actions (disabled by default):
- `--run-drc`: run `kicad-cli pcb drc` after SES import and include
  `drc_summary.violations` and `drc_summary.unconnected_items` in the
  JSON result. These lists are distinct: empty `unconnected_items` is
  connectivity only, not DRC-clean.
- `--refill-zones`: run `kicad-cli pcb drc --refill-zones --save-board` after
  SES import.
- `--kicad-cli-path`: override auto-discovery when needed.

## FreeRouting tuning flags
Allowed engine knobs (iterate freely from `freerouting_telemetry` /
`next_actions`; do not wait for DRC to learn `final_unrouted`):
- `--headless` / `--no-headless` (default: headless; GUI debug only)
- `--timeout-sec` — Java **subprocess** wall clock (default 600), not `-t`
- `--autorouter-passes N` (`-ap`), `--post-route-passes N` (`-pp`)
- `--fanout` (`-fo`), `--threads N` (`-mt`)
- `--optimization-threshold RATIO` (`-oit`)
- `--board-update-strategy greedy|global|hybrid` (`-us`)
- `--hybrid-ratio RATIO` (`-hr`, float as implemented)
- `--item-selection-strategy sequential|random|prioritized` (`-is`)
- `--ignore-net-class CLASS` (`-inc`, repeatable)
- `--save-intermediate` (`-im`)
- `--log-level LEVEL` (`-ll`), `--trace`, `--experimental` (`-test`)
- `--disable-analytics` (`-da`), `--disable-logging` (`-dl`)
- `--dialog-timeout SEC` (`-dct`)
- `--extra-freerouting-arg` after the headless/`-de`/`-do` skeleton
  (`-dr` / `--rules-file` extras are dropped)

Protected physical constraints (exhausted engine retries + RCA + DFM
numbers + one `ask_user_question` yes; never silent):
- `--rules-file PATH` (`-dr`)
- KiCad rules (`set_design_settings`, `set_kicad_project_design_rules`,
  `.kicad_dru`), Edge.Cuts, stackup, via/track-as-router

Inspect `commands[0].command`, `commands[0].freerouting_options`, and
`freerouting_telemetry` in the JSON output.

## Telemetry vs Java exit 0
INFO stdout is enough; `-ll ALL` / `freerouting.log` is optional deeper
debug (ok_point, named incompletes). Read the log if present; do not
block the route on it.

`freerouting_telemetry` fields:
- `started_unrouted`, `pass_history` (pass, time_sec, score, unrouted)
- omitted `(N unrouted)` on a pass means that pass has 0 unrouted
- `total_passes`, `final_score`, `cpu_seconds`, `peak_heap_mb`
- `final_unrouted`, `board_unchanged`

Java exit 0 and `status: routed` mean SES imported (or the process
finished), **not** 100% connected. `segment_count_*` is not connectivity.
Always inspect telemetry, then `run_drc` and `list_nets`.

## When to tune passes
Start with the default route command. Use telemetry, then DRC. Order:
strategy (`-us`/`-is`/`-hr`) → `--fanout`/`--threads` →
`--autorouter-passes`/`--timeout-sec`/`--post-route-passes`.
Pass starvation (score rising, still unrouted): more passes/timeout.
Oscillation: `--item-selection-strategy random`.
Dense SMD plateau: `--board-update-strategy hybrid` + `--hybrid-ratio`,
`--fanout`. Connected but ugly: `--post-route-passes`.
Score ~0 / board unchanged: **stop mutating**; RCA; ask. Do not enlarge
Edge.Cuts or relax clearance from telemetry alone.

## Skill install
If `SKILL.md` is stale (missing telemetry / protected-lever policy),
re-run `install_kicad_autorouter(..., force=true)`.

## Invariants
Headless by default. JAR auto-download/cache (urllib → curl → wget).
`--timeout-sec` bounds the Java subprocess; do not leave GUI or unbounded
Java running.

## Net-level control limits
FreeRouting CLI **cannot** route only arbitrary individual nets or pads.
The strongest CLI control is `--ignore-net-class` (`-inc`), which **excludes**
net classes from autorouting — not a per-net selector.
Never invent track geometry. Never use `write`/`edit`/`bash` to inject
`(segment …)` or `(via …)` copper. On hard FreeRouting failure (nonzero
Java exit, missing/empty SES, timeout with no import), do not fall back
to manual geometry — stop and report infeasible with an RCA.
For leftover unconnected nets after bulk autoroute:
1. Inspect `freerouting_telemetry` and `next_actions`. Run `run_drc`.
   Inspect both `violations`/`errors` and `unconnected_items`
   (connectivity only). If the pass created **new DRC errors** vs the
   pre-route baseline, revert (`unroute_pcb_net` / restore prior board),
   stop, and report.
2. Retune **allowed** engine flags using telemetry (strategy →
   fanout/threads → passes/timeout/post-route) and/or `--ignore-net-class`.
   `unroute_pcb_net` then autoroute messy partials. Count route attempts
   toward the 3-attempt retry budget.
3. If still infeasible after exhausted engine retries: stop mutating.
   RCA plus DFM-backed numbers, then one `ask_user_question` before any
   KiCad rule, `--rules-file`, Edge.Cuts, stackup, or via/track-as-router
   change. Never change constraints silently. Skip if the user already
   forbade rule changes or fab capability is unknown.
4. After the retry budget or a hard failure: **stop and report
   infeasible** with an RCA and next steps. Do not invent tracks.
   Do not silently enlarge the board.

## Steps
1. Install this skill once with `install_kicad_autorouter`.
2. Run `.copperpilot/skills/kicad_autorouter/main.py diagnose --platform mac` to verify Java and
   pcbnew.
3. If diagnose returns `recommended_route_command`, run that exact
   command on the user's machine (common on macOS when system Python
   cannot import pcbnew).
4. Otherwise run `.copperpilot/skills/kicad_autorouter/main.py route --platform mac
   --project-dir .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate --pcb .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate/ESP32S3FH4R2.kicad_pcb`.
5. Read the JSON for `freerouting_telemetry`, `next_actions`,
   `segment_count_before`, `segment_count_after`, `commands[0].command`,
   and artifact paths. Segment counts are not connectivity or DRC-clean.
   Java 0 / `status: routed` is not 100% connected.
6. Run `run_drc` and inspect both `violations` and `unconnected_items`.
7. Refill zones separately with `fill_pcb_zones` or
   `kicad-cli pcb drc --refill-zones`.
8. For remaining unconnected nets, follow Net-level control limits
   (allowed engine retune, then stop + RCA + DFM + ask before
   protected constraints).

## Examples
- `python .copperpilot/skills/kicad_autorouter/main.py diagnose --platform mac --java-bin java`
- `python .copperpilot/skills/kicad_autorouter/main.py route --platform mac --project-dir .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate --pcb .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate/ESP32S3FH4R2.kicad_pcb`
- `python .copperpilot/skills/kicad_autorouter/main.py route --platform mac --project-dir .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate --pcb .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate/ESP32S3FH4R2.kicad_pcb --autorouter-passes 5 --post-route-passes 3 --fanout --threads 6 --timeout-sec 900`
- `python .copperpilot/skills/kicad_autorouter/main.py route --platform mac --project-dir .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate --pcb .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate/ESP32S3FH4R2.kicad_pcb --keep-artifacts --log-level INFO --trace`
- `python .copperpilot/skills/kicad_autorouter/main.py route --platform mac --project-dir .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate --pcb .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate/ESP32S3FH4R2.kicad_pcb --ignore-net-class Power --ignore-net-class Default`
- `python .copperpilot/skills/kicad_autorouter/main.py route --platform mac --project-dir .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate --pcb .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate/ESP32S3FH4R2.kicad_pcb --run-drc --refill-zones`
- `python .copperpilot/skills/kicad_autorouter/main.py route --platform mac --project-dir .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate --pcb .copperpilot/tmp/staging/unit-6-pcb-routing-planes-and-drc/candidate/ESP32S3FH4R2.kicad_pcb --freerouting-version 2.2.4 --jar-path .copperpilot/skills/kicad_autorouter/cache/freerouting-2.2.4.jar`
