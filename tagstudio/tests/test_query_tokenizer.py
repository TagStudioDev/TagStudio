import pytest
from src.core.query_tokenizer import QueryTokenizer, Token, TokenType


@pytest.mark.parametrize("keyword", QueryTokenizer.keywords)
def test_parsing_keywords(keyword: str):
    query_parser = QueryTokenizer(keyword)
    token = query_parser.next_token()

    assert token.type == TokenType.KEYWORD
    assert token.data == keyword


@pytest.mark.parametrize(
    ["source", "expected_token_type"],
    [(":", TokenType.COLON), ("(", TokenType.LEFT_PAREN), (")", TokenType.RIGHT_PAREN)],
)
def test_parsing_single_character_tokens(source: str, expected_token_type: TokenType):
    query_parser = QueryTokenizer(source)
    token = query_parser.next_token()
    assert isinstance(token, Token)
    assert token.type == expected_token_type
    assert token.data is None


@pytest.mark.parametrize(
    "source",
    ["mediatype:photoshop", 'mediatype:"photoshop"'],
)
def test_parse_single_expr_query(source: str):
    query_parser = QueryTokenizer(source)
    tokens: list[Token] = []

    i = 0
    while i < 3:
        token = query_parser.next_token()

        assert isinstance(token, Token)

        tokens.append(token)
        i += 1

    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[1].type == TokenType.COLON
    assert tokens[2].type == TokenType.IDENTIFIER


@pytest.mark.parametrize("source", ["mediatype:photoshop AND path:books"])
def test_parse_multi_expr_query(source: str):
    query_tokenizer: QueryTokenizer = QueryTokenizer(source)

    assert query_tokenizer.next_token().type == TokenType.IDENTIFIER
    assert query_tokenizer.next_token().type == TokenType.COLON
    assert query_tokenizer.next_token().type == TokenType.IDENTIFIER
    assert query_tokenizer.next_token().type == TokenType.KEYWORD
    assert query_tokenizer.next_token().type == TokenType.IDENTIFIER
    assert query_tokenizer.next_token().type == TokenType.COLON
    assert query_tokenizer.next_token().type == TokenType.IDENTIFIER
