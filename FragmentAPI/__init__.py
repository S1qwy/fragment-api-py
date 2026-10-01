"""Async Fragment marketplace and Telegram service client."""

import logging

from FragmentAPI.client import FragmentClient
from FragmentAPI.exceptions import *
from FragmentAPI.exceptions import __all__ as _exceptions
from FragmentAPI.storage.base import SessionStorage
from FragmentAPI.storage.file import FileSessionStorage
from FragmentAPI.storage.redis import RedisSessionStorage
from FragmentAPI.types.models import *
from FragmentAPI.types.models import __all__ as _models

logging.getLogger("FragmentAPI").addHandler(logging.NullHandler())

__version__ = "13.0.0"
__author__ = "S1qwy"
__email__ = "S1qwy@internet.ru"

__all__ = [
    "__version__",
    "FragmentClient",
    "SessionStorage",
    "FileSessionStorage",
    "RedisSessionStorage",
    *_exceptions,
    *_models,
]