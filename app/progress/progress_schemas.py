# app/progress/progress_schemas.py
from typing import List

from pydantic import BaseModel

from datetime import datetime


from app.posts import posts_schemas
from app.progress_detail_container import progress_detail_container_schemas
from app.progress_detail_roro import progress_detail_roro_schemas
from app.users import users_schemas


class ProgressBase(BaseModel):
    title: str

class ProgressCreate(ProgressBase):
    pass

class ProgressUpdate(ProgressBase):
    title: str |None = None


class ProgressOut(ProgressBase):
    id:int
    created_at:datetime
    updated_at:datetime|None = None
    creator:users_schemas.UserOut
    progress_detail_roro:List[progress_detail_roro_schemas.ProgressDetailRoRoOut]|None = None
    progress_detail_container:List[progress_detail_container_schemas.ProgressDetailContainerOut]|None = None
    post:posts_schemas.SimplePostOut

    class Config:
        from_attributes = True
