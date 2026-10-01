from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

RecordCategoryName = Literal["planting", "inputs", "labour", "expenses", "harvest", "sales"]


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class RecordWrite(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    category: RecordCategoryName
    occurred_on: date
    notes: str = Field(default="", max_length=4000)
    quantity: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    unit: str = Field(default="", max_length=40)
    amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class RecordRead(BaseModel):
    id: str
    category: str
    category_label: str
    title: str
    occurred_on: date
    notes: str
    quantity: Decimal | None
    unit: str
    amount: Decimal | None
    created_at: datetime
    updated_at: datetime
