# Based off example from Refactoring Guru:
# https://refactoring.guru/design-patterns/singleton/python/example#example-1
# Adapted for TagStudio: https://github.com/CyanVoxel/TagStudio

from threading import Lock


class Singleton(type):
    """A thread-safe implementation of a Singleton."""

    _instances: dict = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]
