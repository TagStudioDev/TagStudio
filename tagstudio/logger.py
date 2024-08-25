import logging

from args import TagStudioArgs, parser

args = parser.parse_args(namespace=TagStudioArgs)

tag_studio_log = logging.getLogger(__name__)

if args.debug:
    tag_studio_log.setLevel(logging.DEBUG)
