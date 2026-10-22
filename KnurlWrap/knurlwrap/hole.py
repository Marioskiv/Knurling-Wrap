# Knurling & Wrap — Hole: round holes on any surface (Part Design).
#
# Copyright (c) 2026 Marioskiv
# https://github.com/Marioskiv/Knurling-Wrap
# SPDX-License-Identifier: MIT
"""Hole on any surface (asked by Marios 2026-10-22: "open holes in every solid without effort").

Three ways to say where the hole goes (the "Θέση" of the hole):

- Κλικ: click the part where the hole goes and press the button. The hole is drilled there,
  square to the surface at that point.
- Γωνία και ύψος: for round parts (a pulley, a shaft). An axis (Z, X or Y through a centre), an
  angle around it and a height along it; the hole points at the axis or square to the surface it
  meets. Several holes evenly round (or at a given angle step) for grub screws.
- Σκαρίφημα: every circle of a sketch is a hole of that circle's diameter, square to the sketch.
  The line of each hole comes from outside the part, so a sketch on the XZ plane through the
  middle of a pulley gives radial holes through its teeth.

The drill always comes from outside the part along the hole's line, so whatever lies on that
line before the hole's start is cut too, like a real drill. It stops at the first empty space it
meets (the default: through the wall, e.g. into a pulley's bore), at a depth, or goes right through.

Some features leave a solid that looks fine but makes every later cut fail ("result is empty"):
a Part Design Hole with "Model Thread" ticked was one on Marios's HTD 5M pulley (FreeCAD 26.3).
The command tests the cut first; when the last solid is broken it puts the hole just before the
first feature that breaks it, and says so.
"""

import math
import os

import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # the KnurlWrap folder
ICON = os.path.join(HERE, "Resources", "Hole.svg")
# the values below are SAVED in documents: never rename them
MODES = ["Ως το πρώτο κενό", "Βάθος", "Διαμπερής"]
POSITIONS = ["Κλικ", "Γωνία και ύψος", "Σκαρίφημα"]
AIMS = ["Προς τον άξονα", "Κάθετα στην επιφάνεια"]
AXES = ["Z", "X", "Y"]
V = App.Vector


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------
def point_and_normal(face, point):
    """The point exactly on the face and the face's outward normal there (out of the material)."""
    u, v = face.Surface.parameter(V(point))
    p = face.Surface.value(u, v)
    n = V(face.normalAt(u, v))         # normalAt follows the face's orientation: out of the solid
    return V(p), n.normalize()


def _diag(shape):
    return max(shape.BoundBox.DiagonalLength, 1.0)


def _far(shape, point):
    """A distance along any line through `point` that is surely outside the part."""
    return 2 * _diag(shape) + (point - shape.BoundBox.Center).Length


def pieces(shape, origin, direction, length):
    """The pieces of the line origin + t * direction (0 <= t <= length) inside the material, as
    sorted (t in, t out); touching pieces (split at a seam) are joined."""
    ray = Part.LineSegment(origin, origin + direction * length).toShape()
    out = []
    for e in ray.common(shape).Edges:
        a, b = ((e.Vertexes[0].Point - origin).dot(direction), (e.Vertexes[-1].Point - origin).dot(direction))
        out.append([min(a, b), max(a, b)])
    out.sort()
    joined = []
    for a, b in out:
        if joined and a <= joined[-1][1] + 1e-6:
            joined[-1][1] = max(joined[-1][1], b)
        else:
            joined.append([a, b])
    return joined


def first_exit(shape, point, direction):
    """Distance from `point` along `direction` to where the line first leaves the material
    (None when it never enters it)."""
    segs = pieces(shape, point - direction * 0.01, direction, _far(shape, point) + 0.01)
    return segs[0][1] - 0.01 if segs else None


def line_tool(shape, point, direction, diameter, mode, depth, from_point=True):
    """The cylinder that drills along the line through `point` (going `direction`): it starts
    outside the part and ends at the hole's bottom; None when there is nothing to drill.

    from_point: the hole starts at `point` (a clicked point on the surface); otherwise where the
    line, coming from outside, first enters the material. Depth and "first empty space" count
    from that start."""
    far = _far(shape, point)
    origin = point - direction * far
    if from_point:
        start = far
    else:
        segs = pieces(shape, origin, direction, 2 * far)
        if not segs:
            return None
        start = segs[0][0]
    if mode == "Διαμπερής":
        end = 2 * far
    elif mode == "Βάθος":
        end = start + depth
    else:
        segs = pieces(shape, origin, direction, 2 * far)
        seg = next((s for s in segs if s[1] > start + 1e-6 and s[0] <= start + 0.01), None)
        if seg is None:
            return None
        end = seg[1] + 0.01           # a hair past the far wall: no skin left
    if end <= start:
        return None
    return Part.makeCylinder(diameter / 2.0, end, origin, direction)


