"""Load full-account sessions from files or Redis and close owned resources."""

from FragmentAPI import (
    CookieError,
    FileSessionStorage,
    FragmentClient,
    RedisSessionStorage,
)

from _common import run, setting


async def use_storage(storage: object) -> None:
    """Load an existing session without unexpectedly starting interactive login."""
    session_id = setting("FRAGMENT_SESSION_ID", "default")
    cookies = await storage.load(session_id)
    if not cookies:
        raise CookieError("No stored session. Run authentication.py first.")
    async with FragmentClient(
        cookies=cookies,
        session_storage=storage,
        session_id=session_id,
    ) as client:
        profile = await client.get_profile()
        print(f"Authenticated profile: {profile.name}")


async def files() -> None:
    """Use atomic JSON file storage."""
    storage = FileSessionStorage(setting("FRAGMENT_SESSION_DIR", ".fragment_sessions"))
    await use_storage(storage)


async def redis() -> None:
    """Use Redis and explicitly close its independent connection pool."""
    storage = RedisSessionStorage(
        redis_url=setting("REDIS_URL", "redis://localhost:6379/0"),
        ttl=3600,
    )
    try:
        await use_storage(storage)
    finally:
        await storage.aclose()


if __name__ == "__main__":
    run({"files": files, "redis": redis}, "files")