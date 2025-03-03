__version__ = "9.3.2"

__all__ = ("__version__",)

import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__)))
)  # add this so that `poetry run tagstudio` works
