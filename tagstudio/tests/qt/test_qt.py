from pathlib import Path

from src.core.library import Entry


def test_update_thumbs(qt_driver):
    qt_driver.frame_content = [Entry(path=Path("/tmp/foo"))]
    qt_driver.update_thumbs()
