# CLAUDE.md — read this first

Owner: Marios (GitHub: Marioskiv). He writes in Greeklish; **always answer in proper Greek script**, simple,
honest and direct. Never claim something you have not checked.
**No change without asking him first** (code, tests, settings, versions): propose, wait for a clear "ναι".

## Before doing anything
1. Read `docs/notes/memory.md` (decisions, how to test) and `docs/notes/pending.md` (open items).
2. For Knurling & Wrap read `docs/notes/knurlwrap.md`.

## What this repo is (Marios, 2026-10-22; repo `Knurling-Wrap`, was `freecad-addons`)
Part Design / general FreeCAD tools, ONE addon in the Addon Manager (`package.xml`, one `<workbench>` per tool
folder). Today: `KnurlWrap/` (Knurl, Wrap on a cylinder, Hole on any surface). Not here: the Polar CNC CAM addon
and the web converter (`polar-cnc-converter`), WikiTips (`freecad-wikitips`), machine files (`cnc-manuals`,
private). Never mix files or notes between repos.

## Rules
- Work on a branch, merge into `main` only after `sh tests/run.sh` passes in a real FreeCAD.
- No pip dependencies; an addon must never break FreeCAD start-up (InitGui catches everything).
- Saved names are a contract: Python module paths (`knurlwrap.knurl`, `knurlwrap.wrap`, `knurlwrap.hole`,
  `wikitips_knurl`, `wikitips_wrap`), class names, property names and the Greek enumeration values are stored in
  users' documents: never rename them.
- Every source file: `Copyright (c) 2026 Marioskiv`, the repo URL, `SPDX-License-Identifier: MIT`.
- Update `CHANGELOG.md`, the version in `package.xml`, and the notes at the end of every session.
