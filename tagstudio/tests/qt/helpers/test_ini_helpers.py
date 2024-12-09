import pytest
from src.qt.helpers.ini_helpers import IniKey, is_valid_ini_key


def test_is_valid_ini_key():
    valid_keys = {"valid_key", "Valid.key_2", "1valid_key", "valid-key", ".valid_key_3", "_valid"}
    invalid_keys = {"invalid key", ""}

    for key in valid_keys:
        assert is_valid_ini_key(key)

    for key in invalid_keys:
        assert not is_valid_ini_key(key)


class TestIniKey:
    @staticmethod
    def test___new__():
        assert IniKey("valid_key") == "valid_key"
        assert IniKey("Valid.key_2") == "Valid.key_2"

        invalid_keys = {"invalid key", ""}

        for key in invalid_keys:
            with pytest.raises(ValueError):
                IniKey(key)

        for key in invalid_keys:
            assert IniKey(key, forced=True) == key
