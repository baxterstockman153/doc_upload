from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date, datetime
from typing import Optional


def _strip_and_check(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Field must not be empty")
    return v


def _validate_dob(v: date) -> date:
    today = date.today()
    if v > today:
        raise ValueError("date_of_birth must not be in the future")
    if (today - v).days > 120 * 365:
        raise ValueError("date_of_birth must not be more than 120 years in the past")
    return v


class OrderCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    source_file_name: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return _strip_and_check(v)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        return _validate_dob(v)


class OrderUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _strip_and_check(v)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return v
        return _validate_dob(v)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    date_of_birth: date
    source_file_name: Optional[str]
    created_at: datetime
    updated_at: datetime
