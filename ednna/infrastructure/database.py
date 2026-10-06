from __future__ import annotations

import mysql.connector
from mysql.connector import Error

from ednna.settings import DatabaseSettings


def build_mysql_config(settings: DatabaseSettings) -> dict[str, object]:
    return {
        "host": settings.host,
        "user": settings.user,
        "password": settings.password,
        "database": settings.database,
        "port": settings.port,
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
    }


def connect_mysql(settings: DatabaseSettings):
    try:
        return mysql.connector.connect(**build_mysql_config(settings))
    except Error:
        return None
