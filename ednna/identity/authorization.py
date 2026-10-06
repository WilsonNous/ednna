from __future__ import annotations

from .principal import Principal


class AuthorizationDeniedError(PermissionError):
    pass


class AuthorizationService:
    """Default-deny permission checks for EDNNA capabilities."""

    def require(self, principal: Principal, permission: str) -> None:
        if permission not in principal.permissions:
            raise AuthorizationDeniedError(
                f"Principal '{principal.user_id}' lacks permission '{permission}'"
            )

    def require_query(self, principal: Principal, capability: str) -> None:
        self.require(principal, f"{capability}:query")

    def require_action(self, principal: Principal, capability: str) -> None:
        self.require(principal, f"{capability}:action")
