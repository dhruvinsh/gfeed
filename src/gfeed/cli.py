import argparse
import asyncio
import sys

from loguru import logger

from gfeed.fetch import main


def cli():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--osmos", action="store_true", help="Export github star repo(s) for osmosfeed."
    )
    group.add_argument(
        "--opml",
        action="store_true",
        help="Export github star repo(s) for RSS application as opml file.",
    )
    parser.add_argument(
        "--debug", action="store_true", default=False, help="More verbose output."
    )
    def positive_float(value):
        try:
            fvalue = float(value)
            if fvalue <= 0:
                raise argparse.ArgumentTypeError(
                    f"Invalid rate limit: {value}. Must be a positive number."
                )
            return fvalue
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Invalid rate limit: {value}. Must be a positive number."
            )

    parser.add_argument(
        "--rate-limit",
        type=positive_float,
        default=1.0,
        help="Set the rate limit for requests in requests per second (e.g., 0.5 for 1 request every 2 seconds).",
    )

    args = parser.parse_args()

    logger.remove()
    if args.debug:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")

    asyncio.run(main(args.osmos, args.opml, args.rate_limit))
