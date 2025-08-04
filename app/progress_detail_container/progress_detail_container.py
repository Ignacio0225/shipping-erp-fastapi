# app/progress_detail_container/progress_detail_container.py

from typing import List

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 SQLAlchemy 세션

from app.database import get_db
from app.progress_detail_container import progress_detail_container_schemas
from app.progress_detail_container.progress_detail_container_services import ProgressContainerServices

from app.users import users_models, dependencies

router = APIRouter(
    prefix='/api/progress',
    tags=['ProgressContainer'],
)


def get_services(db: AsyncSession = Depends(get_db)) -> ProgressContainerServices:
    return ProgressContainerServices(db)


@router.get('/container/{progress_id}', response_model=List[progress_detail_container_schemas.ProgressDetailContainerOut], status_code=200)
async def get_progress_container(
        progress_id: int,
        _: users_models.User = Depends(dependencies.staff_only),
        service: ProgressContainerServices = Depends(get_services)
):
    return await service.get_progress_container(
        progress_id=progress_id,
    )

@router.post('/container/{progress_id}',response_model=progress_detail_container_schemas.ProgressDetailContainerOut,status_code=201)
async def create_progress_container(
        progress_id:int,
        payload:progress_detail_container_schemas.ProgressDetailContainerCreate,
        current_user:users_models.User=Depends(dependencies.staff_only),
        service:ProgressContainerServices=Depends(get_services)
):
    return await service.create_progress_container(
        progress_id=progress_id,
        payload=payload,
        current_user=current_user,
    )

@router.patch('/container/{progress_container_id}',response_model=progress_detail_container_schemas.ProgressDetailContainerOut,status_code=201)
async def patch_progress_container(
        progress_container_id:int,
        payload:progress_detail_container_schemas.ProgressDetailContainerUpdate,
        current_user:users_models.User=Depends(dependencies.staff_only),
        service:ProgressContainerServices=Depends(get_services)
):
    return await service.patch_progress_container(
        progress_container_id=progress_container_id,
        payload=payload,
        current_user=current_user,
    )
