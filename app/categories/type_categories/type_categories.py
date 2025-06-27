
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List

from app import database
from app.categories.type_categories import type_categories_schemas, type_categories_models
from app.users import users_models
from app.users import dependencies

router = APIRouter(
    prefix='/api/category',
    tags=['TypeCategory'],
)


@router.get('/type', response_model=List[type_categories_schemas.CategoryOut], status_code=200)
async def list_type_categories(
        db: AsyncSession = Depends(database.get_db),
        _: users_models.User = Depends(dependencies.admin_only),
):
    base_query = select(type_categories_models.TypeCategory)
    result = await db.execute(base_query)
    type_categories = result.scalars().all()
    return type_categories


@router.post('/type', response_model=List[type_categories_schemas.CategoryOut], status_code=201)
async def create_type_categories(
        payload: type_categories_schemas.CategoryCreate,
        db: AsyncSession = Depends(database.get_db),
        current_user: users_models.User = Depends(dependencies.admin_only),
):
    # Pydantic 객체를 unpack해서 모델 인스턴스 생성
    new_type_category = type_categories_models.TypeCategory(**payload.model_dump(), creator_id=current_user.id)

    db.add(new_type_category)
    await db.commit()
    await db.refresh(new_type_category)
    return new_type_category


@router.delete('/type/{type_category_id}', status_code=204)
async def delete_type_categories(
        type_category_id: int,
        db: AsyncSession = Depends(database.get_db),
        current_user : users_models.User = Depends(dependencies.admin_only),
):
    type_category = await db.get(type_categories_models.TypeCategory, type_category_id)

    if not type_category:
        raise HTTPException(404,'Type Category not found')

    if type_category.creator_id != current_user.id:
        raise HTTPException(status_code=403,detail='작성자만 삭제할 수 있습니다.')
    await db.execute(
        delete(type_categories_models.TypeCategory)
        .where(type_categories_models.TypeCategory.id == type_category_id)
    )
    await db.commit()