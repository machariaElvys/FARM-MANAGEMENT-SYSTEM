from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.domain import User
from app.security import read_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Please sign in to continue.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    user_id = read_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized
    user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None:
        raise unauthorized
    return user
