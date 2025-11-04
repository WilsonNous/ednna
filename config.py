# config.py
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),  # Default local
    "user": os.getenv("DB_USER", "noust785_edi_admin"),
    "password": os.getenv("DB_PASSWORD", "N3tunn@21#"),
    "database": os.getenv("DB_NAME", "noust785_edi_ops"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci"
}
