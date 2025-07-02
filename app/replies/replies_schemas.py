from app.posts import shipments_schemas
from app.users import users_schemas


from typing import List
from pydantic import BaseModel
from datetime import datetime

#get에 사용
class ReplyBase(BaseModel):
    description:str


#post에 사용
class ReplyCreate(ReplyBase):
    pass

#put에 사용
class ReplyUpdate(BaseModel):
    description:str | None

class ReplyOut(ReplyBase):
    id: int
    description:str | None
    created_at: datetime
    updated_at: datetime |None
    creator: users_schemas.UserOut
    shipments:shipments_schemas.SimpleShipmentOut


class ReplyPageOut(BaseModel):
    items: List[ReplyOut]
    total: int
    page: int
    size: int
    total_pages: int