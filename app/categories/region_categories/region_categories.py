# app/categories/region_categories/region_categories.py
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession


from app.database import get_db

from app.categories.region_categories import region_categories_schemas
from app.categories.region_categories.region_categories_services import RegionCategoriesServices
from app.users import users_models
from app.users import dependencies

router = APIRouter(
    prefix='/api/category',
    tags=['RegionCategory'],
)

def get_services(db:AsyncSession =Depends(get_db)) -> RegionCategoriesServices:
    return RegionCategoriesServices(db)

@router.get('/region', response_model=List[region_categories_schemas.CategoryOut], status_code=200)
async def list_region_categories(
        _: users_models.User = Depends(dependencies.user_only),
        service:RegionCategoriesServices=Depends(get_services)
):
    return await service.list_region_categories(

    )


@router.post('/region', response_model=region_categories_schemas.CategoryOut, status_code=201)
async def create_region_categories(
        payload: region_categories_schemas.CategoryCreate,
        current_user: users_models.User = Depends(dependencies.admin_only),
        service:RegionCategoriesServices=Depends(get_services)
):
    return await service.create_region_categories(
        payload=payload,
        current_user=current_user,
    )



@router.delete('/region/{region_category_id}', status_code=204)
async def delete_region_categories(
        region_category_id: int,
        current_user : users_models.User = Depends(dependencies.admin_only),
        service:RegionCategoriesServices=Depends(get_services)
):
    await service.delete_region_categories(
        region_category_id=region_category_id,
        current_user=current_user,
    )