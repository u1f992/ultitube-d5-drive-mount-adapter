import argparse
from pathlib import Path

import cadquery as cq

from .adapter import ultitube_drive_mount_adapter
from .preview import render_preview

PART_NAME = "ultitube_drive_mount_adapter"
STL_TOLERANCE = 0.02
STL_ANGULAR_TOLERANCE = 0.1


def export(directory: Path) -> tuple[float, float, float]:
    """Write the adapter as STEP, STL and a PNG preview named `PART_NAME` into `directory` and return the bounding box size in mm."""
    shape = ultitube_drive_mount_adapter()
    bb = shape.BoundingBox()
    directory.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(directory / f"{PART_NAME}.step"))
    shape.exportStl(
        str(directory / f"{PART_NAME}.stl"),
        STL_TOLERANCE,
        STL_ANGULAR_TOLERANCE,
        relative=False,
    )
    render_preview(shape, directory / f"{PART_NAME}.png")
    return (bb.xlen, bb.ylen, bb.zlen)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the ULTITUBE D5 drive mount adapter as STEP and STL with a PNG preview."
    )
    parser.add_argument("out", type=Path, nargs="?", default=Path("out"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    x, y, z = export(args.out)
    print(f"{PART_NAME} {x:.1f} x {y:.1f} x {z:.1f} mm")