def hole_tool(shape, point, direction, diameter, mode, depth):
    """The drill of a clicked hole (kept for the first version's callers)."""
    return line_tool(shape, point, direction, diameter, mode, depth, True)


def cut_ok(shape, tool, result):
    """True when the cut looks right. A broken solid gives a valid-looking result that has lost
    (almost) all of its material, or one that lost more than the drill can take."""
    if result is None or result.isNull() or not result.Solids or not result.isValid():
        return False
    removed = shape.Volume - result.Volume
    return -1e-6 <= removed <= tool.Volume * 1.001 + 1e-6 and result.Volume > 1e-6


def cut_with(shape, tools):
    """(result, why): the solid with the holes, or (None, "miss" / "broken")."""
    if not tools or any(t is None for t in tools):
        return None, "miss"
    tool = tools[0] if len(tools) == 1 else Part.makeCompound(tools)
    try:
        result = shape.cut(tool)
    except Exception:
        return None, "broken"
    if not cut_ok(shape, tool, result):
        return None, "broken"
    if len(result.Solids) == 1:
        result = result.Solids[0]
    return result, ""


def drill(shape, point, direction, diameter, mode, depth):
    """(result, why) of one clicked hole."""
    return cut_with(shape, [hole_tool(shape, point, direction, diameter, mode, depth)])


def inward(shape, point, direction):
    """`direction`, or its opposite when the material is on the other side of the point (the
    normal of a face of a broken solid can point into the material)."""
    e = min(0.05, _diag(shape) * 1e-3)
    if not shape.isInside(point + direction * e, 1e-7, True) and shape.isInside(point - direction * e, 1e-7, True):
        return -direction
    return direction


# --- Γωνία και ύψος ---------------------------------------------------------
def axis_frame(axis):
    """(axis direction, angle 0 direction, angle 90 direction) of "Z", "X" or "Y". Angles turn
    counter-clockwise looking from the axis' tip: Z from +X to +Y, X from +Y to +Z, Y from +Z to +X."""
    a, u = {"Z": (V(0, 0, 1), V(1, 0, 0)), "X": (V(1, 0, 0), V(0, 1, 0)), "Y": (V(0, 1, 0), V(0, 0, 1))}[axis]
    return a, u, a.cross(u)


def axis_centre(shape, axis):
    """A point of the part's own axis, at the middle of the part along it (height 0 = the middle):
    the axis of its biggest cylindrical face along `axis` (a pulley's hub, a shaft), else the middle
    of its bounding box across the axis."""
    a = axis_frame(axis)[0]
    best = None
    for f in shape.Faces:
        s = f.Surface
        if isinstance(s, Part.Cylinder) and abs(abs(V(s.Axis).normalize().dot(a)) - 1) < 1e-9:
            if best is None or s.Radius > best[0]:
                best = (s.Radius, V(s.Center))
    c = best[1] if best is not None else V(shape.BoundBox.Center)
    return c - a * c.dot(a) + a * V(shape.BoundBox.Center).dot(a)


def extent(shape, centre, axis):
    """(lowest, highest) height of the part along the axis, measured from `centre`."""
    a = axis_frame(axis)[0]
    bb = shape.BoundBox
    hs = [(V(x, y, z) - centre).dot(a) for x in (bb.XMin, bb.XMax) for y in (bb.YMin, bb.YMax)
          for z in (bb.ZMin, bb.ZMax)]
    return min(hs), max(hs)


def angle_height(point, centre, axis):
    """(angle in degrees, height) of a point about an axis through `centre`."""
    a, u, v = axis_frame(axis)
    r = point - centre
    return math.degrees(math.atan2(r.dot(v), r.dot(u))), r.dot(a)


def angles(angle, count, step):
    count = max(1, int(count))
    step = step if abs(step) > 1e-9 else 360.0 / count
    return [angle + i * step for i in range(count)]


