"""Compatibility configuration for the legacy Flask application.

New EDNNA code should import from ednna.settings directly.
"""

from ednna.infrastructure.database import build_mysql_config
from ednna.settings import DatabaseSettings, require_env


DB_CONFIG = build_mysql_config(DatabaseSettings.from_env())
