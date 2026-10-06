from __future__ import annotations

from typing import Protocol


class DuplicateActionError(RuntimeError):
    pass


class IdempotencyStore(Protocol):
    def reserve(self, key: str) -> None:
        ...


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._keys: set[str] = set()

    def reserve(self, key: str) -> None:
        if key in self._keys:
            raise DuplicateActionError(f"Duplicate action blocked for idempotency key '{key}'")
        self._keys.add(key)
