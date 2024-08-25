import logging

from args import TagStudioArgs, parser

args = parser.parse_args(namespace=TagStudioArgs)

logging.basicConfig(format="%(message)s", level=logging.INFO)

tag_studio_log = logging.getLogger(__name__)
tag_studio_log.addHandler(logging.FileHandler("tagstudio.log"))
tag_studio_log.addHandler(logging.StreamHandler())  # print logs.

if args.debug:
    tag_studio_log.setLevel(logging.DEBUG)


def get_logger(name: str):
    return tag_studio_log.getChild(name)
