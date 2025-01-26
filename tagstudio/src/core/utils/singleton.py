# from gist: https://gist.github.com/JonatanNevo/c48efb9a13636252ddf48e3b864899f0
from typing import TypeVar, Generic, Any

T = TypeVar("T")


class Singleton(type, Generic[T]):
    _instances: dict['Singleton[T]', T] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> T:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]