from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import get_settings
from app.database.session import Base, SessionLocal, engine
from app.models.domain import RecordCategory
from app.routers import admin, auth, records, reports

DEFAULT_CATEGORIES = [
    ("planting", "Planting"),
    ("inputs", "Farm inputs"),
    ("labour", "Labour"),
    ("expenses", "Other expenses"),
    ("harvest", "Harvest"),
    ("sales", "Sales"),
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for sort_order, (name, label) in enumerate(DEFAULT_CATEGORIES):
            if db.scalar(select(RecordCategory).where(RecordCategory.name == name)) is None:
                db.add(RecordCategory(name=name, label=label, sort_order=sort_order))
        db.commit()
    yield


settings = get_settings()
app = FastAPI(title="Farm Record Management API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api")
app.include_router(records.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
