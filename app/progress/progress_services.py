# app/progress/progress_services.py
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from app.progress import progress_models, progress_schemas
from app.progress_detail_roro import progress_detail_roro_models
from app.users import users_models

ERROR_NOT_FOUND = 'Progress Detail 을 찾을 수 없습니다. (404 Not Found)'


class ProgressServices:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_progress(
            self,
            post_id: int,
    ):
        base_query = (
            select(progress_models.Progress)
            .where(progress_models.Progress.post_id == post_id)
            .options(
                selectinload(progress_models.Progress.creator),
                selectinload(progress_models.Progress.post),
                selectinload(progress_models.Progress.progress_detail_roro).selectinload(
                    progress_detail_roro_models.ProgressRoRo.progress_detail_roro_detail),
            )
        )
        result = await self.db.execute(base_query)
        progress = result.scalar_one_or_none()
        return progress

    async def create_progress(
            self,
            current_user: users_models.User,
            payload: progress_schemas.ProgressCreate,
            post_id: int,
    ):
        new_progress = progress_models.Progress(
            payload.model_dump(
                exclude_unset=True,
            ),
            creator_id=current_user.id,
            post_id=post_id,
        )
        self.db.add(new_progress)
        await self.db.commit()

        result = await self.db.execute(
            select(progress_models.Progress)
            .where(progress_models.Progress.post_id == post_id)
            .options(
                selectinload(progress_models.Progress.creator),
                selectinload(progress_models.Progress.post),
                selectinload(progress_models.Progress.progress_detail_roro)
                .selectinload(progress_detail_roro_models.ProgressRoRo.progress_detail_roro_detail),
            )
        )

        progress = result.scalar_one_or_none()

        return progress

    async def update_progress(
            self,
            current_user: users_models.User,
            payload: progress_schemas.ProgressUpdate,
            progress_id: int,
    ):
        progress = await self.db.get(
            progress_models.Progress, progress_id)

        if not progress:
            raise HTTPException(status_code=404, detail=ERROR_NOT_FOUND)  # 없으면 404 에러

        if progress.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")  # 작성자만 수정 가능

        await self.db.execute(
            update(progress_models.Progress)
            .where(progress_models.Progress.id == progress_id)
            .values(**payload.model_dump(
                exclude_unset=True, )
                    ))
        await self.db.commit()

        result = await self.db.execute(
            select(progress_models.Progress)
            .where(progress_models.Progress.id == progress_id)
            .options(
                selectinload(progress_models.Progress.creator),
                selectinload(progress_models.Progress.post),
                selectinload(progress_models.Progress.progress_detail_roro)
                .selectinload(progress_detail_roro_models.ProgressRoRo.progress_detail_roro_detail),
            )
        )

        progress = result.scalar_one_or_none()

        return progress

    async def delete_progress(
            self,
            current_user: users_models.User,
            progress_id: int,
    ):
        progress = await self.db.get(progress_models.Progress, progress_id)
        if not progress:
            if not progress:
                raise HTTPException(status_code=404, detail='Progress not found')
            if progress.creator_id != current_user.id:
                raise HTTPException(status_code=403, detail='관리자만 삭제할 수 있습니다.')

        await self.db.execute(
            delete(progress_models.Progress)
            .where(progress_models.Progress.id == progress_id)
        )
        await self.db.commit()
