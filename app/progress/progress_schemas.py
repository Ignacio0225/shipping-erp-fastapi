# app/progress/progress_schemas.py
from typing import List

from pydantic import BaseModel

from datetime import datetime


from app.posts import posts_schemas
from app.progress_detail_roro import progress_detail_roro_schemas
from app.users import users_schemas


class ProgressBase(BaseModel):
    title: str

class ProgressCreate(ProgressBase):
    pass

class ProgressUpdate(ProgressBase):
    title: str |None


class ProgressOut(ProgressBase):
    created_at:datetime
    updated_at:datetime|None
    creator:users_schemas.UserOut
    progress_detail_roro:List[progress_detail_roro_schemas.ProgressDetailRoRoOut]|None
    post:posts_schemas.SimplePostOut

    class Config:
        from_attributes = True
