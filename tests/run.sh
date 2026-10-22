#!/bin/sh
# freecad-addons — run every test in a real FreeCAD (needs FreeCAD 1.1+ and xvfb-run).
#
#   FREECAD=/path/to/bin/freecad sh tests/run.sh
#
# Uses a throw-away FreeCAD user folder with this repository installed as an addon; each test runs
# in its own FreeCAD start. Every test must say RESULT: PASS.
#
# Copyright (c) 2026 Marioskiv
# https://github.com/Marioskiv/freecad-addons
# SPDX-License-Identifier: MIT
set -u
FREECAD=${FREECAD:-freecad}
REPO=$(cd "$(dirname "$0")/.." && pwd)
OUT=${OUT:-/tmp/freecad-addons-test}
rm -rf "$OUT"
mkdir -p "$OUT/home"
VER=$("$FREECAD" --version 2>/dev/null | sed -n 's/.* \([0-9][0-9]*\)\.\([0-9][0-9]*\).*/v\1-\2/p' | head -1)
MOD="$OUT/home/.local/share/FreeCAD/${VER:-v26-3}/Mod"
mkdir -p "$MOD"
ln -s "$REPO" "$MOD/freecad-addons"

result="RESULT: PASS"
# Knurling & Wrap: Knurl, Wrap on a cylinder, Hole on any surface, and a file made while Knurl and
# Wrap were part of WikiTips (opened with no WikiTips installed)
for t in knurl cyl_wrap surface_hole knurlwrap_old_file; do
    HOME="$OUT/home" PC_OUT="$OUT/$t" PC_REPO="$REPO" xvfb-run -a -s "-screen 0 1600x1000x24" \
        "$FREECAD" "$REPO/tests/${t}_test.py" > "$OUT/freecad-$t.log" 2>&1
    r=$(grep -h "^RESULT" "$OUT/$t/result.txt" 2>/dev/null || echo "RESULT: no result (see $OUT/freecad-$t.log)")
    grep -h "^FAIL" "$OUT/$t/result.txt" "$OUT/$t/log.txt" 2>/dev/null
    echo "$t: $r"
    [ "$r" = "RESULT: PASS" ] || result="$result; $t $r"
done
echo "$result"
[ "$result" = "RESULT: PASS" ]
