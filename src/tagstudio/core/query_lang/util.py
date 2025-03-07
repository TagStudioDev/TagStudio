class ParsingError(BaseException):
    start: int
    end: int
    msg: str

    def __init__(self, start: int, end: int, msg: str = "Syntax Error") -> None:
        self.start = start
        self.end = end
        self.msg = msg

    def __str__(self) -> str:
        return f"Syntax Error {self.start}->{self.end}: {self.msg}"  # pragma: nocover

    def __repr__(self) -> str:
        return self.__str__()  # pragma: nocover
