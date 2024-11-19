from enum import Enum


class TokenType(Enum):
    KEYWORD = 1
    LITERAL = 2
    QUERY = 3
    ILLEGAL = 4
    COLON = 5
    LEFT_PAREN = 6
    RIGHT_PAREN = 7
    END_OF_INPUT = 8


class Token:
    def __init__(self, data: str | None, tok_type: TokenType):
        self.data: str | None = (
            data  # this doesnt need to have data for token types where it is obvious (i.e. COLON)
        )
        self.type: TokenType = tok_type


class QueryTokenizer:
    def __init__(self, query: str):
        self.query: str = query
        self.current_pos = 0
        self.next_pos = 0
        self.current_character = ""
        self.next_character = ""
        self.read_character()

    keywords = ["AND", "OR", "NOT"]

    queries = ["mediatype", "filetype", "path", "tag"]

    @staticmethod
    def is_character(character: str) -> bool:
        return (
            64 < ord(character) < 91
            or 96 < ord(character) < 123
            or ord(character) == 95
            or character == '"'
            or character == "/"
            or character == "*"
        )  # is in ascii range a-z or A-Z

    @staticmethod
    def is_numeric(character: str) -> bool:
        return 47 < ord(character) < 58

    def skip_whitespace(self) -> None:
        while self.current_character == " ":
            self.read_character()

    def read_character(self) -> None:
        self.current_pos = self.next_pos
        self.next_pos += 1

        if self.current_pos < len(self.query):
            self.current_character = self.query[self.current_pos]
        else:
            self.current_character = "\0"

        if self.next_pos < len(self.query):
            self.next_character = self.query[self.next_pos]
        else:
            self.next_character = "\0"

    def next_identifier(self) -> Token | None:
        begin_pos = self.current_pos
        inside_literal = False
        while (
            self.is_character(self.current_character)
            or self.is_numeric(self.current_character)
            or inside_literal
        ):
            if self.current_character == '"' or self.current_character == "'":
                inside_literal = not inside_literal
            self.read_character()

        return Token((self.query[begin_pos : self.current_pos]).strip('"'), TokenType.LITERAL)

    def next_token(self) -> Token:
        token: Token | None = None

        self.skip_whitespace()
        if self.current_character == ":":
            token = Token(None, TokenType.COLON)
        elif self.current_character == "(":
            token = Token(None, TokenType.LEFT_PAREN)
        elif self.current_character == ")":
            token = Token(None, TokenType.RIGHT_PAREN)
        elif self.current_character == "\0":
            token = Token(None, TokenType.END_OF_INPUT)
        else:
            if self.is_character(self.current_character):
                ident = self.next_identifier()
                if ident.data.upper() in self.keywords:
                    ident.type = TokenType.KEYWORD
                    return ident
                elif ident.data.lower() in self.queries:
                    ident.type = TokenType.QUERY
                    return ident
                else:
                    return ident
        self.read_character()
        return token

    def tokenize_all(self) -> list[Token]:
        tokens: list[Token] = []
        while (token := self.next_token()).type not in [TokenType.END_OF_INPUT, TokenType.ILLEGAL]:
            tokens.append(token)
        return tokens
