# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

from __future__ import annotations

import math
import struct
from pathlib import Path
from time import perf_counter
from typing import override

import numpy as np
import structlog
from PIL import Image, ImageColor

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview

logger = structlog.get_logger(__name__)

# TODO: Make these parameters configurable
_MAX_STL_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
_MAX_STL_TRIANGLES = 250_000

_BINARY_STL_HEADER_SIZE = 84
_BINARY_STL_TRIANGLE_COUNT_OFFSET = 80
_BINARY_STL_TRIANGLE_SIZE = 50
_BINARY_STL_TRAILING_CHARS_TO_IGNORE = b"\x00\r\n\t "
_BINARY_STL_DTYPE = np.dtype(
    [
        ("normal", "<f4", (3,)),
        ("vertices", "<f4", (3, 3)),
        ("attribute_byte_count", "<u2"),
    ]
)
_ASCII_VERTEX_MARKERS = (b"vertex", b"VERTEX", b"Vertex")
_MODEL_PADDING = 0.86
_MIN_TRIANGLE_AREA = 1e-12
_MODEL_BASE_COLOR = np.asarray([150.0, 153.0, 163.0], dtype=np.float32)
_LIGHT_DIRECTION = np.asarray([0.35, -0.45, 0.82], dtype=np.float32)
_LIGHT_DIRECTION /= np.linalg.norm(_LIGHT_DIRECTION)
_AMBIENT_INTENSITY = 0.34
_DIFFUSE_INTENSITY = 0.66
_THUMBNAIL_YAW_DEGREES = 35.0
_THUMBNAIL_PITCH_DEGREES = -42.0


class STLRenderError(ValueError):
    """Raised when an STL file cannot be loaded or rendered."""


class STLPreview(BasePreview):
    media_type_name = "model.stl"
    _fallback_icon = "model"

    @override
    @classmethod
    def register_types(cls) -> None:
        MediaTypes.register("model.stl", ".stl", RENDER)

    @override
    @classmethod
    def render(
        cls,
        filepath: Path,
        is_small: bool,
        theme: Theme,
        size: tuple[int, int],
        dpi_scale: float,
    ) -> Image.Image | None:
        return _stl_thumb(filepath, theme, size)


def _stl_thumb(filepath: Path, theme: Theme, size: tuple[int, int]) -> Image.Image | None:
    """Render a thumbnail for an STL file.

    Args:
        filepath (Path): The path of the file.
        theme (Theme): The system color theme.
        size (tuple[int, int]): The target size of the thumbnail.
    """
    bg_color: str = "#1e1e1e" if theme == Theme.DARK else "#FFFFFF"
    im: Image.Image | None = None
    try:
        im = _render_stl_thumbnail(
            filepath=filepath,
            size=max(size),
            bg_color=bg_color,
            max_file_size=_MAX_STL_FILE_SIZE,
            max_triangles=_MAX_STL_TRIANGLES,
        )
    except STLRenderError as e:
        logger.info("Skipping STL thumbnail", filename=filepath.name, error=str(e))
    except Exception as e:
        logger.error("Couldn't render thumbnail", filename=filepath.name, error=type(e).__name__)
    return im


def _parse_bg_color(bg_color: str) -> tuple[int, int, int]:
    """Parses `bg_color` into an RGB triple.

    Raises ValueError rather than STLRenderError: an invalid color is a
    caller argument mistake, not a problem with the STL file being rendered.
    """
    rgb = ImageColor.getrgb(bg_color)
    if len(rgb) != 3:
        raise ValueError(f"bg_color must resolve to an RGB triple, got {bg_color!r}")
    return rgb


