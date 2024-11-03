from string import ascii_letters, digits

from ..qt_logger import logger


def is_valid_ini_key(key: str) -> bool:
    """Check if a given string is a valid INI key for QSettings.

    This function validates whether the provided key is suitable for use in an INI file
    managed by QSettings. Valid INI keys are those that are human-readable and do not
    require URL encoding when saved.

    A valid key can contain letters (both uppercase and lowercase), digits,
    and the characters '-', '_', and '.'.

    Args:
        key (str): The string to be checked for validity as an INI key.

    Returns:
        bool: True if the key is valid (i.e., human-readable and contains only allowed characters),
            False otherwise.

    Notes:
        - An empty string is considered invalid.
        - This function is designed to ensure that keys remain human-readable
          when stored in an INI file, preventing issues with URL encoding.
    """
    if not key:
        return False

    allowed_chars = ascii_letters + digits + "-_."

    return all(char in allowed_chars for char in key)


class IniKey(str):
    """A subclass of `str` that ensures the string is a valid INI key.

    A valid INI key can contain letters (both uppercase and lowercase), digits,
    and the characters `-`, `_`, and `.`.

    Args:
        key (str): INI key.
        forced (bool): If True, the key will be considered valid even if it
            contains invalid characters. Defaults to False.

    Raises:
        ValueError: If the key is invalid and forced is False.

    Notes:
        - An empty string is considered invalid.
        - This class is designed to ensure that keys remain human-readable
          when stored in an INI file, preventing issues with URL encoding.
    """

    def __new__(cls, key: str, forced: bool = False):
        if not is_valid_ini_key(key):
            if not forced:
                raise ValueError(f"Invalid INI key: {key}")
            else:
                logger.warning(f"Forced INI key: {key}")
        return super().__new__(cls, key)
