# app/progress_roro/progress_roro_schemas.py

from datetime import datetime, date
from typing import List

from pydantic import BaseModel,Field

from app.users import users_schemas


class ProgressDetailRoRoDetailBase(BaseModel):
    MODEL: str | None
    CHASSISNo: str | None
    EL: bool | None
    HBL: str | None


class ProgressDetailRoRoDetailCreate(ProgressDetailRoRoDetailBase):
    pass


class ProgressDetailRoRoDetailUpdate(ProgressDetailRoRoDetailBase):
    pass


class ProgressDetailRoRoDetailOut(ProgressDetailRoRoDetailBase):
    id: int

    class Config:
        from_attributes = True


class ProgressDetailRoRoBase(BaseModel):
    BKNo: str | None = None
    LINE: List[str] | None = None
    VESSEL: List[str] | None = None
    DOC: List[str] | None = None
    PARTNER: str | None = None
    ETA: date | None = None
    ETD: date | None = None
    PAYMENT: str | None = None

    ATD: date | None = None
    SHIPPER: str | None = None
    DESTINATION: str | None = None
    SMALL: int | None = None
    BUY_SMALL: int | None = None
    S_SUV: int | None = None
    BUY_S_SUV: int | None = None
    SUV: int | None = None
    BUY_SUV: int | None = None
    RV_CARGO: int | None = None
    BUY_RV_CARGO: int | None = None
    SPECIAL: int | None = None
    BUY_SPECIAL: int | None = None
    CBM: float | None = None
    BUY_CBM: float | None = None
    SELL: int | None = None
    HC: int | None = None
    WFG: int | None = None
    SECURITY: int | None = None
    CARRIER: int | None = None
    PARTNER_FEE: int | None = None
    OTHER: int | None = None
    RATE: float | None = None
    PROFIT_USD: float | None = None
    PROFIT_KRW: float | None = None
    progress_detail_roro_detail: List[ProgressDetailRoRoDetailCreate] = Field(default_factory=list)


class ProgressDetailRoRoCreate(ProgressDetailRoRoBase):
    pass


class ProgressDetailRoRoUpdate(ProgressDetailRoRoBase):
    pass


class ProgressDetailRoRoOut(ProgressDetailRoRoBase):
    id: int
    created_at: datetime
    updated_at: datetime | None
    creator: users_schemas.UserOut
    progress_detail_roro_detail: List[ProgressDetailRoRoDetailOut] = Field(default_factory=list)

    class Config:
        from_attributes = True