def _render_stl_thumbnail(
    filepath: Path,
    size: int,
    bg_color: str,
    max_file_size: int,
    max_triangles: int,
) -> Image.Image:
    """Render an STL file to a square thumbnail image, with orthographic projection."""
    bg_rgb = _parse_bg_color(bg_color)

    file_size = filepath.stat().st_size
    if file_size > max_file_size:
        raise STLRenderError("STL file is too large")

    start_time = perf_counter()
    header = _read_stl_header(filepath)
    read_time = perf_counter()
    triangles, source_triangle_count, stl_kind = _load_stl_triangles(
        filepath, header, file_size, max_triangles
    )
    load_time = perf_counter()
    loaded_triangle_count = len(triangles)
    triangles, normals = _prepare_triangles(triangles)
    prepare_time = perf_counter()
    if len(triangles) == 0:
        raise STLRenderError("STL file contains no renderable triangles")

    projected, depths, normals = _project_triangles(triangles, normals, size)
    project_time = perf_counter()
    image, drawn_triangle_count = _rasterize(projected, depths, normals, size, bg_rgb)
    raster_time = perf_counter()

    logger.debug(
        "[STL Renderer] Rendered thumbnail",
        filename=filepath.name,
        stl_kind=stl_kind,
        file_size=file_size,
        source_triangle_count=source_triangle_count,
        loaded_triangle_count=loaded_triangle_count,
        renderable_triangle_count=len(triangles),
        drawn_triangle_count=drawn_triangle_count,
        read_seconds=round(read_time - start_time, 4),
        load_seconds=round(load_time - read_time, 4),
        prepare_seconds=round(prepare_time - load_time, 4),
        project_seconds=round(project_time - prepare_time, 4),
        raster_seconds=round(raster_time - project_time, 4),
        total_seconds=round(raster_time - start_time, 4),
    )

    return image


def _read_stl_header(filepath: Path) -> bytes:
    """Reads the header of an STL file, avoiding a full file read."""
    with filepath.open("rb") as file:
        return file.read(_BINARY_STL_HEADER_SIZE)


def _load_stl_triangles(
    filepath: Path, header: bytes, file_size: int, max_triangles: int
) -> tuple[np.ndarray, int, str]:
    """STL files come in either binary or ascii format.

    Figure out the format and parse the triangles from the file.
    """
    if len(header) < _BINARY_STL_HEADER_SIZE:
        raise STLRenderError("STL file is too small")

    # Assume binary format. Validate by reading tri count and checking against file size.
    triangle_count = struct.unpack_from("<I", header, _BINARY_STL_TRIANGLE_COUNT_OFFSET)[0]
    expected_size_if_binary = _BINARY_STL_HEADER_SIZE + (triangle_count * _BINARY_STL_TRIANGLE_SIZE)

    if file_size == expected_size_if_binary:
        triangles = _load_binary_stl_triangles(filepath, triangle_count, max_triangles)
        return triangles, triangle_count, "binary"

    if expected_size_if_binary < file_size:
        with filepath.open("rb") as file:
            file.seek(expected_size_if_binary)
            trailing = file.read(file_size - expected_size_if_binary)
        if not trailing.strip(_BINARY_STL_TRAILING_CHARS_TO_IGNORE):
            triangles = _load_binary_stl_triangles(filepath, triangle_count, max_triangles)
            return triangles, triangle_count, "binary"

    # No sign of binary format found. Try parsing ascii-format instead.
    data = filepath.read_bytes()
    triangles, source_triangle_count = _load_ascii_stl_triangles(data, max_triangles)
    return triangles, source_triangle_count, "ascii"


def _load_binary_stl_triangles(
    filepath: Path, triangle_count: int, max_triangles: int
) -> np.ndarray:
    if triangle_count > max_triangles:
        raise STLRenderError("STL file contains too many triangles")

    records = np.memmap(
        filepath,
        dtype=_BINARY_STL_DTYPE,
        mode="r",
        offset=_BINARY_STL_HEADER_SIZE,
        shape=(triangle_count,),
    )
    triangles = records["vertices"].astype(np.float32, copy=True)
    del records
    return triangles


def _split_on_vertex_marker(data: bytes) -> list[bytes]:
    """Split on the "vertex" keyword, tolerating the upper/mixed case some exporters use."""
    for marker in _ASCII_VERTEX_MARKERS:
        chunks = data.split(marker)
        if len(chunks) > 1:
            return chunks
    return [data]


