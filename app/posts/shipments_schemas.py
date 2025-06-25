# app/posts/shipments_schemas.py
# API 요청과 응답에 사용될 Pydantic 모델을 정의하는 파일
from app.region_categories import region_categories_schemas
from app.type_categories import type_categories_schemas
from app.users import users_schemas


from typing import List
from pydantic import BaseModel
from datetime import datetime


#get에 사용
class ShipmentBase(BaseModel):
    title:str
    description:str

#post에 사용
class ShipmentCreate(ShipmentBase):
    pass


#put에 사용
class ShipmentUpdate(ShipmentBase):
    title: str | None
    description: str | None
    type_category_id:int |None
    region_category_id:int |None


#데이터를 받아올때 유효성검사를 위한 모델에 사용 (파일 패스가 리스트기때문에)
class ShipmentOut(ShipmentBase):
    id:int
    file_paths:list[str] | None
    created_at:datetime
    updated_at:datetime | None
    creator:users_schemas.UserOut
    type_category:type_categories_schemas.CategoryOut
    region_category:region_categories_schemas.CategoryOut

    class Config:
        from_attributes = True

# ShipmentOut 자체를 리스트에 다 담아줌
class ShipmentsPageOut(BaseModel):
    items: List[ShipmentOut]
    total: int
    page: int
    size: int
    total_pages: int
