from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.domain import FarmRecord, RecordCategory, User, new_id
from app.schemas.api import RecordRead, RecordWrite

router = APIRouter(prefix="/records", tags=["farm records"])


def serialize_record(record: FarmRecord) -> RecordRead:
    return RecordRead(
        id=record.id,
        category=record.category.name,
        category_label=record.category.label,
        title=record.title,
        occurred_on=record.occurred_on,
        notes=record.notes,
        quantity=record.quantity,
        unit=record.unit,
        amount=record.amount,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def find_category(db: Session, name: str) -> RecordCategory:
    category = db.scalar(select(RecordCategory).where(RecordCategory.name == name))
    if category is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown record category.")
    return category


def owned_record(db: Session, record_id: str, farmer_id: str) -> FarmRecord:
    record = db.scalar(
        select(FarmRecord)
        .options(joinedload(FarmRecord.category))
        .where(FarmRecord.id == record_id, FarmRecord.farmer_id == farmer_id)
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm record not found.")
    return record


@router.get("", response_model=list[RecordRead])
def list_records(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RecordRead]:
    statement = (
        select(FarmRecord)
        .options(joinedload(FarmRecord.category))
        .where(FarmRecord.farmer_id == current_user.id)
    )
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(FarmRecord.title.ilike(term), FarmRecord.notes.ilike(term)))
    if category:
        statement = statement.join(FarmRecord.category).where(RecordCategory.name == category)
    if start_date:
        statement = statement.where(FarmRecord.occurred_on >= start_date)
    if end_date:
        statement = statement.where(FarmRecord.occurred_on <= end_date)
    statement = statement.order_by(FarmRecord.occurred_on.desc(), FarmRecord.created_at.desc())
    records = db.scalars(statement.limit(limit).offset(offset)).unique().all()
    return [serialize_record(record) for record in records]


@router.post("", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: RecordWrite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecordRead:
    record = FarmRecord(
        id=str(UUID(new_id())),
        farmer_id=current_user.id,
        category=find_category(db, payload.category),
        title=payload.title.strip(),
        occurred_on=payload.occurred_on,
        notes=payload.notes.strip(),
        quantity=payload.quantity,
        unit=payload.unit.strip(),
        amount=payload.amount,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_record(owned_record(db, record.id, current_user.id))


@router.put("/{record_id}", response_model=RecordRead)
def update_record(
    record_id: UUID,
    payload: RecordWrite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecordRead:
    record = owned_record(db, str(record_id), current_user.id)
    record.category = find_category(db, payload.category)
    record.title = payload.title.strip()
    record.occurred_on = payload.occurred_on
    record.notes = payload.notes.strip()
    record.quantity = payload.quantity
    record.unit = payload.unit.strip()
    record.amount = payload.amount
    db.commit()
    db.refresh(record)
    return serialize_record(owned_record(db, record.id, current_user.id))


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    record = owned_record(db, str(record_id), current_user.id)
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
