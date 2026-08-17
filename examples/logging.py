"""
Logging configuration examples.

Demonstrates how to enable and configure the FragmentAPI logger
for debugging requests and monitoring library behavior.
"""

import asyncio
import logging
from FragmentAPI import FragmentClient


async def basic_debug_logging():
    """Enable DEBUG-level logging for all FragmentAPI operations."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    logger = logging.getLogger("FragmentAPI")
    logger.setLevel(logging.DEBUG)

    client = FragmentClient(
        cookies="stel_ssid=abc; stel_dt=-180; stel_token=xyz; stel_ton_token=tok",
    )
    print(f"Client: {client}")


async def info_level_logging():
    """Enable INFO-level logging for production monitoring."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    logging.getLogger("FragmentAPI").setLevel(logging.INFO)

    client = FragmentClient(
        cookies="stel_ssid=abc; stel_dt=-180; stel_token=xyz; stel_ton_token=tok",
    )
    print(f"Client ready: {client}")


async def file_logging():
    """Log FragmentAPI operations to a file."""
    file_handler = logging.FileHandler("fragment_api.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    )

    logger = logging.getLogger("FragmentAPI")
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

    client = FragmentClient(
        cookies="stel_ssid=abc; stel_dt=-180; stel_token=xyz; stel_ton_token=tok",
    )
    print(f"Logging to fragment_api.log: {client}")


async def selective_logging():
    """Only log warnings and errors from FragmentAPI."""
    logging.basicConfig(level=logging.WARNING)

    logging.getLogger("FragmentAPI").setLevel(logging.WARNING)

    client = FragmentClient(
        cookies="stel_ssid=abc; stel_dt=-180; stel_token=xyz; stel_ton_token=tok",
    )
    print("Only warnings and errors will be logged")


async def suppress_logging():
    """Completely suppress FragmentAPI logging."""
    logging.getLogger("FragmentAPI").setLevel(logging.CRITICAL + 1)

    client = FragmentClient(
        cookies="stel_ssid=abc; stel_dt=-180; stel_token=xyz; stel_ton_token=tok",
    )
    print("All FragmentAPI logging suppressed")


if __name__ == "__main__":
    asyncio.run(basic_debug_logging())