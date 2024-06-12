import logging
import os.path
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Callable

ERROR = f"[ERROR]"
WARNING = f"[WARNING]"
INFO = f"[INFO]"

logging.basicConfig(format="%(message)s", level=logging.INFO)

def delete_file(path: str | Path, callback: Callable):
    _path = str(path)
    logging.info(f"Deleting file: {_path}")
    if not os.path.exists(_path):
        logging.error(f"File not found: {_path}")
        return
    try:
        os.remove(path)
        callback()
    except:
        traceback.print_exc()

class FileDeleterHelper:

    def __init__(self, filepath: str | Path):
        self.filepath = str(filepath)

    def set_filepath(self, filepath: str | Path):
        self.filepath = str(filepath)

    def set_delete_callback(self, callback: Callable):
        self.delete_callback = callback

    def delete_file(self):
        delete_file(self.filepath, self.delete_callback)