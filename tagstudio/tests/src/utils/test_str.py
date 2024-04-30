import unittest

from parameterized import parameterized

from src.core.utils.str import strip_punctuation


class StrTest(unittest.TestCase):
    @parameterized.expand([
        ('{[(parenthesis)]}', 'parenthesis'),
        ('‘“`"\'quotes\'"`”’', 'quotes'),
        ('_- 　spacers', 'spacers'),
        ('{}[]()\'"`‘’“”- 　', '')
    ])
    def test_strip_punctuation(self, text, expected_output):
        self.assertEqual(strip_punctuation(text), expected_output)
