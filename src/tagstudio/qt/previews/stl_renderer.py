# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import math
import re
import struct
import threading
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image, ImageDraw

_BINARY_STL_HEADER_SIZE = 84
_BINARY_STL_TRIANGLE_SIZE = 50
_BINARY_STL_DTYPE = np.dtype(
    [
        ("normal", "<f4", (3,)),
        ("vertices", "<f4", (3, 3)),
        ("attribute_byte_count", "<u2"),
    ]
)
_ASCII_FLOAT_PATTERN = rb"[-+]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][-+]?\d+)?"
_ASCII_VERTEX_RE = re.compile(
    rb"(?im)^\s*vertex\s+("
    + _ASCII_FLOAT_PATTERN
    + rb"\s+"
    + _ASCII_FLOAT_PATTERN
    + rb"\s+"
    + _ASCII_FLOAT_PATTERN
    + rb")"
)
_MODEL_PADDING = 0.86
_MIN_TRIANGLE_AREA = 1e-12
_MIN_RENDER_TRIANGLES = 12_000
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
    triangles = _sample_triangles(triangles, _target_triangle_count(size, max_triangles))
    sampled_triangle_count = len(triangles)
    triangles, normals = _prepare_triangles(triangles)
    prepare_time = perf_counter()
    if len(triangles) == 0:
        raise StlRenderError("STL file contains no renderable triangles")

    projected, depths, normals = _project_triangles(triangles, normals, size)
    project_time = perf_counter()
    image = _rasterize(projected, depths, normals, size, bg_color)
    raster_time = perf_counter()

    if _BENCHMARK_STL_RENDERER:
        _print_benchmark(
            filepath=filepath,
            stl_kind=stl_kind,
            file_size=file_size,
            source_triangle_count=source_triangle_count,
            loaded_triangle_count=loaded_triangle_count,
            sampled_triangle_count=sampled_triangle_count,
            renderable_triangle_count=len(triangles),
            read_seconds=read_time - start_time,
            load_seconds=load_time - read_time,
            prepare_seconds=prepare_time - load_time,
            project_seconds=project_time - prepare_time,
            raster_seconds=raster_time - project_time,
            total_seconds=raster_time - start_time,
        )

    return image


def _read_stl_header(filepath: Path) -> bytes:
    with filepath.open("rb") as file:
        return file.read(_BINARY_STL_HEADER_SIZE)


def _load_stl_triangles(
    filepath: Path, header: bytes, file_size: int, max_triangles: int
) -> tuple[np.ndarray, int, str]:
    if len(header) < _BINARY_STL_HEADER_SIZE:
        raise StlRenderError("STL file is too small")

    triangle_count = struct.unpack_from("<I", header, 80)[0]
    expected_size = _BINARY_STL_HEADER_SIZE + (triangle_count * _BINARY_STL_TRIANGLE_SIZE)

    if expected_size == file_size:
        triangles = _load_binary_stl_triangles(filepath, triangle_count, max_triangles)
        return triangles, triangle_count, "binary"

    data = filepath.read_bytes()
    trailing = data[expected_size:] if expected_size <= file_size else b""
    if expected_size < file_size and not trailing.strip(b"\x00\r\n\t "):
        triangles = _load_binary_stl_triangles(filepath, triangle_count, max_triangles)
        return triangles, triangle_count, "binary"

    triangles, source_triangle_count = _load_ascii_stl_triangles(data, max_triangles)
    return triangles, source_triangle_count, "ascii"


def _load_binary_stl_triangles(
    filepath: Path, triangle_count: int, max_triangles: int
) -> np.ndarray:
    records = np.memmap(
        filepath,
        dtype=_BINARY_STL_DTYPE,
        mode="r",
        offset=_BINARY_STL_HEADER_SIZE,
        shape=(triangle_count,),
    )
    vertices = records["vertices"]
    if triangle_count > max_triangles:
        sample_indexes = np.linspace(0, triangle_count - 1, max_triangles, dtype=np.intp)
        vertices = vertices[sample_indexes]

    triangles = vertices.astype(np.float32, copy=True)
    del records
    return triangles


