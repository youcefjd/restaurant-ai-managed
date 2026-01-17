"""Logging configuration for the Restaurant Reservation System."""

import logging
import sys


def setup_logging(name: str) -> logging.Logger:
    """
    Set up logging for the application.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)
        # Prevent propagation to root logger to avoid duplicate log messages
        logger.propagate = False

    return logger
