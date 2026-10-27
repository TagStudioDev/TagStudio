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
from PIL import Image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview

logger = structlog.get_logger(__name__)

# TODO: Make these parameters configurable
_MAX_STL_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
_MAX_STL_TRIANGLES = 500_000

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
_MODEL_BASE_COLOR = np.asarray([144.0, 148.0, 160.0], dtype=np.float32)  # Slightly cool gray
_LIGHT_VECTOR = np.asarray([-0.2, 0.4, 0.9], dtype=np.float32)
_LIGHT_DIRECTION = _LIGHT_VECTOR / np.linalg.norm(_LIGHT_VECTOR)
_AMBIENT_INTENSITY = 0.4
_DIFFUSE_INTENSITY = 0.75
_THUMBNAIL_YAW_DEGREES = 45.0  # Isometric projection
_THUMBNAIL_PITCH_DEGREES = -60.0
_RASTER_BATCH_AREA = 500_000  # Number of bounding box pixels tested at once
_EDGE_TOLERANCE = 0.00001  # Tolerance for overlapping shared edges to hide seams


class STLRenderError(ValueError):
    """Raised when an STL file cannot be loaded or rendered."""


class STLPreview(BasePreview):
    media_type_name = "model.stl"

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
        return _stl_thumb(filepath, size)


def _stl_thumb(filepath: Path, size: tuple[int, int]) -> Image.Image | None:
    """Render a thumbnail for an STL file.

    Args:
        filepath (Path): The path of the file.
        size (tuple[int, int]): The target size of the thumbnail.
    """
    im: Image.Image | None = None
    try:
        im = _render_stl_thumbnail(
            filepath=filepath,
            size=max(size),
            max_file_size=_MAX_STL_FILE_SIZE,
            max_triangles=_MAX_STL_TRIANGLES,
        )
    except STLRenderError as e:
        logger.info("Skipping STL thumbnail", filename=filepath.name, error=str(e))
    except Exception as e:
        logger.error("Couldn't render thumbnail", filename=filepath.name, error=type(e).__name__)
    return im


def _render_stl_thumbnail(
    filepath: Path,
    size: int,
    max_file_size: int,
    max_triangles: int,
) -> Image.Image:
    """Render an STL file to a square thumbnail image, with orthographic projection."""
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
    image, drawn_triangle_count = _rasterize(projected, depths, normals, size)
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
    """Read the header of an STL file."""
    with filepath.open("rb") as file:
        return file.read(_BINARY_STL_HEADER_SIZE)


