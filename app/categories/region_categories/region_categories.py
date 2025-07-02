from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete
from typing import List

from app import database
from app.categories.region_categories import region_categories_models
from app.categories.region_categories import region_categories_schemas
from app.users import users_models
from app.users import dependencies

router = APIRouter(
    prefix='/api/category',
    tags=['RegionCategory'],
)


@router.get('/region', response_model=List[region_categories_schemas.CategoryOut], status_code=200)
async def list_region_categories(
        db: AsyncSession = Depends(database.get_db),
        _: users_models.User = Depends(dependencies.user_only),
):
    base_query = select(region_categories_models.RegionCategory)
    base_query = base_query.options(
        selectinload(region_categories_models.RegionCategory.creator),
    )

    result = await db.execute(base_query)
    region_categories = result.scalars().all()
    return region_categories


@router.post('/region', response_model=List[region_categories_schemas.CategoryOut], status_code=201)
async def create_region_categories(
        payload: region_categories_schemas.CategoryCreate,
        db: AsyncSession = Depends(database.get_db),
        current_user: users_models.User = Depends(dependencies.admin_only),
):
    # Pydantic 객체를 unpack해서 모델 인스턴스 생성
    new_region_category = region_categories_models.RegionCategory(**payload.model_dump(), creator_id=current_user.id)

    db.add(new_region_category)
    await db.commit()
    result = await db.execute(
        select(region_categories_models.RegionCategory)
        .options(
            selectinload(region_categories_models.RegionCategory.creator),  # 작성자 정보  # 지역 관계
        )
    )
    region_category_relations = result.scalar_one()

    return region_category_relations  # JSON 직렬화 -> 응답



@router.delete('/region/{region_category_id}', status_code=204)
async def delete_region_categories(
        region_category_id: int,
        db: AsyncSession = Depends(database.get_db),
        current_user : users_models.User = Depends(dependencies.admin_only),
):
    region_category_id = await db.get(region_categories_models.RegionCategory, region_category_id)

    if not region_category_id:
        raise HTTPException(404,'Region Category not found')

    if region_category_id.creator_id != current_user.id:
        raise HTTPException(status_code=403,detail='작성자만 삭제할 수 있습니다.')
    await db.execute(
        delete(region_categories_models.RegionCategory)
        .where(region_categories_models.RegionCategory.id == region_category_id)
    )
    await db.commit()