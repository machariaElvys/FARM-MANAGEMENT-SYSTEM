from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.domain import User
from app.schemas.api import LoginRequest, RegisterRequest, TokenRead, UserRead
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=TokenRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenRead:
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password), role="farmer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenRead(access_token=create_access_token(user.id), user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenRead)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenRead:
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email, User.is_active.is_(True)))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect.")
    return TokenRead(access_token=create_access_token(user.id), user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
