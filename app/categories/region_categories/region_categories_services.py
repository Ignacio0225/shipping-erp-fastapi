# app/categories/region_categories/region_categories_services.py

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete

from app.categories.region_categories import region_categories_models
from app.categories.region_categories import region_categories_schemas
from app.users import users_models


ERROR_NOT_FOUND='지역 카테고리를 찾을 수 없습니다. (404 Not Found)'
ERROR_FORBIDDEN='작성자만 삭제할 수 있습니다.'



class RegionCategoriesServices:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_region_categories(
            self,
    ):
        base_query = select(region_categories_models.RegionCategory)
        base_query = base_query.options(
            selectinload(region_categories_models.RegionCategory.creator),
        )

        result = await self.db.execute(base_query)
        region_categories = result.scalars().all()
        return region_categories

    async def create_region_categories(
            self,
            payload: region_categories_schemas.CategoryCreate,
            current_user: users_models.User,
    ):
        # Pydantic 객체를 unpack해서 모델 인스턴스 생성
        new_region_category = region_categories_models.RegionCategory(
            **payload.model_dump(),
            creator_id=current_user.id
        )

        self.db.add(new_region_category)
        await self.db.commit()
        result = await self.db.execute(
            select(region_categories_models.RegionCategory)
            .options(
                selectinload(region_categories_models.RegionCategory.creator),  # 작성자 정보  # 지역 관계
            ).where(region_categories_models.RegionCategory.id==new_region_category.id)
        )
        region_category_relations = result.scalar_one()

        return region_category_relations  # JSON 직렬화 -> 응답

    async def delete_region_categories(
            self,
            region_category_id: int,
            current_user: users_models.User,
    ):
        region_category_id = await self.db.get(region_categories_models.RegionCategory, region_category_id)

        if not region_category_id:
            raise HTTPException(status_code=404, detail=ERROR_NOT_FOUND)

        if region_category_id.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail=ERROR_FORBIDDEN)
        await self.db.execute(
            delete(region_categories_models.RegionCategory)
            .where(region_categories_models.RegionCategory.id == region_category_id)
        )
        await self.db.commit()
