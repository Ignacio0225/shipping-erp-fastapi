# app/categories/type_categories/type_categories.py
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession


from app.database import get_db
from app.categories.type_categories import type_categories_schemas, type_categories_models
from app.categories.type_categories.type_categories_services import TypeCategoriesServices
from app.users import users_models
from app.users import dependencies

router = APIRouter(
    prefix='/api/category',
    tags=['TypeCategory'],
)

def get_services(db:AsyncSession =Depends(get_db)) -> TypeCategoriesServices:
    return TypeCategoriesServices(db)


@router.get('/type', response_model=List[type_categories_schemas.CategoryOut], status_code=200)
async def list_type_categories(
        _: users_models.User = Depends(dependencies.user_only),
        service:TypeCategoriesServices=Depends(get_services)
):
    return await service.list_type_categories(
    )


@router.post('/type', response_model=type_categories_schemas.CategoryOut, status_code=201)
async def create_type_categories(
        payload: type_categories_schemas.CategoryCreate,
        current_user: users_models.User = Depends(dependencies.admin_only),
        service:TypeCategoriesServices=Depends(get_services)
):
    return await service.create_type_categories(
        payload=payload,
        current_user=current_user,
    )


@router.delete('/type/{type_category_id}', status_code=204)
async def delete_type_categories(
        type_category_id: int,
        current_user : users_models.User = Depends(dependencies.admin_only),
        service:TypeCategoriesServices=Depends(get_services)
):
    await service.delete_type_categories(
        type_category_id=type_category_id,
        current_user=current_user,
    )