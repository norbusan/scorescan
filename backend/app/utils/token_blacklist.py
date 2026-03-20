import secrets
from typing import Optional

import redis

from app.config import get_settings

settings = get_settings()

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


# --- Token blacklist (for logout / password change invalidation) ---

_BLACKLIST_PREFIX = "token_blacklist:"


def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a token's JTI to the blacklist with a TTL matching its remaining lifetime."""
    r = get_redis()
    r.setex(f"{_BLACKLIST_PREFIX}{jti}", ttl_seconds, "1")


def is_token_blacklisted(jti: str) -> bool:
    """Check whether a token JTI has been blacklisted."""
    r = get_redis()
    return r.exists(f"{_BLACKLIST_PREFIX}{jti}") > 0


# --- User-level token invalidation (password change / reset) ---

_PWD_GEN_PREFIX = "pwd_generation:"


def increment_password_generation(user_id: str) -> int:
    """Increment and return the password generation counter for a user."""
    r = get_redis()
    return r.incr(f"{_PWD_GEN_PREFIX}{user_id}")


def get_password_generation(user_id: str) -> int:
    """Get the current password generation counter for a user (0 if unset)."""
    r = get_redis()
    val = r.get(f"{_PWD_GEN_PREFIX}{user_id}")
    return int(val) if val else 0


# --- Short-lived download tokens (replace JWT in URL query params) ---

_DOWNLOAD_PREFIX = "download_token:"
_DOWNLOAD_TTL = 60  # seconds


def create_download_token(user_id: str, job_id: str) -> str:
    """Create a short-lived, single-use download token stored in Redis."""
    token = secrets.token_urlsafe(32)
    r = get_redis()
    r.setex(
        f"{_DOWNLOAD_PREFIX}{token}",
        _DOWNLOAD_TTL,
        f"{user_id}:{job_id}",
    )
    return token


def validate_download_token(token: str, job_id: str) -> Optional[str]:
    """
    Validate and consume a download token.
    Returns the user_id if valid, None otherwise.
    The token is deleted after use (single-use).
    """
    r = get_redis()
    key = f"{_DOWNLOAD_PREFIX}{token}"
    value = r.get(key)
    if not value:
        return None
    stored_user_id, stored_job_id = value.split(":", 1)
    if stored_job_id != job_id:
        return None
    r.delete(key)  # single-use
    return stored_user_id
