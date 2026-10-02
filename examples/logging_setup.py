"""Configure Python logging without claiming request-level instrumentation."""

import logging

from _common import make_client, run


async def console() -> None:
    """Configure application logging and inspect a credential-free client repr."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("fragment_examples")
    async with make_client() as client:
        logger.info("Client configuration: %r", client)
    logger.info("Client closed.")


async def library() -> None:
    """Set the library logger level without logging secrets or raw HTTP bodies."""
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("FragmentAPI").setLevel(logging.DEBUG)
    print("FragmentAPI logger configured.")
    print("Log output depends on instrumentation present in the installed version.")
    print("Do not log mnemonics, cookies, OAuth tokens, login codes, or signed BOCs.")


if __name__ == "__main__":
    run({"console": console, "library": library}, "console")