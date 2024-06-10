import logging
from typing import Final

MAIN_LOGGER_NAME: Final[str] = "tag_studio"

_root_logger = logging.getLogger()
_main_logger = _root_logger.getChild(MAIN_LOGGER_NAME)


def setup_logging() -> None:
    # TODO: https://github.com/TagStudioDev/TagStudio/pull/235#discussion_r1628613369
    # TODO: https://github.com/TagStudioDev/TagStudio/pull/235#issuecomment-2156582433
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s: %(message)s", level=logging.DEBUG
    )


def get_logger(name: str) -> logging.Logger:
    return _main_logger.getChild(name)
