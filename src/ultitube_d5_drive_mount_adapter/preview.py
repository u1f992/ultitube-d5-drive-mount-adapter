from pathlib import Path

import cadquery as cq
import numpy as np
import numpy.typing as npt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

Array = npt.NDArray[np.float64]

MESH_TOLERANCE = 0.02
MESH_ANGULAR_TOLERANCE = 0.1
LIGHT_DIRECTION = np.array([0.35, -0.45, 0.8])
AMBIENT = 0.3
DIFFUSE = 0.6
PANEL_INCHES = 7.0
DPI = 90

VIEWS = {
    "above, from -X -Y": (42, -115),
    "above, from +X -Y": (25, -60),
    "top": (90, -90),
    "from +X": (0, 0),
    "below, from +X -Y": (-35, -60),
}


def triangles(shape: cq.Shape) -> Array:
    vertices, faces = shape.tessellate(MESH_TOLERANCE, MESH_ANGULAR_TOLERANCE)
    points: Array = np.array([[v.x, v.y, v.z] for v in vertices])
    mesh: Array = points[np.array(faces)]
    return mesh


def shades(mesh: Array) -> Array:
    cross = np.cross(mesh[:, 1] - mesh[:, 0], mesh[:, 2] - mesh[:, 0])
    length = np.linalg.norm(cross, axis=1, keepdims=True)
    normals = cross / np.where(length == 0, 1, length)
    brightness: Array = np.abs(normals @ LIGHT_DIRECTION).clip(0, 1) * DIFFUSE + AMBIENT
    return np.repeat(brightness[:, None], 3, axis=1)


def render_preview(shape: cq.Shape, path: Path) -> None:
    """Write a PNG that shows `shape` from every direction in `VIEWS`, side by side in that order."""
    mesh = triangles(shape)
    colours = shades(mesh)
    low, high = mesh.min((0, 1)), mesh.max((0, 1))
    figure = Figure(figsize=(PANEL_INCHES * len(VIEWS), PANEL_INCHES))
    for index, (title, (elevation, azimuth)) in enumerate(VIEWS.items()):
        axes = figure.add_subplot(1, len(VIEWS), index + 1, projection="3d")
        axes.add_collection3d(Poly3DCollection(mesh, facecolors=colours, linewidths=0))
        axes.set_xlim(low[0], high[0])
        axes.set_ylim(low[1], high[1])
        axes.set_zlim(low[2], high[2])
        axes.set_box_aspect(high - low)
        axes.view_init(elev=elevation, azim=azimuth)
        axes.set_axis_off()
        axes.text2D(0.5, 0.92, title, transform=axes.transAxes, ha="center", va="top")
    figure.tight_layout()
    figure.savefig(path, dpi=DPI)
