import pytest

from src.core.utils.str import strip_punctuation

@pytest.mark.parametrize("text, expected", [
    ('{[(parenthesis)]}', 'parenthesis'),
    ('‘“`"\'quotes\'"`”’', 'quotes'),
    ('_- 　spacers', 'spacers'),
    ('{}[]()\'"`‘’“”- 　', '')
])
def test_strip_punctuation(text, expected):
    assert strip_punctuation(text) == expected
