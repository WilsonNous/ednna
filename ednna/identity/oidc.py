from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient

from ednna.identity.principal import Principal


class AuthenticationError(PermissionError):
    pass


@dataclass(frozen=True)
class OIDCSettings:
    issuer: str
    audience: str
    jwks_url: str
    tenant_claim: str = "tid"
    user_claim: str = "oid"
    service_claim: str = "azp"
    roles_claim: str = "roles"
    permissions_claim: str = "scp"


class OIDCAuthenticator:
    """Validate an OIDC JWT and map trusted claims to an EDNNA Principal."""

    def __init__(
        self,
        settings: OIDCSettings,
        jwk_client: PyJWKClient | None = None,
    ) -> None:
        self._settings = settings
        self._jwk_client = jwk_client or PyJWKClient(settings.jwks_url)

    def authenticate(self, token: str) -> Principal:
        if not token.strip():
            raise AuthenticationError("Bearer token is required")

        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._settings.audience,
                issuer=self._settings.issuer,
                options={"require": ["exp", "iat"]},
            )
        except Exception as exc:
            raise AuthenticationError("Invalid authentication token") from exc

        user_id = self._claim_as_string(claims, self._settings.user_claim)
        tenant_id = self._claim_as_string(claims, self._settings.tenant_claim)
        if not user_id or not tenant_id:
            raise AuthenticationError("Required identity claims are missing")

        roles = self._claim_as_tuple(claims, self._settings.roles_claim)
        permissions = self._permissions(claims.get(self._settings.permissions_claim))
        service_id = self._claim_as_string(claims, self._settings.service_claim)

        return Principal(
            user_id=user_id,
            tenant_id=tenant_id,
            service_id=service_id,
            roles=roles,
            permissions=permissions,
        )

    @staticmethod
    def _claim_as_string(claims: dict[str, Any], name: str) -> str | None:
        value = claims.get(name)
        return str(value) if value is not None and str(value).strip() else None

    @staticmethod
    def _claim_as_tuple(claims: dict[str, Any], name: str) -> tuple[str, ...]:
        value = claims.get(name)
        if value is None:
            return ()
        if isinstance(value, list):
            return tuple(str(item) for item in value)
        return tuple(str(value).split())

    @staticmethod
    def _permissions(value: Any) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, list):
            return tuple(str(item) for item in value)
        return tuple(part for part in str(value).split() if part)
