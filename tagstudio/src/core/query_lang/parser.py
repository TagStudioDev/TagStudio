from typing import Union

from src.core.query_lang.ast import AST, ANDList, Constraint, ORList, Property
from src.core.query_lang.tokenizer import ConstraintType, Token, Tokenizer, TokenType
from src.core.query_lang.util import ParsingError


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
        out = self.__or_list()
        if self.next_token.type != TokenType.EOF:
            raise ParsingError(self.next_token.start, self.next_token.end, "Syntax Error")
        return out

    def __and_list(self) -> ANDList:
        elements = [ self.__term() ]
        while self.next_token.type != TokenType.EOF and not self.__is_next_or():
            self.__skip_and()
            elements.append(self.__term())
        return ANDList(elements)
    
    def __skip_and(self) -> None:
        if self.__is_next_and():
            self.__eat(TokenType.ULITERAL)

            if self.__is_next_and():
                raise self.__syntax_error("Unexpected AND")
    
    def __is_next_and(self) -> bool:
        return self.next_token.type == TokenType.ULITERAL and self.next_token.value.upper() == "AND"
    
    def __or_list(self) -> ORList:
        terms = [ self.__and_list() ]

        while self.__is_next_or():
            self.__eat(TokenType.ULITERAL)
            terms.append(self.__and_list())

        return ORList(terms)

    def __is_next_or(self) -> bool:
        return self.next_token.type == TokenType.ULITERAL and self.next_token.value.upper() == "OR"
    
    def __term(self) -> Union["ORList", "Constraint"]:
        if self.next_token.type == TokenType.RBRACKETO:
            self.__eat(TokenType.RBRACKETO)
            out = self.__or_list()
            self.__eat(TokenType.RBRACKETC)
            return out
        else:
            return self.__constraint()
    
    def __constraint(self) -> Constraint:
        if self.next_token.type == TokenType.CONSTRAINTTYPE:
            self.last_constraint_type = self.__eat(TokenType.CONSTRAINTTYPE).value
        
        value = self.__literal()

        properties = []
        if self.next_token.type == TokenType.SBRACKETO:
            self.__eat(TokenType.SBRACKETO)
            properties.append(self.__property())
            
            while self.next_token.type == TokenType.COMMA:
                self.__eat(TokenType.COMMA)
                properties.append(self.__property())

            self.__eat(TokenType.SBRACKETC)

        return Constraint(self.last_constraint_type, value, properties)
    
    def __property(self) -> Property:
        key = self.__eat(TokenType.ULITERAL).value
        self.__eat(TokenType.EQUALS)
        value = self.__literal()
        return Property(key, value)
    
    def __literal(self) -> str:
        if self.next_token.type in [TokenType.QLITERAL, TokenType.ULITERAL]:
            return self.__eat(self.next_token.type).value
        raise self.__syntax_error()

    def __eat(self, type: TokenType) -> Token:
        if self.next_token.type != type:
            raise self.__syntax_error(f"expected {type} found {self.next_token.type}")
        out = self.next_token
        self.next_token = self.tokenizer.get_next_token()
        return out

    def __syntax_error(self, msg: str = "Syntax Error") -> ParsingError:
        return ParsingError(self.next_token.start, self.next_token.end, msg)

if __name__ == "__main__": #TODO remove
    print("")  # noqa: T201
    p = Parser("Mario AND Luigi tag:test[parent=Color,color=red] OR mediatype:test")
    print(p.parse())  # noqa: T201
