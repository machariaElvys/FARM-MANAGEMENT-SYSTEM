from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.domain import FarmRecord, User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
def report_summary(
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    report_year = year or date.today().year
    records = db.scalars(
        select(FarmRecord)
        .options(joinedload(FarmRecord.category))
        .where(
            FarmRecord.farmer_id == current_user.id,
            FarmRecord.occurred_on >= date(report_year, 1, 1),
            FarmRecord.occurred_on < date(report_year + 1, 1, 1),
        )
        .order_by(FarmRecord.occurred_on.desc(), FarmRecord.created_at.desc())
    ).unique().all()

    expenditure_types = {"inputs", "labour", "expenses"}
    expenses = sum((r.amount or Decimal("0")) for r in records if r.category.name in expenditure_types)
    sales = sum((r.amount or Decimal("0")) for r in records if r.category.name == "sales")
    harvest_by_unit: dict[str, Decimal] = {}
    for record in records:
        if record.category.name == "harvest" and record.quantity is not None:
            unit = record.unit.strip() or "unspecified unit"
            harvest_by_unit[unit] = harvest_by_unit.get(unit, Decimal("0")) + record.quantity
    categories: dict[str, dict] = {}
    for record in records:
        bucket = categories.setdefault(record.category.name, {"label": record.category.label, "count": 0, "amount": Decimal("0")})
        bucket["count"] += 1
        bucket["amount"] += record.amount or Decimal("0")

    return {
        "year": report_year,
        "record_count": len(records),
        "expenses": float(expenses),
        "sales": float(sales),
        "harvest_quantities": [
            {"unit": unit, "quantity": float(quantity)}
            for unit, quantity in sorted(harvest_by_unit.items())
        ],
        "categories": [
            {"name": name, "label": values["label"], "count": values["count"], "amount": float(values["amount"])}
            for name, values in sorted(categories.items())
        ],
        "recent_records": [
            {
                "id": record.id,
                "title": record.title,
                "category": record.category.label,
                "occurred_on": record.occurred_on.isoformat(),
                "amount": float(record.amount) if record.amount is not None else None,
            }
            for record in records[:5]
        ],
    }
