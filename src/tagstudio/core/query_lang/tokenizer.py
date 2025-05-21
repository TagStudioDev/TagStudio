from enum import Enum
from typing import Any

from tagstudio.core.query_lang.ast import ConstraintType
from tagstudio.core.query_lang.util import ParsingError


class TokenType(Enum):
    EOF = -1
    QLITERAL = 0  # Quoted Literal
    ULITERAL = 1  # Unquoted Literal (does not contain ":", " ", "[", "]", "(", ")", "=", ",")
    RBRACKETO = 2  # Round Bracket Open
    RBRACKETC = 3  # Round Bracket Close
    SBRACKETO = 4  # Square Bracket Open
    SBRACKETC = 5  # Square Bracket Close
    CONSTRAINTTYPE = 6
    COLON = 10
    COMMA = 11
    EQUALS = 12


class Token:
    type: TokenType
    value: Any

    start: int
    end: int

    def __init__(self, type: TokenType, value: Any, start: int, end: int) -> None:
        self.type = type
        self.value = value
        self.start = start
        self.end = end

    @staticmethod
    def from_type(type: TokenType, pos: int) -> "Token":
        return Token(type, None, pos, pos)

    @staticmethod
    def EOF(pos: int) -> "Token":  # noqa: N802
        return Token.from_type(TokenType.EOF, pos)

    def __str__(self) -> str:
        return f"Token({self.type}, {self.value}, {self.start}, {self.end})"  # pragma: nocover

    def __repr__(self) -> str:
        return self.__str__()  # pragma: nocover


class Tokenizer:
    text: str
    pos: int
    current_char: str | None

    ESCAPABLE_CHARS = ["\\", '"', '"']
    NOT_IN_ULITERAL = [":", " ", "[", "]", "(", ")", "=", ","]

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if len(text) > 0 else None

    def get_next_token(self) -> Token:
        self.__skip_whitespace()
        if self.current_char is None:
            return Token.EOF(self.pos)

        if self.current_char in ("'", '"'):
            return self.__quoted_string()
        elif self.current_char == "(":
            self.__advance()
            return Token.from_type(TokenType.RBRACKETO, self.pos - 1)
        elif self.current_char == ")":
            self.__advance()
            return Token.from_type(TokenType.RBRACKETC, self.pos - 1)
        elif self.current_char == "[":
            self.__advance()
            return Token.from_type(TokenType.SBRACKETO, self.pos - 1)
        elif self.current_char == "]":
            self.__advance()
            return Token.from_type(TokenType.SBRACKETC, self.pos - 1)
        elif self.current_char == ",":
            self.__advance()
            return Token.from_type(TokenType.COMMA, self.pos - 1)
        elif self.current_char == "=":
            self.__advance()
            return Token.from_type(TokenType.EQUALS, self.pos - 1)
        else:
            return self.__unquoted_string_or_constraint_type()

    def __unquoted_string_or_constraint_type(self) -> Token:
        out = ""

        start = self.pos

        while self.current_char is not None:
            if self.current_char in self.NOT_IN_ULITERAL:
                if self.current_char == ":":
                    if len(out) == 0:
                        raise ParsingError(self.pos, self.pos)
                    constraint_type = ConstraintType.from_string(out)
                    if constraint_type is not None:
                        self.__advance()
                        return Token(TokenType.CONSTRAINTTYPE, constraint_type, start, self.pos)
                else:
                    break

            out += self.current_char
            self.__advance()

        end = self.pos - 1
        return Token(TokenType.ULITERAL, out, start, end)

    def __quoted_string(self) -> Token:
        start = self.pos
        quote = self.current_char
        self.__advance()
        escape = False
        out = ""

        while escape or self.current_char != quote:
            if self.current_char is None:
                raise ParsingError(start, self.pos, "Unterminated quoted string")
            if escape:
                escape = False
                if self.current_char not in Tokenizer.ESCAPABLE_CHARS:
                    out += "\\"
                else:
                    out += self.current_char
                    self.__advance()
                    continue
            if self.current_char == "\\":
                escape = True
            else:
                out += self.current_char
            self.__advance()
        end = self.pos
        self.__advance()
        return Token(TokenType.QLITERAL, out, start, end)

    def __advance(self) -> None:
        if self.pos < len(self.text) - 1:
            self.pos += 1
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def __skip_whitespace(self) -> None:
        while self.current_char is not None and self.current_char.isspace():
            self.__advance()
