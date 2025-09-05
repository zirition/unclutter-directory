import logging
import sys

logger = logging.getLogger("unclutter_directory")


def setup_logging(quiet: bool = False):
    """
    Configure global logging based on quiet flag.

    Args:
        quiet: If True, set level to ERROR; otherwise INFO
    """
    level = logging.ERROR if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger():
    return logger
