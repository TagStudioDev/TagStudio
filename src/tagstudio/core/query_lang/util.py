# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import override


class ParsingError(BaseException):
    start: int
    end: int
    msg: str

    def __init__(self, start: int, end: int, msg: str = "Syntax Error") -> None:
        super().__init__()
        self.start = start
        self.end = end
        self.msg = msg

    @override
    def __str__(self) -> str:
        return f"Syntax Error {self.start}->{self.end}: {self.msg}"  # pragma: nocover

    @override
    def __repr__(self) -> str:
        return self.__str__()  # pragma: nocover
