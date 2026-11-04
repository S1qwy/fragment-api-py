"""Inspect revenue links or explicitly review a server withdrawal challenge."""
from _common import make_client, required, require_execution, run


async def inspect() -> None:
    async with make_client(account=True) as client:
        info = await client.inspect_withdrawal(required("FRAGMENT_WITHDRAWAL_URL"))
        print(f"Kind={info.kind}; mode={info.mode}; KYC required={info.kyc_required}")
        print(f"Amount={info.amount}; currency={info.currency}; destination={info.destination}")


async def withdraw() -> None:
    require_execution()
    async with make_client(account=True, mode="prepare") as client:
        request = await client.prepare_withdrawal(required("FRAGMENT_WITHDRAWAL_URL"))
        print(f"Destination: {request.destination}")
        print(request.confirm_message or "Fragment returned no confirmation challenge; inspect the original withdrawal status.")
        if not request.confirmation_required:
            return
        if input("Review the server message. Type CONFIRM to submit: ") != "CONFIRM":
            return
        result = await client.confirm_withdrawal(request)
        print(f"Server accepted={result.ok}; mode={result.mode}")


if __name__ == "__main__":
    run({"inspect": inspect, "withdraw": withdraw}, "inspect")
