# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import math
import struct
import threading
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image, ImageColor

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
_BENCHMARK_STL_RENDERER = True
_benchmark_print_lock = threading.Lock()


class StlRenderError(ValueError):
    """Raised when an STL file cannot be loaded or rendered."""


def render_stl_thumbnail(
    filepath: Path,
    size: int,
    bg_color: str,
    max_file_size: int,
    max_triangles: int,
) -> Image.Image:
    """Render an STL file to a square thumbnail image."""
    file_size = filepath.stat().st_size
    if file_size > max_file_size:
        raise StlRenderError("STL file is too large")

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
        raise StlRenderError("STL file contains no renderable triangles")

    projected, depths, normals = _project_triangles(triangles, normals, size)
    project_time = perf_counter()
    image, drawn_triangle_count = _rasterize(projected, depths, normals, size, bg_color)
    raster_time = perf_counter()

    if _BENCHMARK_STL_RENDERER:
        _print_benchmark(
            filepath=filepath,
            stl_kind=stl_kind,
            file_size=file_size,
            source_triangle_count=source_triangle_count,
            loaded_triangle_count=loaded_triangle_count,
            renderable_triangle_count=len(triangles),
            drawn_triangle_count=drawn_triangle_count,
            read_seconds=read_time - start_time,
            load_seconds=load_time - read_time,
            prepare_seconds=prepare_time - load_time,
            project_seconds=project_time - prepare_time,
            raster_seconds=raster_time - project_time,
            total_seconds=raster_time - start_time,
        )

    return image


def _read_stl_header(filepath: Path) -> bytes:
    """Reads the header of an STL file, avoiding a full file read."""
    with filepath.open("rb") as file:
        return file.read(_BINARY_STL_HEADER_SIZE)


def _load_stl_triangles(
    filepath: Path, header: bytes, file_size: int, max_triangles: int
) -> tuple[np.ndarray, int, str]:
    """STL files come in either binary or ascii format. Figure out the format and parse the
    triangles from the file."""
    if len(header) < _BINARY_STL_HEADER_SIZE:
        raise StlRenderError("STL file is too small")

    # Assume binary format. Validate by reading tri count and checking against file size.
    triangle_count = struct.unpack_from("<I", header, _BINARY_STL_TRIANGLE_COUNT_OFFSET)[0]
    expected_size_if_binary = _BINARY_STL_HEADER_SIZE + (triangle_count * _BINARY_STL_TRIANGLE_SIZE)

    if file_size == expected_size_if_binary:
        triangles = _load_binary_stl_triangles(filepath, triangle_count, max_triangles)
        return triangles, triangle_count, "binary"

    data = filepath.read_bytes()
    rest = data[expected_size_if_binary:] if expected_size_if_binary <= file_size else b""
    rest_is_just_whitespaces = not rest.strip(_BINARY_STL_TRAILING_CHARS_TO_IGNORE)
    if file_size > expected_size_if_binary and rest_is_just_whitespaces:
        triangles = _load_binary_stl_triangles(filepath, triangle_count, max_triangles)
        return triangles, triangle_count, "binary"

    # No sign of binary format found. Try parsing ascii-format instead.
    triangles, source_triangle_count = _load_ascii_stl_triangles(data, max_triangles)
    return triangles, source_triangle_count, "ascii"


def _load_binary_stl_triangles(filepath: Path, triangle_count: int, max_triangles: int) -> np.ndarray:
    if triangle_count > max_triangles:
        raise StlRenderError("STL file contains too many triangles")

    records = np.memmap(
        filepath,
        dtype=_BINARY_STL_DTYPE,
        mode="r",
        offset=_BINARY_STL_HEADER_SIZE,
        shape=(triangle_count,),
    )
    vertices = records["vertices"]
    triangles = vertices.astype(np.float32, copy=True)
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
        raise StlRenderError("STL file contains no triangles")
    if vertex_count % 3:
        raise StlRenderError("STL file contains incomplete triangles")
    if source_triangle_count > max_triangles:
        raise StlRenderError("STL file contains too many triangles")

    values = np.empty(vertex_count * 3, dtype=np.float32)
    index = 0
    try:
        for chunk in chunks[1:]:
            x, y, z = chunk.split(None, 3)[:3]
            values[index] = float(x)
            values[index + 1] = float(y)
            values[index + 2] = float(z)
            index += 3
    except ValueError as error:
        raise StlRenderError("STL file contains an invalid vertex") from error

    triangles = values.reshape((-1, 3, 3))
    return triangles, source_triangle_count


