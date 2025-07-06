# app/progress/progress.py

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

from app.database import get_db
from app.progress.progress_services import ProgressServices
from app.progress import progress_schemas
from app.users import users_models, dependencies

router = APIRouter(
    prefix='/api',
    tags=['Progress']
)


def get_services(db: AsyncSession = Depends(get_db)) -> ProgressServices:
    return ProgressServices(db)


@router.get('/progress/{post_id}', response_model=progress_schemas.ProgressOut, status_code=200)
async def get_progress(
        post_id: int,
        _: users_models.User = Depends(dependencies.user_only),
        service: ProgressServices = Depends(get_services)
):
    return await service.get_progress(
        post_id=post_id,
    )


@router.post('/progress/{post_id}', response_model=progress_schemas.ProgressOut, status_code=201)
async def create_progress(
        payload: progress_schemas.ProgressCreate,
        post_id: int,
        current_user: users_models.User = Depends(dependencies.staff_only),
        service: ProgressServices = Depends(get_services)
):
    return await service.create_progress(
        current_user,
        payload=payload,
        post_id=post_id,
    )


@router.put('/progress/{progress_id}', response_model=progress_schemas.ProgressOut, status_code=201)
async def update_progress(
        payload: progress_schemas.ProgressUpdate,
        progress_id: int,
        current_user: users_models.User = Depends(dependencies.staff_only),
        service: ProgressServices = Depends(get_services)
):
    return await service.update_progress(
        current_user,
        payload=payload,
        progress_id=progress_id,
    )


@router.delete('/progress/{progress_id}', status_code=204)
async def delete_progress(
        progress_id: int,
        current_user: users_models.User = Depends(dependencies.admin_only),
        service: ProgressServices = Depends(get_services),
):
    await service.delete_progress(
        progress_id=progress_id,
        current_user=current_user,
    )
