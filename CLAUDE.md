# CLAUDE.md

Instructions for AI coding assistants working on this repository.

- The owner's working notes, rules and open items are kept privately (repository `Marioskiv/cnc-manuals`,
  folder `knurling-wrap/docs/repo-notes/`). Read them first when you have access; otherwise ask the owner.
- Ask the owner before changing code, tests, settings or versions.
- Work on a branch; merge into `main` only after `sh tests/run.sh` passes in a real FreeCAD.
- No pip dependencies; the addon must never break FreeCAD start-up.
- Saved names are a contract (module paths, class and property names, the Greek enumeration values are stored in
  users' documents): never rename them.
- Every source file carries `Copyright (c) 2026 Marioskiv`, the repository URL and `SPDX-License-Identifier: MIT`.
- Keep notes in the private repository, not here.
