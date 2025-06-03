# app/posts/shipments_schemas.py
# API 요청과 응답에 사용될 Pydantic 모델을 정의하는 파일

from pydantic import BaseModel
from datetime import datetime


#get에 사용
class ShipmentBase(BaseModel):
    title:str
    description:str


#post에 사용
class ShipmentCreate(ShipmentBase):
    pass # ShipmentBase를 동일하게 받아옴



#put에 사용
class ShipmentUpdate(BaseModel):
    title: str | None
    description: str | None



#데이터를 받아올때 유효성검사를 위한 모델에 사용
class ShipmentOut(ShipmentBase):
    id:int
    file_paths:list[str] | None
    created_at:datetime
    creator_id:int

    class Config:
        from_attributes = True