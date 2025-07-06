# app/categories/type_categories/type_categories_schemas.py
# API 요청과 응답에 사용될 Pydantic 모델을 정의하는 파일

from pydantic import BaseModel

from app.users import users_schemas


#get에 사용
class CategoryBase(BaseModel):
    title:str

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id:int
    title:str
    creator: users_schemas.UserOut
    class Config:
        from_attributes = True