def nearest_face_normal(shape, point):
    """Outward normal of the face of `shape` nearest to `point` (None if none)."""
    best = None
    vx = Part.Vertex(point)
    for f in shape.Faces:
        try:
            d = f.distToShape(vx)[0]
        except Exception:
            continue
        if best is None or d < best[0]:
            best = (d, f)
    if best is None:
        return None
    return point_and_normal(best[1], point)[1]


def radial_tools(shape, centre, axis, angle, height, count, step, aim, diameter, mode, depth):
    a, u, v = axis_frame(axis)
    on_axis = centre + a * height
    tools = []
    for ang in angles(angle, count, step):
        r = u * math.cos(math.radians(ang)) + v * math.sin(math.radians(ang))
        d = -r
        if aim == "Κάθετα στην επιφάνεια":
            far = _far(shape, on_axis)
            segs = pieces(shape, on_axis + r * far, d, 2 * far)
            if not segs:
                tools.append(None)
                continue
            p = on_axis + r * far + d * segs[0][0]
            n = nearest_face_normal(shape, p)
            if n is None:
                tools.append(None)
                continue
            tools.append(line_tool(shape, p, inward(shape, p, -n), diameter, mode, depth, True))
        else:
            tools.append(line_tool(shape, on_axis, d, diameter, mode, depth, False))
    return tools


# --- Σκαρίφημα --------------------------------------------------------------
def sketch_circles(sketch):
    """(centre, diameter) of every whole circle of a sketch (construction lines are not in it)."""
    out = []
    for e in sketch.Shape.Edges:
        if isinstance(e.Curve, Part.Circle) and e.isClosed():
            out.append((V(e.Curve.Center), 2 * e.Curve.Radius))
    return out


def sketch_direction(sketch, reversed_=False):
    """Into the part from the sketch's front side (like a Pocket), or the other way."""
    n = sketch.getGlobalPlacement().Rotation.multVec(V(0, 0, 1)) if hasattr(sketch, "getGlobalPlacement") \
        else sketch.Placement.Rotation.multVec(V(0, 0, 1))
    return n if reversed_ else -n


def sketch_tools(shape, sketch, reversed_, mode, depth):
    d = sketch_direction(sketch, reversed_)
    return [line_tool(shape, c, d, dia, mode, depth, False) for c, dia in sketch_circles(sketch)]


# --- the feature ------------------------------------------------------------
def _base_shape(obj):
    base = getattr(obj, "BaseFeature", None) or getattr(obj, "Base", None)
    return base.Shape if base is not None and not base.Shape.isNull() else None


def tools_for(obj, shape):
    """The drills of a HoleOnSurface for a given solid."""
    pos = getattr(obj, "Position", POSITIONS[0])
    if pos == "Σκαρίφημα":
        if obj.Sketch is None:
            return []
        return sketch_tools(shape, obj.Sketch, obj.Reversed, obj.Mode, obj.Depth.Value)
    if pos == "Γωνία και ύψος":
        return radial_tools(shape, V(obj.AxisCentre), obj.Axis, obj.Angle.Value, obj.Height.Value,
                            obj.Count, obj.AngleStep.Value, obj.Aim, obj.Diameter.Value, obj.Mode, obj.Depth.Value)
    direction = V(obj.Direction)
    if direction.Length < 1e-9:
        return []
    return [hole_tool(shape, V(obj.Point), direction.normalize(), obj.Diameter.Value, obj.Mode, obj.Depth.Value)]


def chain(feature):
    """The features under `feature` in its Body, last first (feature itself included)."""
    out = []
    while feature is not None and feature not in out:
        out.append(feature)
        feature = getattr(feature, "BaseFeature", None)
    return out


def healthy_place(tip, obj):
    """(feature to put the hole after, the feature that breaks the solid or None).

    Walks back from the Tip until the holes cut right. A clicked hole's direction is checked
    against each solid (the normal of a face of a broken solid can point into the material)."""
    breaker = None
    first = V(obj.Direction)
    for f in chain(tip):
        if f.Shape.isNull() or not f.Shape.Solids:
            break
        if getattr(obj, "Position", POSITIONS[0]) == "Κλικ":
            obj.Direction = inward(f.Shape, V(obj.Point), first)
        res, _why = cut_with(f.Shape, tools_for(obj, f.Shape))
        if res is not None:
            return f, breaker
        breaker = f
    obj.Direction = first
    return None, breaker