def _load_ascii_stl_triangles(data: bytes, max_triangles: int) -> tuple[np.ndarray, int]:
    chunks = _split_on_vertex_marker(data)
    vertex_count = len(chunks) - 1
    source_triangle_count = vertex_count // 3

    if vertex_count == 0:
        raise STLRenderError("STL file contains no triangles")
    if vertex_count % 3:
        raise STLRenderError("STL file contains incomplete triangles")
    if source_triangle_count > max_triangles:
        raise STLRenderError("STL file contains too many triangles")

    values = np.empty(vertex_count * 3, dtype=np.float32)
    index = 0
    try:
        for chunk in chunks[1:]:
            # maxsplit=3: chunk runs until the next vertex marker, so an unbounded
            # split would rescan the rest of the file for every vertex.
            x, y, z = chunk.split(None, 3)[:3]
            values[index] = float(x)
            values[index + 1] = float(y)
            values[index + 2] = float(z)
            index += 3
    except ValueError as error:
        raise STLRenderError("STL file contains an invalid vertex") from error

    triangles = values.reshape((-1, 3, 3))
    return triangles, source_triangle_count


def _prepare_triangles(triangles: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    finite_mask = np.isfinite(triangles).all(axis=(1, 2))
    triangles = triangles[finite_mask]
    if len(triangles) == 0:
        return triangles, np.empty((0, 3), dtype=np.float32)

    edges_a = triangles[:, 1] - triangles[:, 0]
    edges_b = triangles[:, 2] - triangles[:, 0]
    normals = np.cross(edges_a, edges_b)
    normal_lengths = np.linalg.norm(normals, axis=1)
    valid_mask = normal_lengths > _MIN_TRIANGLE_AREA
    triangles = triangles[valid_mask]
    normals = normals[valid_mask]
    normal_lengths = normal_lengths[valid_mask]
    if len(triangles) == 0:
        return triangles, np.empty((0, 3), dtype=np.float32)

    normals = normals / normal_lengths[:, np.newaxis]

    min_bounds = triangles.reshape((-1, 3)).min(axis=0)
    max_bounds = triangles.reshape((-1, 3)).max(axis=0)
    center = (min_bounds + max_bounds) * 0.5
    extent = float(np.max(max_bounds - min_bounds))
    if not math.isfinite(extent) or extent <= 0:
        raise STLRenderError("STL mesh has zero extent")

    triangles = (triangles - center) / extent
    return triangles.astype(np.float32, copy=False), normals.astype(np.float32, copy=False)


def _project_triangles(
    triangles: np.ndarray, normals: np.ndarray, size: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rotation = _thumbnail_rotation_matrix()
    rotated = triangles @ rotation.T
    rotated_normals = normals @ rotation.T

    points = rotated.reshape((-1, 3))
    min_xy = points[:, :2].min(axis=0)
    max_xy = points[:, :2].max(axis=0)
    center_xy = (min_xy + max_xy) * 0.5
    span = float(np.max(max_xy - min_xy))
    if not math.isfinite(span) or span <= 0:
        raise STLRenderError("STL mesh has zero projected extent")

    scale = (size - 1) * _MODEL_PADDING / span
    projected = np.empty((len(rotated), 3, 2), dtype=np.float32)
    projected[:, :, 0] = ((rotated[:, :, 0] - center_xy[0]) * scale) + ((size - 1) * 0.5)
    projected[:, :, 1] = ((center_xy[1] - rotated[:, :, 1]) * scale) + ((size - 1) * 0.5)

    return projected, rotated[:, :, 2].astype(np.float32), rotated_normals.astype(np.float32)


def _thumbnail_rotation_matrix() -> np.ndarray:
    yaw = math.radians(_THUMBNAIL_YAW_DEGREES)
    pitch = math.radians(_THUMBNAIL_PITCH_DEGREES)
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    cp = math.cos(pitch)
    sp = math.sin(pitch)

    rotate_z = np.asarray([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)
    rotate_x = np.asarray([[1.0, 0.0, 0.0], [0.0, cp, -sp], [0.0, sp, cp]], dtype=np.float32)
    return rotate_x @ rotate_z


def _rasterize(
    projected: np.ndarray,
    depths: np.ndarray,
    normals: np.ndarray,
    size: int,
    bg_rgb: tuple[int, int, int],
) -> tuple[Image.Image, int]:
    pixels = np.empty((size, size, 3), dtype=np.uint8)
    pixels[:, :] = bg_rgb
    depth_buffer = np.full((size, size), -np.inf, dtype=np.float32)

    intensities = _AMBIENT_INTENSITY + (_DIFFUSE_INTENSITY * np.abs(normals @ _LIGHT_DIRECTION))
    colors = np.clip(_MODEL_BASE_COLOR * intensities[:, np.newaxis], 0, 255).astype(np.uint8)

    projected_list = projected.tolist()
    depths_list = depths.tolist()
    colors_list = colors.tolist()
    rendered_any = False
    drawn_triangle_count = 0

    for index in range(len(projected_list)):
        xy = projected_list[index]
        xs = (xy[0][0], xy[1][0], xy[2][0])
        ys = (xy[0][1], xy[1][1], xy[2][1])
        if max(xs) < 0 or min(xs) >= size or max(ys) < 0 or min(ys) >= size:
            continue

        tri_z = depths_list[index]
        tri = (
            (xy[0][0], xy[0][1], tri_z[0]),
            (xy[1][0], xy[1][1], tri_z[1]),
            (xy[2][0], xy[2][1], tri_z[2]),
        )
        if _fill_triangle(pixels, depth_buffer, tri, size, colors_list[index]):
            rendered_any = True
            drawn_triangle_count += 1

    if not rendered_any:
        raise STLRenderError("STL mesh is outside the thumbnail frame")

    return Image.fromarray(pixels, "RGB"), drawn_triangle_count


def _fill_triangle(
    pixels: np.ndarray,
    depth_buffer: np.ndarray,
    tri: tuple[tuple[float, float, float], ...],
    size: int,
    color: list[int],
) -> bool:
    """Fill a single triangle into a pixel buffer via scanline conversion."""
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
    if ay > by:
        ax, ay, az, bx, by, bz = bx, by, bz, ax, ay, az
    if by > cy:
        bx, by, bz, cx, cy, cz = cx, cy, cz, bx, by, bz
    if ay > by:
        ax, ay, az, bx, by, bz = bx, by, bz, ax, ay, az

    y_start = max(0, math.ceil(ay))
    y_end = min(size - 1, math.ceil(cy) - 1)
    r, g, b = color
    drew_any = False

    # a/b/c are the triangle's vertices sorted by y; ta/tb interpolate the left/right
    # edge x and z at each scanline.
    for y in range(y_start, y_end + 1):
        fy = float(y)
        ta = 0.0 if cy == ay else (fy - ay) / (cy - ay)
        xa = ax + ta * (cx - ax)
        za = az + ta * (cz - az)
        if fy < by:
            tb = 0.0 if by == ay else (fy - ay) / (by - ay)
            xb = ax + tb * (bx - ax)
            zb = az + tb * (bz - az)
        else:
            tb = 0.0 if cy == by else (fy - by) / (cy - by)
            xb = bx + tb * (cx - bx)
            zb = bz + tb * (cz - bz)

        if xa > xb:
            xa, xb = xb, xa
            za, zb = zb, za

        x_start = max(0, math.ceil(xa))
        x_end = min(size - 1, math.ceil(xb) - 1)
        for x in range(x_start, x_end + 1):
            tx = 0.0 if xb == xa else (x - xa) / (xb - xa)
            # Linear z interpolation is only correct because the projection is
            # orthographic; this test makes triangles occlude correctly regardless
            # of draw order.
            z = za + tx * (zb - za)
            if z <= depth_buffer[y, x]:
                continue
            depth_buffer[y, x] = z
            pixels[y, x, 0] = r
            pixels[y, x, 1] = g
            pixels[y, x, 2] = b
            drew_any = True

    return drew_any
