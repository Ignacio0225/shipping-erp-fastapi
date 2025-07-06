# app/categories/type_categories/type_categories_services.py

from fastapi import  Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload



from app.categories.type_categories import type_categories_schemas, type_categories_models
from app.users import users_models



ERROR_NOT_FOUND='타입 카테고리를 찾을 수 없습니다. (404 Not Found)'
ERROR_FORBIDDEN='작성자만 삭제할 수 있습니다.'


class TypeCategoriesServices:

    def __init__(self,db:AsyncSession):
        self.db=db


    async def list_type_categories(
            self,
    ):
        base_query = (
            select(type_categories_models.TypeCategory)
            .options(selectinload(type_categories_models.TypeCategory.creator),
        ))
        result = await self.db.execute(base_query)
        type_categories = result.scalars().all()
        return type_categories

    async def create_type_categories(
            self,
            payload: type_categories_schemas.CategoryCreate,
            current_user: users_models.User,
    ):
        # Pydantic 객체를 unpack해서 모델 인스턴스 생성
        new_type_category = type_categories_models.TypeCategory(**payload.model_dump(), creator_id=current_user.id)

        self.db.add(new_type_category)
        await self.db.commit()
        result = await self.db.execute(
            select(type_categories_models.TypeCategory)
            .options(
                selectinload(type_categories_models.TypeCategory.creator),  # 작성자 정보  # 지역 관계
            ).where(type_categories_models.TypeCategory.id == new_type_category.id)
        )
        type_category_relations = result.scalar_one()

        return type_category_relations  # JSON 직렬화 -> 응답

    async def delete_type_categories(
            self,
            type_category_id: int,
            current_user: users_models.User,
    ):
        type_category = await self.db.get(type_categories_models.TypeCategory, type_category_id)

        if not type_category:
            raise HTTPException(status_code=404,detail=ERROR_NOT_FOUND)

        if type_category.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail=ERROR_FORBIDDEN)
        await self.db.execute(
            delete(type_categories_models.TypeCategory)
            .where(type_categories_models.TypeCategory.id == type_category_id)
        )
        await self.db.commit()


