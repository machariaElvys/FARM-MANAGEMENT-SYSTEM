import csv
import io
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.domain import FarmRecord, User

router = APIRouter(prefix="/reports", tags=["reports"])

EXPENDITURE_TYPES = {"inputs", "labour", "expenses"}
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _year_records(db: Session, farmer_id: str, report_year: int) -> list[FarmRecord]:
    return (
        db.scalars(
            select(FarmRecord)
            .options(joinedload(FarmRecord.category))
            .where(
                FarmRecord.farmer_id == farmer_id,
                FarmRecord.occurred_on >= date(report_year, 1, 1),
                FarmRecord.occurred_on < date(report_year + 1, 1, 1),
            )
            .order_by(FarmRecord.occurred_on.desc(), FarmRecord.created_at.desc())
        )
        .unique()
        .all()
    )


@router.get("/summary")
def report_summary(
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    report_year = year or date.today().year
    records = _year_records(db, current_user.id, report_year)

    expenses = sum((r.amount or Decimal("0")) for r in records if r.category.name in EXPENDITURE_TYPES)
    sales = sum((r.amount or Decimal("0")) for r in records if r.category.name == "sales")
    profit = sales - expenses

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

    monthly = []
    for month in range(1, 13):
        month_records = [r for r in records if r.occurred_on.month == month]
        month_expenses = sum((r.amount or Decimal("0")) for r in month_records if r.category.name in EXPENDITURE_TYPES)
        month_sales = sum((r.amount or Decimal("0")) for r in month_records if r.category.name == "sales")
        monthly.append(
            {
                "month": month,
                "label": MONTH_NAMES[month - 1],
                "expenses": float(month_expenses),
                "sales": float(month_sales),
                "profit": float(month_sales - month_expenses),
                "record_count": len(month_records),
            }
        )

    return {
        "year": report_year,
        "record_count": len(records),
        "expenses": float(expenses),
        "sales": float(sales),
        "profit": float(profit),
        "harvest_quantities": [
            {"unit": unit, "quantity": float(quantity)}
            for unit, quantity in sorted(harvest_by_unit.items())
        ],
        "categories": [
            {"name": name, "label": values["label"], "count": values["count"], "amount": float(values["amount"])}
            for name, values in sorted(categories.items())
        ],
        "monthly": monthly,
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


@router.get("/export.csv")
def export_records_csv(
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Download the farmer's records as CSV (one year, or all years if omitted)."""
    if year is not None:
        records = _year_records(db, current_user.id, year)
        filename = f"shamba-ledger-records-{year}.csv"
    else:
        records = (
            db.scalars(
                select(FarmRecord)
                .options(joinedload(FarmRecord.category))
                .where(FarmRecord.farmer_id == current_user.id)
                .order_by(FarmRecord.occurred_on.asc(), FarmRecord.created_at.asc())
            )
            .unique()
            .all()
        )
        filename = "shamba-ledger-records.csv"

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "category", "title", "quantity", "unit", "amount_kes", "notes"])
    for record in records:
        writer.writerow(
            [
                record.occurred_on.isoformat(),
                record.category.label,
                record.title,
                "" if record.quantity is None else str(record.quantity),
                record.unit,
                "" if record.amount is None else str(record.amount),
                record.notes,
            ]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
