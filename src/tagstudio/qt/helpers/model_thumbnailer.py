import threading
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue

import numpy as np
import numpy.typing as npt
import structlog
from open3d.io import read_triangle_model
from open3d.visualization.rendering import (
    MaterialRecord,
    OffscreenRenderer,
    TriangleMeshModel,
)
from PIL import Image

logger = structlog.get_logger(__name__)


@dataclass
class QueueRequest:
    filename: Path
    size: tuple[int, int]
    model: TriangleMeshModel


@dataclass
class QueueResponse:
    filename: Path
    size: tuple[int, int]
    image: npt.NDArray


QUEUE_TIMEOUT = 0.1
DEFAULT_SIZE = (256, 256)


# A thread safe class to handle multiple rendering calls to the Open3D library
class Open3DRenderer:
    def __init__(self):
        self._stop_event = threading.Event()
        self._render_request_queue = Queue()
        self._image_response_queue = Queue()
        self.UP = [0, 1, 0]
        self.FOV = 60
        self.DISTANCE_SCALE = 1.0
        self.BG_COLOR = (0.5, 0.5, 0.5, 1.0)
        self.renderer = None

        # Primarily for .STL files
        self.default_mat = MaterialRecord()
        self.default_mat.base_color = [1.0, 0.5, 0.0, 1.0]
        self.default_mat.shader = "defaultLit"

        self._render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self._render_thread.start()

    # ! I do not know why .mtl's are getting passed here so I just kick them out for now
    def render(self, filename: Path, size: tuple[int, int]) -> Image.Image:
        if filename.suffix == ".mtl":
            return None
        return self._render(filename, size)

    def _render(self, filename: Path, size: tuple[int, int]) -> Image.Image:
        model = read_triangle_model(filename)
        request = QueueRequest(filename, size, model)
        self._render_request_queue.put(request)

        response: QueueResponse | None = None
        while response is None:
            # Fetch only the correct response
            try:
                response = self._image_response_queue.get(timeout=QUEUE_TIMEOUT)
                if response.filename != filename:
                    self._image_response_queue.put(response)
                    response = None
            except Empty:
                continue

        return Image.fromarray(response.image)

    def _update_camera(self, renderer: OffscreenRenderer, model: TriangleMeshModel):
        combined_bounding_box = None
        # Iterate through all meshes to compute the combined bounding box
        for mesh_model in model.meshes:
            mesh = mesh_model.mesh
            bounding_box = mesh.get_axis_aligned_bounding_box()

            if combined_bounding_box is None:
                combined_bounding_box = bounding_box
            else:
                combined_bounding_box = combined_bounding_box + bounding_box

        # Get the center of the combined bounding box
        center = combined_bounding_box.get_center()

        # Calculate the diagonal size of the bounding box
        diagonal = combined_bounding_box.get_extent()
        distance = np.linalg.norm(diagonal) * self.DISTANCE_SCALE
        eye = center + np.array([1, 1, 1]) * distance / np.linalg.norm([1, 1, 1])

        # Vertical offset helps center object in render better
        vertical_offset = 0.4
        eye[1] += vertical_offset
        renderer.setup_camera(self.FOV, center, eye, self.UP)

    def _render_loop(self):
        old_size = DEFAULT_SIZE
        while not self._stop_event.set():
            try:
                request: QueueRequest = self._render_request_queue.get(timeout=QUEUE_TIMEOUT)
            except Empty:
                continue

            if self.renderer is not None and request.size != old_size:
                logger.info(f"Releasing renderer for resize from {old_size} to {request.size}")
                del self.renderer
                self.renderer = None

            if self.renderer is None:
                logger.info(f"RESIZING from {old_size} to {request.size}")
                self.renderer = OffscreenRenderer(request.size[0], request.size[1])
                old_size = request.size

            # Setup Scene
            self.renderer.scene.clear_geometry()
            self.renderer.scene.add_model("model", request.model)

            # If stl paint the model
            if request.filename.suffix == ".stl":
                self.renderer.scene.update_material(self.default_mat)

            self.renderer.scene.set_background(self.BG_COLOR)

            # Update the camera position
            self._update_camera(self.renderer, request.model)

            # Render the image
            image = self.renderer.render_to_image()
            image_np = np.asarray(image)

            response = QueueResponse(request.filename, request.size, image_np)
            self._image_response_queue.put(response)
