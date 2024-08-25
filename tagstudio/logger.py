import logging
from args import TagStudioArgs, parser

args = parser.parse_args(namespace=TagStudioArgs)

formatter = logging.Formatter("[%(name)s]: [%(levelname)s] => %(message)s") # TODO: maybe include timestamps?

tag_studio_log = logging.getLogger(__name__)

file_handler = logging.FileHandler("tagstudio.log", mode="w")
stream_handler = logging.StreamHandler()

file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

tag_studio_log.addHandler(file_handler)
# tag_studio_log.addHandler(stream_handler)  # print logs.

if args.debug:
    file_handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.DEBUG)
    tag_studio_log.setLevel(logging.DEBUG)
else:
    file_handler.setLevel(logging.INFO)
    stream_handler.setLevel(logging.INFO)
    tag_studio_log.setLevel(logging.INFO)

def get_logger(name: str):
    """
    Convenience function to get a logger with the given name, as a child of the tag_studio_log logger.
    
    Parameters
    -----------
    :param:`name`: :class:`str`
        the name for the logger
    
    Returns
    -------
    :class:`_type_`
        a logger
    """
    return tag_studio_log.getChild(name)