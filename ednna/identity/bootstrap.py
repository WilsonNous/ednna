from __future__ import annotations

from ednna.settings import OIDCAppSettings

from .oidc import OIDCAuthenticator, OIDCSettings


def build_oidc_authenticator() -> OIDCAuthenticator:
    settings = OIDCAppSettings.from_env()
    return OIDCAuthenticator(
        OIDCSettings(
            issuer=settings.issuer,
            audience=settings.audience,
            jwks_url=settings.jwks_url,
            tenant_claim=settings.tenant_claim,
            user_claim=settings.user_claim,
            service_claim=settings.service_claim,
            roles_claim=settings.roles_claim,
            permissions_claim=settings.permissions_claim,
        )
    )
