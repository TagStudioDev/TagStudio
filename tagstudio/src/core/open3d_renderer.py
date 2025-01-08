import hashlib
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from queue import Queue, Empty

import cv2
import numpy as np
import open3d
from PIL import Image

from core.utils.singleton import Singleton

@dataclass
class QueueRequest:
    filename: Path
    size: tuple[int, int]
    mesh: open3d.geometry.TriangleMesh


@dataclass
class QueueResponse:
    filename: Path
    size: tuple[int, int]
    image: np.array


QUEUE_TIMEOUT = 0.1
DEFAULT_SIZE = (160, 160)

# Caching render results in memory, can be persistent if needed
class RenderCache:
    def __init__(self):
        self._cache: dict[str, Image.Image] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _generate_key(filename: Path, size: tuple[int, int]) -> str:
        with filename.open("rb") as f:
            content_hash = hashlib.file_digest(f, "md5")
            content_hash.update(str(size).encode())
        return content_hash.hexdigest()

    def get(self, filename: Path, size: tuple[int, int]) -> Optional[Image.Image]:
        key = self._generate_key(filename, size)
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        return None

    def put(self, filename: Path, size: tuple[int, int], image: Image.Image):
        key = self._generate_key(filename, size)
        with self._lock:
            self._cache[key] = image

    def clear(self):
        with self._lock:
            self._cache.clear()

# A thread safe class to handle multiple rendering calls to the Open3D library
class Open3DRenderer(metaclass=Singleton):
    def __init__(self, render_cache: Optional[RenderCache] = None):
        if render_cache is not None:
            self._rendered_thumbnails_cache = render_cache
        else:
            self._rendered_thumbnails_cache = RenderCache()

        self._stop_event = threading.Event()
        self._render_request_queue = Queue()
        self._image_response_queue = Queue()
        self._render_thread = threading.Thread(target=self._render_loop)
        self._render_thread.start()


    def render(self, filename: Path, size: tuple[int, int]) -> Image.Image:
        image = self._rendered_thumbnails_cache.get(filename, size)
        if image is None:
            image = self._render(filename, size)
            self._rendered_thumbnails_cache.put(filename, size, image)
        return image

    def _render(self, filename: Path, size: tuple[int, int]) -> Image.Image:
        mesh = open3d.io.read_triangle_mesh(filename)
        mesh.compute_vertex_normals()
        request = QueueRequest(filename, size, mesh)
        self._render_request_queue.put(request)

        response: QueueResponse | None = None
        while response is None:
            # Fetch only the correct response
            try:
                response: QueueResponse = self._image_response_queue.get(timeout=QUEUE_TIMEOUT)
                if response.filename != filename:
                    self._image_response_queue.put(response)
                    response = None
            except Empty:
                continue

        image_np = (response.image * 255).astype(np.uint8)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        return Image.fromarray(image_bgr)

    def _render_loop(self):
        vis = open3d.visualization.Visualizer()
        old_size = DEFAULT_SIZE
        self._create_window(vis, old_size)

        while not self._stop_event.set():
            try:
                request: QueueRequest = self._render_request_queue.get(timeout=QUEUE_TIMEOUT)
            except Empty:
                continue

            if request.size != old_size:
                print(f"RESIZING from {old_size} to {request.size}")
                vis.destroy_window()
                self._create_window(vis, request.size)
                old_size = request.size

            
            vis.add_geometry(request.mesh)

            vis.poll_events()
            vis.update_renderer()

            image = vis.capture_screen_float_buffer(do_render=True)
            image_np = np.asarray(image)

            vis.remove_geometry(request.mesh)

            response = QueueResponse(request.filename, request.size, image_np)
            self._image_response_queue.put(response)

    @staticmethod
    def _create_window(visualiser: open3d.visualization.Visualizer, size: tuple[int, int]):
        visualiser.create_window(visible=False, width=size[0], height=size[1])
        opt = visualiser.get_render_option()
        opt.background_color = np.asarray([1, 1, 1])
        opt.light_on = True
        opt.mesh_show_back_face = True
