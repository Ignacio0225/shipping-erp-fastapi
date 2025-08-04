# app/progress_detail_container/progress_detail_container_schemas.py

from datetime import datetime, date
from typing import List

from pydantic import BaseModel,Field

from app.users import users_schemas


class ProgressDetailContainerDetailBase(BaseModel):
    MODEL: str | None
    CHASSISNo: str | None
    EL: bool | None
    HBL: str | None


class ProgressDetailContainerDetailCreate(ProgressDetailContainerDetailBase):
    pass


class ProgressDetailContainerDetailUpdate(ProgressDetailContainerDetailBase):
    pass


class ProgressDetailContainerDetailOut(ProgressDetailContainerDetailBase):
    id: int

    class Config:
        from_attributes = True


class ProgressDetailContainerBase(BaseModel):
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
    BUY:int | None =None
    SELL: int | None = None
    SHORING:int | None = None
    TRUCKING:int | None = None
    THC: int | None = None
    WFG: int | None = None
    SECURITY: int | None = None
    CARRIER: int | None = None
    PARTNER_FEE: int | None = None
    OTHER: int | None = None
    RATE: float | None = None
    PROFIT_USD: float | None = None
    PROFIT_KRW: float | None = None
    SALESMAN:str|None=None
    progress_detail_container_detail: List[ProgressDetailContainerDetailCreate] = Field(default_factory=list)


class ProgressDetailContainerCreate(ProgressDetailContainerBase):
    pass


class ProgressDetailContainerUpdate(ProgressDetailContainerBase):
    pass


class ProgressDetailContainerOut(ProgressDetailContainerBase):
    id: int
    created_at: datetime
    updated_at: datetime | None
    creator: users_schemas.UserOut
    progress_detail_container_detail: List[ProgressDetailContainerDetailOut] = Field(default_factory=list)

    class Config:
        from_attributes = True