def _load_ascii_stl_triangles(data: bytes, max_triangles: int) -> tuple[np.ndarray, int]:
    max_vertices = max_triangles * 3
    vertex_lines = _ASCII_VERTEX_RE.findall(data)
    loaded_vertices = min(len(vertex_lines), max_vertices)
    loaded_vertices -= loaded_vertices % 3

    if loaded_vertices == 0:
        raise StlRenderError("STL file contains no complete triangles")

    vertex_text = b" ".join(vertex_lines[:loaded_vertices]).decode("ascii")
    values = np.fromstring(vertex_text, dtype=np.float32, sep=" ")
    if len(values) != loaded_vertices * 3:
        raise StlRenderError("STL file contains an invalid vertex")

    triangles = values.reshape((-1, 3, 3))
    return triangles, len(vertex_lines) // 3


def _target_triangle_count(size: int, max_triangles: int) -> int:
    return max_triangles  # min(max_triangles, max(_MIN_RENDER_TRIANGLES, (size * size) // 2))


def _sample_triangles(triangles: np.ndarray, target_count: int) -> np.ndarray:
    if len(triangles) <= target_count:
        return triangles

    sample_indexes = np.linspace(0, len(triangles) - 1, target_count, dtype=np.intp)
    return triangles[sample_indexes]


def _print_benchmark(
    filepath: Path,
    stl_kind: str,
    file_size: int,
    source_triangle_count: int,
    loaded_triangle_count: int,
    sampled_triangle_count: int,
    renderable_triangle_count: int,
    read_seconds: float,
    load_seconds: float,
    prepare_seconds: float,
    project_seconds: float,
    raster_seconds: float,
    total_seconds: float,
) -> None:
    with _benchmark_print_lock:
        print()
        print("[STL Thumbnail Benchmark]")
        print(f"  file:       {filepath}")
        print(f"  format:     {stl_kind}")
        print(f"  size:       {file_size / (1024 * 1024):.2f} MiB")
        print(f"  triangles:  source={source_triangle_count:,}")
        print(f"              loaded={loaded_triangle_count:,}")
        print(f"              sampled={sampled_triangle_count:,}")
        print(f"              renderable={renderable_triangle_count:,}")
        print("  timings:")
        print(f"    read:     {read_seconds * 1000:8.2f} ms")
        print(f"    load:     {load_seconds * 1000:8.2f} ms")
        print(f"    prepare:  {prepare_seconds * 1000:8.2f} ms")
        print(f"    project:  {project_seconds * 1000:8.2f} ms")
        print(f"    raster:   {raster_seconds * 1000:8.2f} ms")
        print(f"    total:    {total_seconds * 1000:8.2f} ms")


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
) -> Image.Image:
    image = Image.new("RGB", (size, size), color=bg_color)
    draw = ImageDraw.Draw(image)
    base_color = np.asarray([150.0, 153.0, 163.0], dtype=np.float32)
    light = np.asarray([0.35, -0.45, 0.82], dtype=np.float32)
    light /= np.linalg.norm(light)

    intensities = 0.34 + (0.66 * np.abs(normals @ light))
    colors = np.clip(base_color * intensities[:, np.newaxis], 0, 255).astype(np.uint8)
    triangle_order = np.argsort(depths.mean(axis=1))
    rendered_any = False

    for index in triangle_order:
        tri = projected[index]
        if (
            tri[:, 0].max() < 0
            or tri[:, 0].min() >= size
            or tri[:, 1].max() < 0
            or tri[:, 1].min() >= size
        ):
            continue

        color = tuple(int(channel) for channel in colors[index])
        draw.polygon([tuple(point) for point in tri], fill=color)
        rendered_any = True

    if not rendered_any:
        raise StlRenderError("STL mesh is outside the thumbnail frame")

    return image
