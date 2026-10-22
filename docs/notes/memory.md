# Memory — decisions and how to test

## Decisions
- 2026-10-22 (Marios): a separate repo for the Part Design tools, name `freecad-addons`. Knurling & Wrap moved
  here from `polar-cnc-converter` 2.25.0 (where it lived since 2026-10-20 as `cad/`; before that in WikiTips).
  Folder `KnurlWrap/` (FreeCAD adds it to `sys.path` and runs its `InitGui.py`). Version restarts at 1.0.0.
- Hole on any surface: only a plain round hole for now (Marios 2026-10-22); details in `knurlwrap.md`.

## How to test
- `FREECAD=<path>/bin/freecad sh tests/run.sh` (xvfb-run). In the Claude container a FreeCAD 26.3 build was at
  `/tmp/claude-0/fcbin/env/bin/freecad` (GitHub release downloads are blocked there).
- `freecad --version` aborts without a display: run.sh then falls back to the `v26-3` user folder.
- Lint: `ruff check --isolated --select E,F,W --line-length 120` (knurl.py has a few old long lines / `l` names).
