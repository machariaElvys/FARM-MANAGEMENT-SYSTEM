from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_admin
from app.models.domain import FarmRecord, User
from app.schemas.api import (
    AdminOverviewRead,
    AdminUserListRead,
    AdminUserRead,
    AdminUserStatusUpdate,
)

router = APIRouter(prefix="/admin", tags=["administration"])


@router.get("/overview", response_model=AdminOverviewRead)
def admin_overview(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminOverviewRead:
    today = date.today()

    return AdminOverviewRead(
        total_users=db.scalar(select(func.count(User.id))) or 0,
        active_users=db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0,
        total_records=db.scalar(select(func.count(FarmRecord.id))) or 0,
        records_this_year=db.scalar(
            select(func.count(FarmRecord.id)).where(
                FarmRecord.occurred_on >= date(today.year, 1, 1),
                FarmRecord.occurred_on < date(today.year + 1, 1, 1),
            )
        ) or 0,
    )


@router.get("/users", response_model=AdminUserListRead)
def list_users(
    search: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminUserListRead:
    conditions = []
    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append(or_(User.name.ilike(term), User.email.ilike(term)))

    total = db.scalar(select(func.count(User.id)).where(*conditions)) or 0
    rows = db.execute(
        select(User, func.count(FarmRecord.id).label("record_count"))
        .outerjoin(FarmRecord, FarmRecord.farmer_id == User.id)
        .where(*conditions)
        .group_by(User.id)
        .order_by(User.created_at.desc(), User.name.asc())
        .limit(limit)
        .offset(offset)
    ).all()

    items = [
        AdminUserRead(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            record_count=record_count,
        )
        for user, record_count in rows
    ]
    return AdminUserListRead(items=items, total=total, limit=limit, offset=offset)


@router.patch("/users/{user_id}/status", response_model=AdminUserRead)
def set_user_status(
    user_id: str,
    payload: AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> AdminUserRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You cannot suspend your own account.")
    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Administrator accounts cannot be changed from this page.",
        )

    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    record_count = db.scalar(select(func.count(FarmRecord.id)).where(FarmRecord.farmer_id == user.id)) or 0
    return AdminUserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        record_count=record_count,
    )
