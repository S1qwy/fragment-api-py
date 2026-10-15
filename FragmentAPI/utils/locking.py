"""Cooperative wallet locks shared by local clients and processes."""

from __future__ import annotations

import asyncio
import errno
import hashlib
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator


@asynccontextmanager
async def file_wallet_lock(address: str) -> AsyncIterator[None]:
    """Lock a canonical payer address on this host; release on process exit.

    Multi-host deployments must inject a shared lock factory and payment store.
    Lock files must not be removed: another process may hold their inode open.
    """
    directory = Path.home() / ".fragment-api" / "wallet-locks"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / (hashlib.sha256(address.encode()).hexdigest() + ".lock")
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    acquired = False
    try:
        if os.name == "nt":
            import msvcrt

            # Windows byte-range locks need a byte even on a newly created file.
            if os.fstat(descriptor).st_size == 0:
                os.write(descriptor, b"0")
        while not acquired:
            try:
                if os.name == "nt":
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    raise
                await asyncio.sleep(0.05)
        yield
    finally:
        if acquired:
            if os.name == "nt":
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
