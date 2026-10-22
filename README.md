# freecad-addons

Εργαλεία για το FreeCAD (1.1 και νεότερο) από τον Marioskiv. Ένα πρόσθετο στο Addon Manager, MIT.
*Tools for FreeCAD 1.1+ by Marioskiv: one addon in the Addon Manager, MIT licence.*

## Knurling & Wrap (Part Design)

Δική του εργαλειοθήκη, μόνο στο **Part Design**. Οδηγίες: [`KnurlWrap/README.md`](KnurlWrap/README.md).

- **Knurl (ραβδώσεις):** knurling σε κύλινδρο με ένα κλικ (διαμάντι ή ίσιο, πραγματικά δόντια ή μόνο γραμμές).
- **Σκαρίφημα σε κύλινδρο (Wrap):** κλικ στον κύλινδρο, σχεδίασε στο σκαρίφημα που ανοίγει· γράμματα και
  σχήματα τυλίγονται γύρω του: χάραξη, ανάγλυφο ή κόψιμο μέχρι τον άξονα.
- **Τρύπα σε επιφάνεια:** κλικ στο κομμάτι εκεί που θέλεις την τρύπα (επίπεδη, κύλινδρος, δόντια τροχαλίας,
  οποιαδήποτε καμπύλη) και πάτα το κουμπί: τρύπα κάθετα στην επιφάνεια, ως το πρώτο κενό, σε βάθος ή διαμπερής.

## Εγκατάσταση / Install

FreeCAD → **Tools → Addon Manager** → ⚙ (ρυθμίσεις) → **Custom repositories** → πρόσθεσε
`https://github.com/Marioskiv/freecad-addons`, branch `main` → OK. Βρες το **freecad-addons** στη λίστα →
**Install**, και ξεκίνα ξανά το FreeCAD.

Αυτά τα εργαλεία ήταν πριν μέσα στο Polar CNC (`polar-cnc-converter`, ως την έκδοση 2.25.0) και ακόμα πιο πριν
στο WikiTips. Τα παλιά αρχεία ανοίγουν κανονικά.

## Tests

`FREECAD=/path/to/bin/freecad sh tests/run.sh` (needs `xvfb-run`): every test must say `RESULT: PASS`.
