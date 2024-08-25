import logging

from args import TagStudioArgs, parser

args = parser.parse_args(namespace=TagStudioArgs)

logger = logging.getLogger(__name__)

if args.debug:
    logger.setLevel(logging.DEBUG)