def _load_stl_triangles(
    filepath: Path, header: bytes, file_size: int, max_triangles: int
) -> tuple[np.ndarray, int, str]:
    """STL files come in either binary or ASCII format.

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

    # No sign of binary format found. Try parsing as the ASCII format instead.
    data = filepath.read_bytes()
    triangles, source_triangle_count = _load_ascii_stl_triangles(data, max_triangles)
    return triangles, source_triangle_count, "ascii"


def _load_binary_stl_triangles(
    filepath: Path, triangle_count: int, max_triangles: int
) -> np.ndarray:
    if triangle_count > max_triangles:
        raise STLRenderError("STL file contains too many triangles")

    return np.fromfile(
        filepath, dtype=_BINARY_STL_DTYPE, count=triangle_count, offset=_BINARY_STL_HEADER_SIZE
    )["vertices"]


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
) -> tuple[Image.Image, int]:
    """Draw the triangles for the model. Only surfaces nearest to the camera are kept.

    Args:
        projected (np.ndarray): Each triangle's three corners as image x and y, shaped (n, 3, 2).
        depths (np.ndarray): Each corner's depth, higher being nearer the camera, shaped (n, 3).
        normals (np.ndarray): Each triangle's unit normal, used for shading, shaped (n, 3).
        size (int): The width and height of the square image in pixels.

    Returns:
        tuple[Image.Image, int]: The image and how many triangles cover at least one pixel.
    """
    # Flip any normals that aren't facing the camera in case file has inverted normals
    normals = np.where(normals[:, 2:3] < 0, -normals, normals)
    # Flat shading with one color per triangle
    diffuse = np.clip(normals @ _LIGHT_DIRECTION, 0, None)
    intensities = _AMBIENT_INTENSITY + (_DIFFUSE_INTENSITY * diffuse)
    colors = np.clip(_MODEL_BASE_COLOR * intensities[:, np.newaxis], 0, 255).astype(np.uint8)

    # Each triangle's bounding box of pixels
    x_starts, y_starts, widths, pixel_area = _pixel_bounds(projected, size)
    steps = _interpolation_steps(projected, depths, x_starts, y_starts)
    pixel_area[~np.isfinite(steps).all(axis=(1, 2))] = 0  # Skip edge-on triangles

    # Nearest depth and triangle at each pixel
    depth_buffer = np.full(size * size, -np.inf, dtype=np.float32)
    triangle_buffer = np.full(size * size, -1, dtype=np.int32)
    is_drawn = np.zeros(len(projected), dtype=bool)

    # Test the pixels in each triangle's bounding box for whether the triangle covers them, only
    # keeping the nearest. Whole triangles go in batches of up to _RASTER_BATCH_AREA pixels.
    area_ends = np.cumsum(pixel_area)
    batch_start = 0
    while batch_start < len(pixel_area):
        area_limit = area_ends[batch_start] - pixel_area[batch_start] + _RASTER_BATCH_AREA
        # At least one triangle
        batch_end = max(batch_start + 1, int(np.searchsorted(area_ends, area_limit, side="right")))
        batch_areas = pixel_area[batch_start:batch_end]

        # The triangle and its column + row in the bounding box for each pixel
        triangles = np.repeat(np.arange(batch_start, batch_end, dtype=np.int32), batch_areas)
        bounding_box_offsets = np.arange(len(triangles), dtype=np.int32) - np.repeat(
            (np.cumsum(batch_areas) - batch_areas).astype(np.int32), batch_areas
        )
        local_x = bounding_box_offsets % widths[triangles]
        local_y = bounding_box_offsets // widths[triangles]

        # Barycentric weights for corners 0 and 1, and the depth, at each pixel
        pixel_steps = steps[triangles]
        x = local_x.astype(np.float32)[:, np.newaxis]
        y = local_y.astype(np.float32)[:, np.newaxis]
        values = pixel_steps[:, :, 0] * x + pixel_steps[:, :, 1] * y + pixel_steps[:, :, 2]
        weight_0, weight_1, z = values[:, 0], values[:, 1], values[:, 2]
        # All three weights at 0 or more means the pixel is inside the triangle.
        # They always add up to 1, so corner 2's weight is 1 minus the other two.
        inside = (
            (weight_0 >= -_EDGE_TOLERANCE)
            & (weight_1 >= -_EDGE_TOLERANCE)
            & (weight_0 + weight_1 <= 1 + _EDGE_TOLERANCE)
        )

        # Positions in the image of the pixels inside their triangle
        triangles, z = triangles[inside], z[inside]
        image_positions = (y_starts[triangles] + local_y[inside]) * size + x_starts[triangles]
        image_positions += local_x[inside]
        is_drawn[triangles] = True

        # Keep the nearest depth at each position and the triangle it came from
        np.maximum.at(depth_buffer, image_positions, z)
        is_nearest = z == depth_buffer[image_positions]
        triangle_buffer[image_positions[is_nearest]] = triangles[is_nearest]
        batch_start = batch_end

    if not is_drawn.any():
        raise STLRenderError("STL mesh is outside the thumbnail frame")

    # Color the covered pixels
    image = np.zeros((size * size, 4), dtype=np.uint8)
    covered = triangle_buffer >= 0
    image[covered, :3] = colors[triangle_buffer[covered]]
    image[covered, 3] = 255
    return Image.fromarray(image.reshape((size, size, 4)), "RGBA"), int(is_drawn.sum())


def _pixel_bounds(
    projected: np.ndarray, size: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Each triangle's top-left pixel's column & row, bounding box width, and bounding box area."""
    xs = projected[:, :, 0]
    ys = projected[:, :, 1]

    # Round within whole pixels to stay within the image
    x_starts = np.clip(np.ceil(xs.min(axis=1)), 0, size).astype(np.int32)
    y_starts = np.clip(np.ceil(ys.min(axis=1)), 0, size).astype(np.int32)
    x_ends = np.clip(np.floor(xs.max(axis=1)), -1, size - 1).astype(np.int32)
    y_ends = np.clip(np.floor(ys.max(axis=1)), -1, size - 1).astype(np.int32)
    widths = np.maximum(x_ends - x_starts + 1, 0)
    heights = np.maximum(y_ends - y_starts + 1, 0)
    return x_starts, y_starts, widths, widths.astype(np.int64) * heights


def _interpolation_steps(
    projected: np.ndarray, depths: np.ndarray, x_starts: np.ndarray, y_starts: np.ndarray
) -> np.ndarray:
    """Each triangle's barycentric weights and depth as steps across its bounding box's pixels.

    A step (a, b, c) is how much a value changes per pixel right (a) and down (b), and its value
    at the bounding box's top-left pixel (c), so a pixel's value is "a * column + b * row + c".

    The weights tell whether a pixel is inside the triangle and blend the corners' depths there.

    Returns:
        np.ndarray: Steps for corner 0's weight, corner 1's weight, and the depth, shaped (n, 3, 3).
    """
    x0, x1, x2 = projected[:, :, 0].astype(np.float64).T
    y0, y1, y2 = projected[:, :, 1].astype(np.float64).T
    z0, z1, z2 = depths.astype(np.float64).T
    origin_x = x_starts.astype(np.float64)
    origin_y = y_starts.astype(np.float64)

    with np.errstate(divide="ignore", invalid="ignore"):  # Ignore zero-area triangles
        # The barycentric weights divide by double the area so each is 1 at its own corner.
        # The area can be negative depending on the corner order, which the division cancels out.
        doubled_area = (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)
        weight_0 = np.stack(
            [
                (y1 - y2) / doubled_area,
                (x2 - x1) / doubled_area,
                ((x2 - x1) * (origin_y - y1) - (y2 - y1) * (origin_x - x1)) / doubled_area,
            ],
            axis=-1,
        )
        weight_1 = np.stack(
            [
                (y2 - y0) / doubled_area,
                (x0 - x2) / doubled_area,
                ((x0 - x2) * (origin_y - y2) - (y0 - y2) * (origin_x - x2)) / doubled_area,
            ],
            axis=-1,
        )
        # Blending the three corner depths by the weights gives the depth at each pixel.
        # NOTE: Blending depth linearly like this is only correct because the view is orthographic.
        depth = weight_0 * (z0 - z2)[:, np.newaxis] + weight_1 * (z1 - z2)[:, np.newaxis]
        depth[:, 2] += z2  # Adds corner 2's depth, whose weight is 1 minus the other two
    return np.stack([weight_0, weight_1, depth], axis=1).astype(np.float32)