def _print_benchmark(
    filepath: Path,
    stl_kind: str,
    file_size: int,
    source_triangle_count: int,
    loaded_triangle_count: int,
    renderable_triangle_count: int,
    drawn_triangle_count: int,
    read_seconds: float,
    load_seconds: float,
    prepare_seconds: float,
    project_seconds: float,
    raster_seconds: float,
    total_seconds: float,
) -> None:
    with _benchmark_print_lock:
        print()  # noqa: T201
        print("[STL Thumbnail Benchmark]")  # noqa: T201
        print(f"  file:       {filepath}")  # noqa: T201
        print(f"  format:     {stl_kind}")  # noqa: T201
        print(f"  size:       {file_size / (1024 * 1024):.2f} MiB")  # noqa: T201
        print(f"  triangles:  source={source_triangle_count:,}")  # noqa: T201
        print(f"              loaded={loaded_triangle_count:,}")  # noqa: T201
        print(f"              renderable={renderable_triangle_count:,}")  # noqa: T201
        print(f"              drawn={drawn_triangle_count:,}")  # noqa: T201
        print("  timings:")  # noqa: T201
        print(f"    read:     {read_seconds * 1000:8.2f} ms")  # noqa: T201
        print(f"    load:     {load_seconds * 1000:8.2f} ms")  # noqa: T201
        print(f"    prepare:  {prepare_seconds * 1000:8.2f} ms")  # noqa: T201
        print(f"    project:  {project_seconds * 1000:8.2f} ms")  # noqa: T201
        print(f"    raster:   {raster_seconds * 1000:8.2f} ms")  # noqa: T201
        print(f"    total:    {total_seconds * 1000:8.2f} ms")  # noqa: T201


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
        raise StlRenderError("STL mesh has zero extent")

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
        raise StlRenderError("STL mesh has zero projected extent")

    scale = (size - 1) * _MODEL_PADDING / span
    projected = np.empty((len(rotated), 3, 2), dtype=np.float32)
    projected[:, :, 0] = ((rotated[:, :, 0] - center_xy[0]) * scale) + ((size - 1) * 0.5)
    projected[:, :, 1] = ((center_xy[1] - rotated[:, :, 1]) * scale) + ((size - 1) * 0.5)

    return projected, rotated[:, :, 2].astype(np.float32), rotated_normals.astype(np.float32)


def _thumbnail_rotation_matrix() -> np.ndarray:
    yaw = math.radians(35.0)
    pitch = math.radians(-42.0)
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
    bg_color: str,
) -> tuple[Image.Image, int]:
    bg_rgb = ImageColor.getrgb(bg_color)
    pixels = np.empty((size, size, 3), dtype=np.uint8)
    pixels[:, :] = bg_rgb

    base_color = np.asarray([150.0, 153.0, 163.0], dtype=np.float32)
    light = np.asarray([0.35, -0.45, 0.82], dtype=np.float32)
    light /= np.linalg.norm(light)

    intensities = 0.34 + (0.66 * np.abs(normals @ light))
    colors = np.clip(base_color * intensities[:, np.newaxis], 0, 255).astype(np.uint8)
    triangle_indexes = _visible_triangle_indexes(normals, depths)
    triangle_order = triangle_indexes[np.argsort(depths[triangle_indexes].mean(axis=1))]

    projected_list = projected.tolist()
    colors_list = colors.tolist()
    rendered_any = False
    drawn_triangle_count = 0

    for index in triangle_order.tolist():
        tri = projected_list[index]
        xs = (tri[0][0], tri[1][0], tri[2][0])
        ys = (tri[0][1], tri[1][1], tri[2][1])
        if max(xs) < 0 or min(xs) >= size or max(ys) < 0 or min(ys) >= size:
            continue

        _fill_triangle(pixels, tri, size, colors_list[index])
        rendered_any = True
        drawn_triangle_count += 1

    if not rendered_any:
        raise StlRenderError("STL mesh is outside the thumbnail frame")

    return Image.fromarray(pixels, "RGB"), drawn_triangle_count


def _fill_triangle(pixels: np.ndarray, tri: list[list[float]], size: int, color: list[int]) -> None:
    """Fill a single triangle directly into a pixel buffer via scanline conversion."""
    (ax, ay), (bx, by), (cx, cy) = tri
    if ay > by:
        ax, ay, bx, by = bx, by, ax, ay
    if by > cy:
        bx, by, cx, cy = cx, cy, bx, by
    if ay > by:
        ax, ay, bx, by = bx, by, ax, ay

    y_start = max(0, math.ceil(ay))
    y_end = min(size - 1, math.ceil(cy) - 1)
    r, g, b = color

    for y in range(y_start, y_end + 1):
        fy = float(y)
        xa = ax if cy == ay else ax + (fy - ay) / (cy - ay) * (cx - ax)
        if fy < by:
            xb = ax if by == ay else ax + (fy - ay) / (by - ay) * (bx - ax)
        else:
            xb = bx if cy == by else bx + (fy - by) / (cy - by) * (cx - bx)

        x_start = max(0, math.ceil(min(xa, xb)))
        x_end = min(size - 1, math.ceil(max(xa, xb)) - 1)
        for x in range(x_start, x_end + 1):
            pixels[y, x, 0] = r
            pixels[y, x, 1] = g
            pixels[y, x, 2] = b


def _visible_triangle_indexes(normals: np.ndarray, depths: np.ndarray) -> np.ndarray:
    front_facing = normals[:, 2] > 0
    front_count = int(np.count_nonzero(front_facing))
    back_count = len(normals) - front_count

    if front_count > len(normals) * 0.25 and back_count > len(normals) * 0.25:
        front_indexes = np.flatnonzero(front_facing)
        back_indexes = np.flatnonzero(~front_facing)
        front_depth = float(depths[front_indexes].mean())
        back_depth = float(depths[back_indexes].mean())
        return front_indexes if front_depth >= back_depth else back_indexes

    return np.arange(len(normals))
