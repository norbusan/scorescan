import uuid
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with a unique JTI."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    from app.utils.token_blacklist import get_password_generation

    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "pwd_gen": get_password_generation(data.get("sub", "")),
    })
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token with a unique JTI."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    from app.utils.token_blacklist import get_password_generation

    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "pwd_gen": get_password_generation(data.get("sub", "")),
    })
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify a JWT token, checking type, blacklist, and password generation."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != token_type:
            return None

        # Check blacklist
        jti = payload.get("jti")
        if jti:
            from app.utils.token_blacklist import is_token_blacklisted
            if is_token_blacklisted(jti):
                return None

        # Check password generation — tokens issued before a password change are invalid
        user_id = payload.get("sub")
        token_pwd_gen = payload.get("pwd_gen")
        if user_id is not None and token_pwd_gen is not None:
            from app.utils.token_blacklist import get_password_generation
            current_gen = get_password_generation(user_id)
            if current_gen > token_pwd_gen:
                return None

        return payload
    except JWTError:
        return None