BROKEN = ("Η τρύπα δεν βγαίνει",
          "Το στερεό πριν από την τρύπα είναι χαλασμένο: κάθε κόψιμο σε αυτό αποτυγχάνει.",
          ["Αν πριν από την τρύπα υπάρχει Hole με σπείρωμα, άνοιξέ το και βγάλε το τικ από το "
           "«Model Thread».",
           "Ή σύρε την τρύπα (HoleOnSurface) στο δέντρο πιο πάνω, πριν από το χαλασμένο βήμα."])
MISS = ("Η τρύπα δεν βγαίνει",
        "Στη θέση αυτή, στη γραμμή της τρύπας, δεν υπάρχει υλικό να τρυπηθεί.",
        ["Άνοιξε την τρύπα (διπλό κλικ) και άλλαξε τη θέση (γωνία, ύψος) ή διάλεξε «Διαμπερής».",
         "Με σκαρίφημα: δες ότι οι κύκλοι είναι πάνω από το κομμάτι, ή τίκαρε «Ανάποδα»."])
NO_CIRCLES = ("Η τρύπα δεν βγαίνει",
              "Το σκαρίφημα δεν έχει κύκλους.",
              ["Άνοιξε το σκαρίφημα και σχεδίασε έναν κύκλο για κάθε τρύπα (η διάμετρος του κύκλου "
               "είναι η διάμετρος της τρύπας).",
               "Οι γραμμές κατασκευής (μπλε) δεν μετράνε."])


def _add(obj, kind, name, group, tip, value=None):
    if name not in obj.PropertiesList:
        obj.addProperty(kind, name, group, tip)
        if value is not None:
            setattr(obj, name, value)


def add_properties(obj):
    """All the properties; the ones a file from an older version lacks are added with values that
    keep that hole as it was."""
    _add(obj, "App::PropertyLength", "Diameter", "Hole", "Διάμετρος της τρύπας", 3.0)
    _add(obj, "App::PropertyEnumeration", "Mode", "Hole",
         "Ως το πρώτο κενό: περνά τον τοίχο και σταματά. Βάθος: όσο λες. Διαμπερής: από άκρη σε άκρη.", MODES)
    _add(obj, "App::PropertyLength", "Depth", "Hole", "Βάθος από την επιφάνεια (μόνο για «Βάθος»)", 5.0)
    _add(obj, "App::PropertyEnumeration", "Position", "Hole",
         "Κλικ: εκεί που έκανες κλικ. Γωνία και ύψος: γύρω από έναν άξονα. Σκαρίφημα: οι κύκλοι του.", POSITIONS)
    _add(obj, "App::PropertyVector", "Point", "Position", "Κλικ: το σημείο της επιφάνειας όπου ανοίγει η τρύπα")
    _add(obj, "App::PropertyVector", "Direction", "Position", "Κλικ: η κατεύθυνση της τρύπας (προς τα μέσα)")
    _add(obj, "App::PropertyEnumeration", "Axis", "Angle and height", "Ο άξονας του στρογγυλού κομματιού", AXES)
    _add(obj, "App::PropertyVector", "AxisCentre", "Angle and height", "Ένα σημείο του άξονα (το κέντρο)")
    _add(obj, "App::PropertyAngle", "Angle", "Angle and height",
         "Γωνία γύρω από τον άξονα (Z: 0 = +X, 90 = +Y)", 0.0)
    _add(obj, "App::PropertyDistance", "Height", "Angle and height",
         "Ύψος κατά μήκος του άξονα, από το AxisCentre (για νέες τρύπες: 0 = η μέση του κομματιού)", 0.0)
    _add(obj, "App::PropertyEnumeration", "Aim", "Angle and height",
         "Η τρύπα δείχνει στον άξονα (κέντρο) ή είναι κάθετη στην επιφάνεια που συναντά", AIMS)
    _add(obj, "App::PropertyInteger", "Count", "Angle and height", "Πόσες τρύπες γύρω-γύρω", 1)
    _add(obj, "App::PropertyAngle", "AngleStep", "Angle and height",
         "Γωνία από τρύπα σε τρύπα (0 = ίσα μοιρασμένες γύρω-γύρω)", 0.0)
    _add(obj, "App::PropertyLink", "Sketch", "Sketch", "Σκαρίφημα: κάθε κύκλος του είναι μια τρύπα")
    _add(obj, "App::PropertyBool", "Reversed", "Sketch", "Τρύπες από την άλλη πλευρά του σκαριφήματος", False)


