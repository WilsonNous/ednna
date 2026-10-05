import os


def require_env(name: str) -> str:
    """Return a required environment variable or fail fast during startup."""
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Required environment variable is not configured: {name}")
    return value


DB_CONFIG = {
    "host": require_env("DB_HOST"),
    "user": require_env("DB_USER"),
    "password": require_env("DB_PASSWORD"),
    "database": require_env("DB_NAME"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
}
