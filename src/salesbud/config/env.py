"""
Environment configuration and constants
"""

import os
from pathlib import Path
from typing import Optional


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    return os.environ.get(key, default)


def get_required_env(key: str) -> str:
    """Get required environment variable or raise error."""
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


class LinkedIn:
    SESSION_COOKIE = "LINKEDIN_SESSION_COOKIE"
    EMAIL = "LINKEDIN_EMAIL"
    PASSWORD = "LINKEDIN_PASSWORD"

    @classmethod
    def get_session_cookie(cls) -> Optional[str]:
        return get_env(cls.SESSION_COOKIE)

    @classmethod
    def has_auth(cls) -> bool:
        return bool(cls.get_session_cookie() or (get_env(cls.EMAIL) and get_env(cls.PASSWORD)))


class Resend:
    API_KEY = "RESEND_API_KEY"
    FROM_EMAIL = "RESEND_FROM_EMAIL"

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        return get_env(cls.API_KEY)

    @classmethod
    def get_from_email(cls) -> Optional[str]:
        return get_env(cls.FROM_EMAIL) or "Rhigden <rhigden@syntolabs.xyz>"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.get_api_key())


class Cal:
    API_KEY = "CAL_API_KEY"

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        return get_env(cls.API_KEY)

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.get_api_key())
