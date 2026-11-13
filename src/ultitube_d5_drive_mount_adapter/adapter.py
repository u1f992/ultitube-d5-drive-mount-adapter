import math

import cadquery as cq


class MeasuredOnUltitubeBundledBracket:
    SHEET_THICKNESS = 1.5
    PLATE_LENGTH = 75.0
    PASSAGE_DIAMETER = 63.5
    HOLE_PITCH = 55.0
    HOLE_DIAMETER = 4.5
    PUMP_PROTRUSION_BELOW_PLATE_LIMIT = 5.0


class Sff8201BottomMountingHoles:
    SPACING_ACROSS_WIDTH_A29 = 61.72
    FIRST_FROM_CONNECTOR_END_A50 = 14.00
    SECOND_FROM_CONNECTOR_END_A51 = 90.60


class Iso273CoarseClearanceHole:
    M3 = 3.6


SHEET_THICKNESS = MeasuredOnUltitubeBundledBracket.SHEET_THICKNESS
BEND_INNER_RADIUS = SHEET_THICKNESS

PASSAGE_ALLOWANCE = 0.5
ULTITUBE_PASSAGE_DIAMETER = (
    MeasuredOnUltitubeBundledBracket.PASSAGE_DIAMETER + PASSAGE_ALLOWANCE
)
ULTITUBE_HOLE_PITCH = MeasuredOnUltitubeBundledBracket.HOLE_PITCH
ULTITUBE_HOLE_ALLOWANCE = 0.5
ULTITUBE_HOLE_DIAMETER = (
    MeasuredOnUltitubeBundledBracket.HOLE_DIAMETER + ULTITUBE_HOLE_ALLOWANCE
)

DRIVE_HOLE_PITCH_X = (
    Sff8201BottomMountingHoles.SECOND_FROM_CONNECTOR_END_A51
    - Sff8201BottomMountingHoles.FIRST_FROM_CONNECTOR_END_A50
)
DRIVE_HOLE_PITCH_Y = Sff8201BottomMountingHoles.SPACING_ACROSS_WIDTH_A29
DRIVE_HOLE_DIAMETER = Iso273CoarseClearanceHole.M3
DRIVE_SEAT_DIAMETER = 10.0
SEAT_MARGIN = 0.5

CABLE_SPACE_BELOW_PUMP = 10.0
PLATE_LENGTH = MeasuredOnUltitubeBundledBracket.PLATE_LENGTH
PLATE_RISE = (
    MeasuredOnUltitubeBundledBracket.PUMP_PROTRUSION_BELOW_PLATE_LIMIT
    + CABLE_SPACE_BELOW_PUMP
)
TAB_CORNER_RADIUS = 2.0
FLAT_BEFORE_BEND = 1.0

PLATE_HALF_LENGTH = PLATE_LENGTH / 2
OUTER_BEND_RADIUS = BEND_INNER_RADIUS + SHEET_THICKNESS
BEND_LEAD = OUTER_BEND_RADIUS + FLAT_BEFORE_BEND
TAB_WIDTH = DRIVE_SEAT_DIAMETER + 2 * SEAT_MARGIN
DRIVE_HOLE_X = DRIVE_HOLE_PITCH_X / 2
DRIVE_HOLE_Y = DRIVE_HOLE_PITCH_Y / 2
WALL_OUTER_Y = DRIVE_HOLE_Y + DRIVE_SEAT_DIAMETER / 2 + OUTER_BEND_RADIUS
WALL_HALF_LENGTH = DRIVE_HOLE_X + TAB_WIDTH / 2
TAB_END_Y = DRIVE_HOLE_Y - TAB_WIDTH / 2
WALL_TOP_BEYOND_PLATE = PLATE_RISE - BEND_INNER_RADIUS
WALL_BOTTOM_BETWEEN_TABS = OUTER_BEND_RADIUS


def box_between(
    low: tuple[float, float, float], high: tuple[float, float, float]
) -> cq.Workplane:
    length, width, height = (b - a for a, b in zip(low, high))
    return cq.Workplane("XY").box(length, width, height, centered=False).translate(low)


def z_hole(
    diameter: float, x: float, y: float, z_low: float, z_high: float
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(diameter / 2)
        .extrude(z_high - z_low + 2)
        .translate((x, y, z_low - 1))
    )


def plate() -> cq.Workplane:
    half_width = WALL_OUTER_Y - BEND_LEAD
    return box_between(
        (-PLATE_HALF_LENGTH, -half_width, PLATE_RISE),
        (PLATE_HALF_LENGTH, half_width, PLATE_RISE + SHEET_THICKNESS),
    )