class HoleOnSurface:
    def __init__(self, obj):
        obj.Proxy = self
        add_properties(obj)

    def onDocumentRestored(self, obj):
        add_properties(obj)

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def execute(self, obj):
        base = _base_shape(obj)
        if base is None:
            raise RuntimeError("Hole: no base solid")
        if getattr(obj, "Position", "") == "Σκαρίφημα" and (obj.Sketch is None or not sketch_circles(obj.Sketch)):
            from .knurl import explain
            explain(*NO_CIRCLES)
            raise RuntimeError("Hole: the sketch has no circles")
        result, why = cut_with(base, tools_for(obj, base))
        if result is None:
            from .knurl import explain
            explain(*(MISS if why == "miss" else BROKEN))
            raise RuntimeError("Hole: " + ("nothing to drill here" if why == "miss" else
                                           "the solid before the hole is broken"))
        obj.Shape = result


def _place(owner, obj):
    """Put a new hole into owner's Body (after the Tip, or before the first feature that breaks the
    solid) or on a plain Part solid. Returns the feature it had to go before, or None."""
    body = next((o for o in owner.InList if o.TypeId == "PartDesign::Body"), None)
    if body is None:
        obj.addProperty("App::PropertyLink", "Base", "Hole", "Το στερεό")
        obj.Base = owner
        return None
    tip = body.Tip or owner
    after, breaker = healthy_place(tip, obj)
    if after is None or after == tip:   # healthy, or broken everywhere (execute explains)
        body.addObject(obj)
        return None
    body.insertObject(obj, after, True)
    return breaker


def _new(owner):
    doc = owner.Document
    in_body = any(o.TypeId == "PartDesign::Body" for o in owner.InList)
    # PartDesign::FeatureSubtractivePython crashes 26.3 with the GUI up: use the plain one
    obj = doc.addObject("PartDesign::FeaturePython" if in_body else "Part::FeaturePython", "HoleOnSurface")
    HoleOnSurface(obj)
    return obj


def make_hole(face_owner, face, point, diameter=3.0, mode=MODES[0], depth=5.0):
    """Create the hole at `point` of `face` (a face of face_owner's shape).

    Returns (hole, the feature it had to go before, or None)."""
    p, n = point_and_normal(face, point)
    obj = _new(face_owner)
    obj.Diameter, obj.Mode, obj.Depth = diameter, mode, depth
    obj.Point, obj.Direction = p, inward(face_owner.Shape, p, -n)
    axis = "Z"
    obj.Axis, obj.AxisCentre = axis, axis_centre(face_owner.Shape, axis)
    obj.Angle, obj.Height = angle_height(p, V(obj.AxisCentre), axis)
    breaker = _place(face_owner, obj)
    face_owner.Document.recompute()
    return obj, breaker


