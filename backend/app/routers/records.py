from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.domain import FarmRecord, RecordCategory, User, new_id
from app.schemas.api import RecordRead, RecordWrite, SyncBatch

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
    record_id = str(payload.id) if payload.id else new_id()
    if db.get(FarmRecord, record_id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A record with this identifier already exists.")
    record = FarmRecord(
        id=record_id,
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


@router.post("/sync")
def sync_records(
    payload: SyncBatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    results = []
    for operation in payload.operations:
        record_id = str(operation.record_id)
        record = db.scalar(
            select(FarmRecord)
            .options(joinedload(FarmRecord.category))
            .where(FarmRecord.id == record_id)
        )

        if operation.action == "delete":
            if record is not None:
                if record.farmer_id != current_user.id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm record not found.")
                db.delete(record)
            results.append({"operation_id": str(operation.operation_id), "action": "delete", "record_id": record_id})
            continue

        if operation.record is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Upsert operations need record data.")
        if operation.record.id is not None and str(operation.record.id) != record_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Record IDs do not match.")
        if record is not None and record.farmer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm record not found.")

        category = find_category(db, operation.record.category)
        if record is None:
            record = FarmRecord(id=record_id, farmer_id=current_user.id, category=category)
            db.add(record)
        record.category = category
        record.title = operation.record.title.strip()
        record.occurred_on = operation.record.occurred_on
        record.notes = operation.record.notes.strip()
        record.quantity = operation.record.quantity
        record.unit = operation.record.unit.strip()
        record.amount = operation.record.amount
        db.flush()
        results.append({"operation_id": str(operation.operation_id), "action": "upsert", "record": serialize_record(record).model_dump(mode="json")})

    db.commit()
    return {"results": results}


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
