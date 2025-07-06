# app/progress_detail_roro/progress_detail_roro.py
from typing import List

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 SQLAlchemy 세션

from app.database import get_db
from app.progress_detail_roro import progress_detail_roro_schemas
from app.progress_detail_roro.progress_detail_roro_services import ProgressRoRoServices

from app.users import users_models, dependencies

router = APIRouter(
    prefix='/api/progress',
    tags=['ProgressRoRo'],
)


def get_services(db: AsyncSession = Depends(get_db)) -> ProgressRoRoServices:
    return ProgressRoRoServices(db)


@router.get('/roro/{progress_id}', response_model=List[progress_detail_roro_schemas.ProgressDetailRoRoOut], status_code=200)
async def get_progress_roro(
        progress_id: int,
        _: users_models.User = Depends(dependencies.staff_only),
        service: ProgressRoRoServices = Depends(get_services)
):
    return await service.get_progress_roro(
        progress_id=progress_id,
    )

@router.post('/roro/{progress_id}',response_model=progress_detail_roro_schemas.ProgressDetailRoRoOut,status_code=201)
async def create_progress_roro(
        progress_id:int,
        payload:progress_detail_roro_schemas.ProgressDetailRoRoCreate,
        current_user:users_models.User=Depends(dependencies.staff_only),
        service:ProgressRoRoServices=Depends(get_services)
):
    return await service.create_progress_roro(
        progress_id=progress_id,
        payload=payload,
        current_user=current_user,
    )

@router.patch('/roro/{progress_roro_id}',response_model=progress_detail_roro_schemas.ProgressDetailRoRoOut,status_code=201)
async def patch_progress_roro(
        progress_roro_id:int,
        payload:progress_detail_roro_schemas.ProgressDetailRoRoUpdate,
        current_user:users_models.User=Depends(dependencies.staff_only),
        service:ProgressRoRoServices=Depends(get_services)
):
    return await service.patch_progress_roro(
        progress_roro_id=progress_roro_id,
        payload=payload,
        current_user=current_user,
    )
