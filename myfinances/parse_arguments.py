import sys
from argparse import ArgumentParser, Namespace

from loguru import logger as log


def get_parsed_arguments() -> Namespace:
    args: Namespace = parse_arguments()
    set_logging(args)
    return args


def parse_arguments() -> Namespace:
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument(
        '--verbose',
        action='store_const',
        dest='log_level',
        const='DEBUG',
        default='INFO',
    )
    parser.add_argument(
        '-c',
        '--config',
        required=True,
        type=str,
    )
    parser.add_argument(
        '-o',
        '--output',
        required=False,
        type=str,
    )
    args: Namespace = parser.parse_args()
    return args


def set_logging(args: Namespace) -> None:
    log.remove()
    log.add(sys.stderr, level=args.log_level)
