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

    assert tokens[0].type == TokenType.QUERY
    assert tokens[1].type == TokenType.COLON
    assert tokens[2].type == TokenType.LITERAL


@pytest.mark.parametrize(
    ["source", "expected_tokens"],
    [
        (
            "mediatype:photoshop AND path:books",
            [
                Token("mediatype", TokenType.QUERY),
                Token(None, TokenType.COLON),
                Token("photoshop", TokenType.LITERAL),
                Token("AND", TokenType.KEYWORD),
                Token("path", TokenType.QUERY),
                Token(None, TokenType.COLON),
                Token("books", TokenType.LITERAL),
            ],
        ),
        (
            'mediatype:"affinity photo" AND (tag:one OR tag:"this is another tag")',
            [
                Token("mediatype", TokenType.QUERY),
                Token(None, TokenType.COLON),
                Token("affinity photo", TokenType.LITERAL),
                Token("AND", TokenType.KEYWORD),
                Token(None, TokenType.LEFT_PAREN),
                Token("tag", TokenType.QUERY),
                Token(None, TokenType.COLON),
                Token("one", TokenType.LITERAL),
                Token("OR", TokenType.KEYWORD),
                Token("tag", TokenType.QUERY),
                Token(None, TokenType.COLON),
                Token("this is another tag", TokenType.LITERAL),
            ],
        ),
    ],
)
def test_parse_multi_expr_query(source: str, expected_tokens: list[Token]):
    query_tokenizer: QueryTokenizer = QueryTokenizer(source)
    for expected_token in expected_tokens:
        actual_token = query_tokenizer.next_token()
        assert expected_token.type == actual_token.type
        assert expected_token.data == actual_token.data
