'''
Anonymous numbers methods - async and sync
'''

from __future__ import annotations

import html
from typing import TYPE_CHECKING

from FragmentAPI.exceptions import (
    AnonymousNumberError,
    FragmentAPIError,
    FragmentBaseError,
    UnexpectedError,
)
from FragmentAPI.types.constants import NUMBERS_PAGE
from FragmentAPI.types.results import LoginCodeResult, TerminateSessionsResult
from FragmentAPI.utils.html import parse_login_code

if TYPE_CHECKING:
    from FragmentAPI.async_client import AsyncFragmentClient
    from FragmentAPI.client import FragmentClient


def _strip_plus(number: str) -> str:
    return number.lstrip("+") if isinstance(number, str) else number


async def get_login_code(client: "AsyncFragmentClient", number: str) -> LoginCodeResult:
    '''Fetch the current pending login code for an anonymous number (async).'''
    try:
        clean = _strip_plus(number)
        result = await client.call(
            "updateLoginCodes",
            {"number": clean, "lt": "0", "from_app": "1"},
            page_url=NUMBERS_PAGE,
        )

        if result.get("html"):
            code, active_sessions = parse_login_code(result["html"])
        else:
            code, active_sessions = None, 0

        return LoginCodeResult(number=number, code=code, active_sessions=active_sessions)

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


def get_login_code_sync(client: "FragmentClient", number: str) -> LoginCodeResult:
    '''Fetch the current pending login code for an anonymous number (sync).'''
    try:
        clean = _strip_plus(number)
        result = client.call(
            "updateLoginCodes",
            {"number": clean, "lt": "0", "from_app": "1"},
            page_url=NUMBERS_PAGE,
        )

        if result.get("html"):
            code, active_sessions = parse_login_code(result["html"])
        else:
            code, active_sessions = None, 0

        return LoginCodeResult(number=number, code=code, active_sessions=active_sessions)

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def toggle_login_codes(client: "AsyncFragmentClient", number: str, can_receive: bool) -> None:
    '''Enable or disable login code delivery for an anonymous number (async).'''
    try:
        clean = _strip_plus(number)
        result = await client.call(
            "toggleLoginCodes",
            {"number": clean, "can_receive": 1 if can_receive else 0},
            page_url=NUMBERS_PAGE,
        )

        if result.get("error"):
            raise FragmentAPIError(html.unescape(result["error"]))

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


def toggle_login_codes_sync(client: "FragmentClient", number: str, can_receive: bool) -> None:
    '''Enable or disable login code delivery for an anonymous number (sync).'''
    try:
        clean = _strip_plus(number)
        result = client.call(
            "toggleLoginCodes",
            {"number": clean, "can_receive": 1 if can_receive else 0},
            page_url=NUMBERS_PAGE,
        )

        if result.get("error"):
            raise FragmentAPIError(html.unescape(result["error"]))

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def terminate_sessions(client: "AsyncFragmentClient", number: str) -> TerminateSessionsResult:
    '''Terminate all active Telegram sessions for an anonymous number (async).'''
    try:
        clean = _strip_plus(number)

        confirmation = await client.call(
            "terminatePhoneSessions",
            {"number": clean},
            page_url=NUMBERS_PAGE,
        )

        if confirmation.get("error"):
            raise AnonymousNumberError(
                AnonymousNumberError.TERMINATE_FAILED.format(
                    number=number, error=html.unescape(confirmation["error"])
                )
            )

        terminate_hash = confirmation.get("terminate_hash")
        if not terminate_hash:
            raise AnonymousNumberError(AnonymousNumberError.NOT_OWNED.format(number=number))

        result = await client.call(
            "terminatePhoneSessions",
            {"number": clean, "terminate_hash": terminate_hash},
            page_url=NUMBERS_PAGE,
        )

        if result.get("error"):
            raise AnonymousNumberError(
                AnonymousNumberError.TERMINATE_FAILED.format(
                    number=number, error=html.unescape(result["error"])
                )
            )

        return TerminateSessionsResult(number=number, message=result.get("msg"))

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


def terminate_sessions_sync(client: "FragmentClient", number: str) -> TerminateSessionsResult:
    '''Terminate all active Telegram sessions for an anonymous number (sync).'''
    try:
        clean = _strip_plus(number)

        confirmation = client.call(
            "terminatePhoneSessions",
            {"number": clean},
            page_url=NUMBERS_PAGE,
        )

        if confirmation.get("error"):
            raise AnonymousNumberError(
                AnonymousNumberError.TERMINATE_FAILED.format(
                    number=number, error=html.unescape(confirmation["error"])
                )
            )

        terminate_hash = confirmation.get("terminate_hash")
        if not terminate_hash:
            raise AnonymousNumberError(AnonymousNumberError.NOT_OWNED.format(number=number))

        result = client.call(
            "terminatePhoneSessions",
            {"number": clean, "terminate_hash": terminate_hash},
            page_url=NUMBERS_PAGE,
        )

        if result.get("error"):
            raise AnonymousNumberError(
                AnonymousNumberError.TERMINATE_FAILED.format(
                    number=number, error=html.unescape(result["error"])
                )
            )

        return TerminateSessionsResult(number=number, message=result.get("msg"))

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc