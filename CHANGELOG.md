# Changelog

## 1.1.1 — 2026-10-22: Hole, height from the middle, steady + / −

Marios: "pressing + / − for the height sometimes keeps moving; I can't centre it on Z: it must start exactly
at the middle of the part and let me move it by millimetres".
- The panel waits until you stop changing a value (0.4 s) before it recomputes. While FreeCAD recomputed it did
  not see the mouse let go of + / −, so the box kept counting on its own.
- New holes: height 0 = the middle of the part along the axis (was the axis' Z 0). The panel shows the part's
  height span, a step for + / − (0.1 / 0.5 / 1 / 5 mm) and a **Στη μέση** button. Typing a number updates once.
- Holes made with 1.1.0 keep their place (their saved centre).
- The same pause before recomputing in the Wrap panel (its depth + / −).

## 1.1.0 — 2026-10-22: Hole on any surface, exact position

Marios: "I can't say where the hole goes, nor make it point at the centre: it needs parameters or a sketch".
- **Γωνία και ύψος:** an axis (Z, X or Y; the centre is found from the part's own cylinder), an angle round it, a
  height along it; the hole points at the axis (default) or is square to the surface it meets; several holes
  round, evenly spread or at a given angle step. A clicked hole keeps its place when switched to this.
- **Σκαρίφημα:** select a sketch with circles and press the button: every circle is a hole of its own diameter,
  square to the sketch, coming from the sketch's side (or the other side, *Ανάποδα*); editing the sketch moves
  the holes.
- Files made with 1.0.x open unchanged (their holes stay "Κλικ").
- `README.md` here, the Greek panel and the tooltip explain the three ways.

## 1.0.1 — 2026-10-22

- The repository is now `Marioskiv/Knurling-Wrap` (was `freecad-addons`); addon name `Knurling-Wrap`. No code change.
  In the Addon Manager, change the custom repository address to `https://github.com/Marioskiv/Knurling-Wrap`.

## 1.0.0 — 2026-10-22

- Knurling & Wrap (Knurl, Wrap on a cylinder, Hole on any surface) moved here from `polar-cnc-converter` 2.25.0,
  unchanged apart from the folder (`cad/` → `KnurlWrap/`) and the repository address. Files made with them open
  as before (same Python module names). Tests: `tests/run.sh`.
