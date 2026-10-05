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