def vertex_at(wire: cq.Wire, y: float, z: float) -> cq.Vertex:
    return min(wire.Vertices(), key=lambda v: math.hypot(v.Y - y, v.Z - z))


def side_profile() -> cq.Wire:
    t = SHEET_THICKNESS
    start, wall_outer, wall_inner = (
        WALL_OUTER_Y - BEND_LEAD,
        WALL_OUTER_Y,
        WALL_OUTER_Y - t,
    )
    outline = [
        (start, PLATE_RISE + t),
        (wall_outer, PLATE_RISE + t),
        (wall_outer, 0.0),
        (TAB_END_Y, 0.0),
        (TAB_END_Y, t),
        (wall_inner, t),
        (wall_inner, PLATE_RISE),
        (start, PLATE_RISE),
    ]
    wire = cq.Wire.makePolygon([cq.Vector(0, y, z) for y, z in outline], close=True)
    for (y, z), radius in (
        (outline[1], OUTER_BEND_RADIUS),
        (outline[2], OUTER_BEND_RADIUS),
        (outline[5], BEND_INNER_RADIUS),
        (outline[6], BEND_INNER_RADIUS),
    ):
        wire = wire.fillet2D(radius, [vertex_at(wire, y, z)])
    return wire


def tab_pad(x: float) -> cq.Workplane:
    pad = box_between(
        (x - TAB_WIDTH / 2, TAB_END_Y, -1),
        (x + TAB_WIDTH / 2, WALL_OUTER_Y + 2, WALL_BOTTOM_BETWEEN_TABS),
    )
    return pad.edges("|Z").edges("<Y").fillet(TAB_CORNER_RADIUS)


def flange_cutter() -> cq.Workplane:
    cutter = box_between(
        (-WALL_HALF_LENGTH - 1, TAB_END_Y - 1, -1),
        (WALL_HALF_LENGTH + 1, WALL_OUTER_Y + 1, WALL_BOTTOM_BETWEEN_TABS),
    )
    for x in (-DRIVE_HOLE_X, DRIVE_HOLE_X):
        cutter = cutter.cut(tab_pad(x))
    return cutter


def wall_top_cutter(x_sign: int) -> cq.Workplane:
    low = (PLATE_HALF_LENGTH, WALL_OUTER_Y - BEND_LEAD - 1, WALL_TOP_BEYOND_PLATE)
    high = (WALL_HALF_LENGTH + 1, WALL_OUTER_Y + 1, PLATE_RISE + SHEET_THICKNESS + 1)
    cutter = box_between(low, high)
    return cutter if x_sign > 0 else cutter.mirror("YZ")


def side() -> cq.Workplane:
    face = cq.Face.makeFromWires(side_profile())
    blank = cq.Solid.extrudeLinear(
        face, cq.Vector(2 * WALL_HALF_LENGTH, 0, 0)
    ).translate(cq.Vector(-WALL_HALF_LENGTH, 0, 0))
    body = cq.Workplane("XY").newObject([blank]).cut(flange_cutter())
    for x_sign in (1, -1):
        body = body.cut(wall_top_cutter(x_sign))
    return body


def ultitube_drive_mount_adapter() -> cq.Shape:
    """Adapter that carries an ULTITUBE D5 on one 2.5-inch drive position.

    The four tabs carry through holes on the bottom mounting hole pattern of a 2.5-inch drive (SFF-8201).
    The M3 screws that would thread into a drive pass up through the tabs and are held by M3 nuts.
    The underside of the tabs is z = 0 and the centre of the ULTITUBE passage is the origin.
    X is the long side of the drive, and the space under the plate is open toward both X ends.
    """
    one_side = side()
    body = plate().union(one_side).union(one_side.mirror("XZ")).clean()
    plate_top = PLATE_RISE + SHEET_THICKNESS
    body = body.cut(z_hole(ULTITUBE_PASSAGE_DIAMETER, 0, 0, PLATE_RISE, plate_top))
    half = ULTITUBE_HOLE_PITCH / 2
    for x in (-half, half):
        for y in (-half, half):
            body = body.cut(z_hole(ULTITUBE_HOLE_DIAMETER, x, y, PLATE_RISE, plate_top))
    for x in (-DRIVE_HOLE_X, DRIVE_HOLE_X):
        for y in (-DRIVE_HOLE_Y, DRIVE_HOLE_Y):
            body = body.cut(z_hole(DRIVE_HOLE_DIAMETER, x, y, 0, SHEET_THICKNESS))
    return body.findSolid()
