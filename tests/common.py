# Knurling-Wrap — shared pieces of the FreeCAD tests (tests/run.sh runs each test file in its own
# FreeCAD start).
#
# Copyright (c) 2026 Marioskiv
# https://github.com/Marioskiv/Knurling-Wrap
# SPDX-License-Identifier: MIT

import os
import time

from PySide import QtGui

OUT = os.environ["PC_OUT"]
REPO = os.environ["PC_REPO"]
os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, "log.txt"), "w", encoding="utf-8")
fails = []


def check(cond, what):
    log.write("%s %s\n" % ("ok  " if cond else "FAIL", what))
    log.flush()
    if not cond:
        fails.append(what)


def finish():
    with open(os.path.join(OUT, "result.txt"), "w", encoding="utf-8") as f:
        f.write("RESULT: %s\n" % ("PASS" if not fails else "FAIL " + "; ".join(fails)))
    log.close()
    os._exit(0)


def pump(ms=50):
    end = time.monotonic() + ms / 1000.0
    while time.monotonic() < end:
        QtGui.QApplication.processEvents()
