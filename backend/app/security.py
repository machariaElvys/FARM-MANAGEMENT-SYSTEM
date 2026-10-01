from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": user_id, "exp": expires_at}, settings.jwt_secret, algorithm="HS256")


def read_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        subject = payload.get("sub")
        return subject if isinstance(subject, str) else None
    except jwt.PyJWTError:
        return None
