"""Validation, restricted capabilities, and non-replaying payment error handling."""

from FragmentAPI import (
    BroadcastUncertainError,
    ConfigurationError,
    FragmentClient,
    FragmentError,
    VerificationError,
    WalletError,
)

from _common import make_client, required, run, show_result


async def validation() -> None:
    """Demonstrate validation failures before authentication or HTTP requests."""
    async with FragmentClient() as client:
        checks = [
            ("Boolean quantity", lambda: client.purchase_stars("example", True)),
            ("Invalid duration", lambda: client.purchase_premium("example", 5)),
            ("Invalid package", lambda: client.giveaway_stars("example", 1, 501)),
        ]
        for label, operation in checks:
            try:
                await operation()
            except ConfigurationError as exc:
                print(f"{label}: {exc}")


async def restrictions() -> None:
    """Show that restricted wallet-auth sessions cannot read account state."""
    async with FragmentClient() as client:
        try:
            await client.get_sessions()
        except ConfigurationError as exc:
            print(exc)


async def purchase() -> None:
    """Handle an actual purchase once, without automatically retrying it."""
    async with make_client(mode="pay") as client:
        try:
            result = await client.purchase_stars(required("FRAGMENT_TARGET"), 100)
        except BroadcastUncertainError:
            print("Unknown broadcast outcome. Stop and reconcile before retrying.")
        except VerificationError:
            print("Fragment requires verification for this operation.")
        except WalletError as exc:
            print(f"Wallet preflight failed: {exc}")
        except FragmentError as exc:
            print(f"Operation failed: {type(exc).__name__}: {exc}")
        else:
            show_result(result)


if __name__ == "__main__":
    run(
        {"validation": validation, "restrictions": restrictions, "purchase": purchase},
        "validation",
    )