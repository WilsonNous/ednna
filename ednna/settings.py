from __future__ import annotations

import os
from dataclasses import dataclass


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Required environment variable is not configured: {name}")
    return value


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    user: str
    password: str
    database: str
    port: int = 3306

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        return cls(
            host=require_env("DB_HOST"),
            user=require_env("DB_USER"),
            password=require_env("DB_PASSWORD"),
            database=require_env("DB_NAME"),
            port=int(os.getenv("DB_PORT", "3306")),
        )


@dataclass(frozen=True)
class SecuritySettings:
    secret_key: str
    admin_password: str

    @classmethod
    def from_env(cls) -> "SecuritySettings":
        return cls(
            secret_key=require_env("SECRET_KEY"),
            admin_password=require_env("ADMIN_PASSWORD"),
        )


@dataclass(frozen=True)
class AppSettings:
    database: DatabaseSettings
    security: SecuritySettings

    @classmethod
    def from_env(cls) -> "AppSettings":
        return cls(
            database=DatabaseSettings.from_env(),
            security=SecuritySettings.from_env(),
        )


@dataclass(frozen=True)
class OIDCAppSettings:
    issuer: str
    audience: str
    jwks_url: str
    tenant_claim: str = "tid"
    user_claim: str = "oid"
    service_claim: str = "azp"
    roles_claim: str = "roles"
    permissions_claim: str = "scp"

    @classmethod
    def from_env(cls) -> "OIDCAppSettings":
        return cls(
            issuer=require_env("OIDC_ISSUER"),
            audience=require_env("OIDC_AUDIENCE"),
            jwks_url=require_env("OIDC_JWKS_URL"),
            tenant_claim=os.getenv("OIDC_TENANT_CLAIM", "tid"),
            user_claim=os.getenv("OIDC_USER_CLAIM", "oid"),
            service_claim=os.getenv("OIDC_SERVICE_CLAIM", "azp"),
            roles_claim=os.getenv("OIDC_ROLES_CLAIM", "roles"),
            permissions_claim=os.getenv("OIDC_PERMISSIONS_CLAIM", "scp"),
        )