def make_sketch_holes(owner, sketch, mode=MODES[0], depth=5.0):
    """Holes at the circles of `sketch` in owner's solid. Returns (hole, breaker or None)."""
    obj = _new(owner)
    obj.Position = "Σκαρίφημα"
    obj.Sketch = sketch
    obj.Mode, obj.Depth = mode, depth
    if sketch_circles(sketch):
        obj.Diameter = sketch_circles(sketch)[0][1]
    breaker = _place(owner, obj)
    owner.Document.recompute()
    return obj, breaker


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------
if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtGui

    try:
        from PySide import QtWidgets
    except ImportError:  # pragma: no cover
        QtWidgets = QtGui

    from PySide import QtCore

    from . import knurl as wk

    STEPS = ["0.1", "0.5", "1", "5"]
    SAVED = ("Diameter", "Mode", "Depth", "Position", "Axis", "AxisCentre", "Angle", "Height", "Aim", "Count",
             "AngleStep", "Reversed")

    def _spin(lo, hi, value, suffix, decimals=2, step=1.0):
        s = QtWidgets.QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setDecimals(decimals)
        s.setSingleStep(step)
        s.setSuffix(suffix)
        s.setValue(value)
        s.setKeyboardTracking(False)        # typing a number: one update when done, not one per digit
        return s

    class TaskHole:
        def __init__(self, obj):
            self.obj = obj
            self.old = {p: getattr(obj, p) for p in SAVED}
            self.form = QtWidgets.QWidget()
            self.form.setWindowTitle("Τρύπα σε επιφάνεια")
            top = QtWidgets.QVBoxLayout(self.form)

            main = QtWidgets.QFormLayout()
            self.pos = QtWidgets.QComboBox()
            self.pos.addItems(POSITIONS if obj.Sketch is not None else POSITIONS[:2])
            self.pos.setCurrentText(obj.Position)
            self.pos.setToolTip("Κλικ: εκεί που έκανες κλικ, κάθετα στην επιφάνεια. Γωνία και ύψος: για "
                                "στρογγυλά κομμάτια, με αριθμούς. Σκαρίφημα: οι κύκλοι του σκαριφήματος.")
            self.dia = _spin(0.1, 500, obj.Diameter.Value, " mm", step=0.5)
            self.mode = QtWidgets.QComboBox()
            self.mode.addItems(MODES)
            self.mode.setCurrentText(obj.Mode)
            self.mode.setToolTip("Ως το πρώτο κενό: περνά τον τοίχο και σταματά (π.χ. ως την κεντρική "
                                 "τρύπα). Βάθος: όσο λες. Διαμπερής: από άκρη σε άκρη.")
            self.depth = _spin(0.1, 1000, obj.Depth.Value, " mm")
            main.addRow("Θέση", self.pos)
            main.addRow("Διάμετρος", self.dia)
            main.addRow("Μέχρι πού", self.mode)
            main.addRow("Βάθος", self.depth)
            top.addLayout(main)

            self.radial = QtWidgets.QGroupBox("Γωνία και ύψος")
            rl = QtWidgets.QFormLayout(self.radial)
            self.axis = QtWidgets.QComboBox()
            self.axis.addItems(AXES)
            self.axis.setCurrentText(obj.Axis)
            self.angle = _spin(-360, 360, obj.Angle.Value, " °", step=5)
            self.angle.setToolTip("Άξονας Z: 0° = προς +X, 90° = προς +Y (αριστερόστροφα, βλέποντας από πάνω).")
            self.height = _spin(-10000, 10000, obj.Height.Value, " mm", step=0.5)
            self.height.setToolTip("0 = η μέση του κομματιού. Με + πάει προς τη μύτη του άξονα (Z: προς τα πάνω).")
            self.hstep = QtWidgets.QComboBox()
            self.hstep.addItems([x + " mm" for x in STEPS])
            self.hstep.setCurrentIndex(1)
            self.hstep.setToolTip("Πόσο αλλάζει το ύψος με κάθε + / −.")
            self.middle = QtWidgets.QPushButton("Στη μέση")
            self.middle.setToolTip("Ύψος 0: η τρύπα ακριβώς στη μέση του κομματιού.")
            hrow = QtWidgets.QHBoxLayout()
            hrow.addWidget(self.height, 1)
            hrow.addWidget(QtWidgets.QLabel("βήμα"))
            hrow.addWidget(self.hstep)
            hrow.addWidget(self.middle)
            self.span = QtWidgets.QLabel()
            self.aim = QtWidgets.QComboBox()
            self.aim.addItems(AIMS)
            self.aim.setCurrentText(obj.Aim)
            self.count = QtWidgets.QSpinBox()
            self.count.setRange(1, 360)
            self.count.setValue(max(1, obj.Count))
            self.step = _spin(-360, 360, obj.AngleStep.Value, " °", step=5)
            self.step.setToolTip("0 = ίσα μοιρασμένες γύρω-γύρω (π.χ. 2 τρύπες = 180°).")
            rl.addRow("Άξονας", self.axis)
            rl.addRow("Γωνία", self.angle)
            rl.addRow("Ύψος", hrow)
            rl.addRow("", self.span)
            rl.addRow("Κατεύθυνση", self.aim)
            rl.addRow("Πόσες τρύπες", self.count)
            rl.addRow("Γωνία ανάμεσα", self.step)
            top.addWidget(self.radial)

            self.sk = QtWidgets.QGroupBox("Σκαρίφημα")
            sl = QtWidgets.QVBoxLayout(self.sk)
            self.rev = QtWidgets.QCheckBox("Ανάποδα (από την άλλη πλευρά του σκαριφήματος)")
            self.rev.setChecked(bool(obj.Reversed))
            sl.addWidget(QtWidgets.QLabel("Κάθε κύκλος του σκαριφήματος είναι μια τρύπα, με τη δική του διάμετρο."))
            sl.addWidget(self.rev)
            top.addWidget(self.sk)

            # every change waits until the user stops for a moment: while FreeCAD recomputes it does not
            # see the mouse let go of + / -, and the box kept counting on its own (Marios, 2026-10-22)
            self.timer = QtCore.QTimer(self.form)
            self.timer.setSingleShot(True)
            self.timer.setInterval(400)
            self.timer.timeout.connect(self.preview)
            for w in (self.dia, self.depth, self.angle, self.height, self.step):
                w.valueChanged.connect(self.later)
            self.count.valueChanged.connect(self.later)
            for w in (self.pos, self.mode, self.aim):
                w.currentIndexChanged.connect(self.later)
            self.axis.currentIndexChanged.connect(self.axis_changed)
            self.rev.toggled.connect(self.later)
            self.hstep.currentIndexChanged.connect(self.step_changed)
            self.middle.clicked.connect(lambda: self.height.setValue(0.0))
            self.step_changed()
            self.show_span()
            self.show_parts()

        def later(self, *args):
            self.show_parts()
            self.timer.start()

        def step_changed(self, *args):
            self.height.setSingleStep(float(STEPS[self.hstep.currentIndex()]))

        def show_span(self):
            base = _base_shape(self.obj)
            if base is None:
                self.span.setText("")
                return
            lo, hi = extent(base, V(self.obj.AxisCentre), self.axis.currentText())
            self.span.setText("Το κομμάτι: ύψος %.2f έως %.2f mm" % (lo, hi))

        def show_parts(self):
            pos = self.pos.currentText()
            self.radial.setVisible(pos == "Γωνία και ύψος")
            self.sk.setVisible(pos == "Σκαρίφημα")
            self.dia.setEnabled(pos != "Σκαρίφημα")
            self.depth.setEnabled(self.mode.currentText() == "Βάθος")

        def axis_changed(self, *args):
            """A new axis: its centre from the part, and the angle and height of the clicked point."""
            base = _base_shape(self.obj)
            axis = self.axis.currentText()
            if base is not None:
                self.obj.Axis = axis
                self.obj.AxisCentre = axis_centre(base, axis)
                ang, h = angle_height(V(self.obj.Point), V(self.obj.AxisCentre), axis)
                for w, val in ((self.angle, ang), (self.height, h)):
                    w.blockSignals(True)
                    w.setValue(val)
                    w.blockSignals(False)
            self.show_span()
            self.preview()

        def preview(self, *args):
            try:
                o = self.obj
                o.Position = self.pos.currentText()
                o.Diameter = self.dia.value()
                o.Mode = self.mode.currentText()
                o.Depth = self.depth.value()
                o.Axis = self.axis.currentText()
                o.Angle = self.angle.value()
                o.Height = self.height.value()
                o.Aim = self.aim.currentText()
                o.Count = self.count.value()
                o.AngleStep = self.step.value()
                o.Reversed = self.rev.isChecked()
                self.show_parts()
                o.Document.recompute()
            except Exception:
                pass

        def accept(self):
            self.timer.stop()
            self.preview()
            Gui.ActiveDocument.resetEdit()
            return True

        def reject(self):
            self.timer.stop()
            for p, val in self.old.items():
                setattr(self.obj, p, val)
            self.obj.Document.recompute()
            Gui.ActiveDocument.resetEdit()
            return True

    class ViewProviderHole:
        def __init__(self, vobj):
            vobj.Proxy = self

        def attach(self, vobj):
            self.Object = vobj.Object

        def getIcon(self):
            return ICON

        def claimChildren(self):
            o = self.Object
            return [x for x in (getattr(o, "Base", None), getattr(o, "Sketch", None)) if x is not None]

        def setEdit(self, vobj, mode=0):
            if mode != 0:
                return None
            Gui.Control.showDialog(TaskHole(vobj.Object))
            return True

        def unsetEdit(self, vobj, mode=0):
            Gui.Control.closeDialog()
            return True

        def doubleClicked(self, vobj):
            Gui.ActiveDocument.setEdit(vobj.Object.Name)
            return True

        def dumps(self):
            return None

        def loads(self, state):
            return None

    def _picked():
        """(owner, face or sketch, picked point or None) of the selection, or (None, reason, None)."""
        for s in Gui.Selection.getSelectionEx("", 0):
            for name, sub, pt in zip(s.SubElementNames, s.SubObjects, s.PickedPoints or [None] * 99):
                if not name.split(".")[-1].startswith("Face"):
                    continue
                owner = s.Object.Tip if s.Object.TypeId == "PartDesign::Body" else s.Object
                if owner is None:
                    return None, "none", None
                if pt is None:
                    u0, u1, v0, v1 = sub.ParameterRange
                    pt = sub.valueAt((u0 + u1) / 2, (v0 + v1) / 2)
                return owner, sub, V(pt)
        # no face: a sketch chosen in the tree (inside a Body the selection names the Body)
        for obj in Gui.Selection.getSelection():
            if obj.TypeId == "Sketcher::SketchObject":
                body = next((o for o in obj.InList if o.TypeId == "PartDesign::Body"), None)
                owner = body.Tip if body is not None else None
                if owner is None or owner == obj:
                    return None, "sketch", None
                return owner, obj, None
        return None, "none", None

    class HoleCommand:
        def GetResources(self):
            return {"Pixmap": ICON, "MenuText": "Τρύπα σε επιφάνεια",
                    "ToolTip": "Κλικ στο κομμάτι εκεί που θέλεις την τρύπα (σε οποιαδήποτε επιφάνεια, και "
                               "καμπύλη), ή διάλεξε ένα σκαρίφημα με κύκλους, μετά το κουμπί. Στο παράθυρο: "
                               "θέση με γωνία και ύψος, προς το κέντρο, πολλές τρύπες γύρω-γύρω."}

        def IsActive(self):
            return App.ActiveDocument is not None

        def Activated(self):
            owner, what, point = _picked()
            if owner is None:
                if what == "sketch":
                    wk._tell("Το σκαρίφημα πρέπει να είναι σε Body",
                             "Το σκαρίφημα δεν είναι μέσα σε Body με στερεό.",
                             ["Φτιάξε το σκαρίφημα μέσα στο Body του κομματιού (Part Design).",
                              "Ή κάνε κλικ στο κομμάτι εκεί που θέλεις την τρύπα."])
                else:
                    wk._tell("Κάνε κλικ στο κομμάτι",
                             "Δεν έχεις κάνει κλικ σε επιφάνεια ούτε έχεις διαλέξει σκαρίφημα.",
                             ["Κάνε κλικ στο κομμάτι, εκεί που θέλεις την τρύπα (στο παράθυρο τη μετακινείς με "
                              "γωνία και ύψος).",
                              "Ή διάλεξε στο δέντρο ένα σκαρίφημα με κύκλους.",
                              "Μετά πάτα το κουμπί «Τρύπα σε επιφάνεια»."])
                return
            doc = owner.Document
            doc.openTransaction("Hole on surface")
            if point is None:
                obj, breaker = make_sketch_holes(owner, what)
                if what.ViewObject is not None:
                    what.ViewObject.Visibility = False
            else:
                obj, breaker = make_hole(owner, what, point)
            if obj.ViewObject is not None:
                ViewProviderHole(obj.ViewObject)
            if getattr(obj, "Base", None) is not None and obj.Base.ViewObject is not None:
                obj.Base.ViewObject.Visibility = False
            doc.commitTransaction()
            Gui.Selection.clearSelection()
            if breaker is not None:
                wk._tell("Η τρύπα μπήκε πιο πριν στο δέντρο",
                         "Το «%s» χαλάει το στερεό (μετά από αυτό κανένα κόψιμο δεν πετυχαίνει), γι' αυτό "
                         "η τρύπα μπήκε πριν από αυτό." % breaker.Label,
                         ["Δεν χρειάζεται να κάνεις τίποτα: η τρύπα και το «%s» είναι και τα δύο στο "
                          "κομμάτι." % breaker.Label,
                          "Αν το «%s» είναι Hole με σπείρωμα, το «Model Thread» το χαλάει." % breaker.Label])
            Gui.ActiveDocument.setEdit(obj.Name)

    def install():
        Gui.addCommand("KnurlWrap_Hole", HoleCommand())
