from __future__ import annotations


CONTRACT_VERSION = "1"
CONTRACT_VERSION_HEADER = "X-Intelligence-Contract-Version"


class UnsupportedContractVersionError(RuntimeError):
    pass


def validate_contract_version(value: str | None) -> None:
    if value is None or not str(value).strip():
        return

    if str(value).strip() != CONTRACT_VERSION:
        raise UnsupportedContractVersionError(
            f"Unsupported intelligence contract version '{value}'"
        )
