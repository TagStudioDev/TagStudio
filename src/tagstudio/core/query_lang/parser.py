# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from tagstudio.core.query_lang.ast import (
    AST,
    ANDList,
    Boolean,
    Constraint,
    ConstraintType,
    Not,
    ORList,
    Property,
)
from tagstudio.core.query_lang.tokenizer import Token, Tokenizer, TokenType
from tagstudio.core.query_lang.util import ParsingError


class Parser:
    text: str
    tokenizer: Tokenizer
    next_token: Token

    last_constraint_type: ConstraintType = ConstraintType.Tag

    def __init__(self, text: str) -> None:
        self.text = text
        self.tokenizer = Tokenizer(self.text)
        self.next_token = self.tokenizer.get_next_token()

    def parse(self) -> AST:
        if self.next_token.type == TokenType.EOF:
            return ORList([])
        out = self.__or_list()
        if self.next_token.type != TokenType.EOF:  # pyright: ignore[reportUnnecessaryComparison]
            raise ParsingError(self.next_token.start, self.next_token.end, "Syntax Error")
        return out

    def __or_list(self) -> AST:
        terms = [self.__and_list()]

        while self.__is_next_or():
            self.__eat(TokenType.ULITERAL)
            terms.append(self.__and_list())

        return ORList(terms) if len(terms) > 1 else terms[0]

    def __is_next_or(self) -> bool:
        return self.next_token.type == TokenType.ULITERAL and self.next_token.value.upper() == "OR"  # pyright: ignore

    def __and_list(self) -> AST:
        elements = [self.__term()]
        while (
            self.next_token.type
            in [
                TokenType.QLITERAL,
                TokenType.ULITERAL,
                TokenType.CONSTRAINTTYPE,
                TokenType.RBRACKETO,
            ]
            and not self.__is_next_or()
        ):
            self.__skip_and()
            elements.append(self.__term())
        return ANDList(elements) if len(elements) > 1 else elements[0]

    def __skip_and(self) -> None:
        if self.__is_next_and():
            self.__eat(TokenType.ULITERAL)

            if self.__is_next_and():
                raise self.__syntax_error("Unexpected AND")

    def __is_next_and(self) -> bool:
        return self.next_token.type == TokenType.ULITERAL and self.next_token.value.upper() == "AND"  # pyright: ignore

    def __term(self) -> AST:
        if self.__is_next_not():
            self.__eat(TokenType.ULITERAL)
            term = self.__term()
            if isinstance(term, Not):  # instead of Not(Not(child)) return child
                return term.child
            return Not(term)
        if self.__is_next_true():
            self.__eat(TokenType.ULITERAL)
            return Boolean(value = True)
        if self.__is_next_false():
            self.__eat(TokenType.ULITERAL)
            return Boolean(value = False)
        if self.next_token.type == TokenType.RBRACKETO:
            self.__eat(TokenType.RBRACKETO)
            out = self.__or_list()
            self.__eat(TokenType.RBRACKETC)
            return out
        else:
            return self.__constraint()

    def __is_next_not(self) -> bool:
        return self.next_token.type == TokenType.ULITERAL and self.next_token.value.upper() == "NOT"  # pyright: ignore

    def __is_next_true(self) -> bool:
        return (
            self.next_token.type == TokenType.ULITERAL
            and self.next_token.value.upper() == "TRUE"  # pyright: ignore
        )

    def __is_next_false(self) -> bool:
        return (
            self.next_token.type == TokenType.ULITERAL
            and self.next_token.value.upper() == "TRUE"  # pyright: ignore
        )

    def __constraint(self) -> Constraint:
        if self.next_token.type == TokenType.CONSTRAINTTYPE:
            constraint = self.__eat(TokenType.CONSTRAINTTYPE).value
            if not isinstance(constraint, ConstraintType):
                raise self.__syntax_error()
            self.last_constraint_type = constraint

        value = self.__literal()

        properties = []
        if self.next_token.type == TokenType.SBRACKETO:
            self.__eat(TokenType.SBRACKETO)
            properties.append(self.__property())

            while self.next_token.type == TokenType.COMMA:  # pyright: ignore[reportUnnecessaryComparison]
                self.__eat(TokenType.COMMA)
                properties.append(self.__property())

            self.__eat(TokenType.SBRACKETC)

        return Constraint(self.last_constraint_type, value, properties)

    def __property(self) -> Property:
        key = self.__eat(TokenType.ULITERAL).value
        self.__eat(TokenType.EQUALS)
        value = self.__literal()
        if not isinstance(key, str):
            raise self.__syntax_error()
        return Property(key, value)

    def __literal(self) -> str:
        if self.next_token.type in [TokenType.QLITERAL, TokenType.ULITERAL]:
            literal = self.__eat(self.next_token.type).value
            if not isinstance(literal, str):
                raise self.__syntax_error()
            return literal
        raise self.__syntax_error()

    def __eat(self, type: TokenType) -> Token:
        if self.next_token.type != type:
            raise self.__syntax_error(f"expected {type} found {self.next_token.type}")
        out = self.next_token
        self.next_token = self.tokenizer.get_next_token()
        return out

    def __syntax_error(self, msg: str = "Syntax Error") -> ParsingError:
        return ParsingError(self.next_token.start, self.next_token.end, msg)
