# app/replies/replies.py

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 SQLAlchemy 세션




from app.database import get_db
from app.replies import replies_schemas
from app.replies.replies_services import RepliesServices
from app.users import users_models, dependencies

router = APIRouter(
    prefix='/api/replies',
    tags=['Replies'],
)

# get_services() 함수는 내부적으로 ShipmentsServices(db)를 반환합니다.
# 👉 즉, DB 세션이 주입된 상태의 클래스 인스턴스를 만들어 반환.
#
# service: ShipmentsServices = Depends(get_services)
# 👉 FastAPI는 의존성 주입(Dependency Injection)을 통해 service에 ShipmentsServices(db) 인스턴스를 넣어줌.
#
# 따라서 service.list_shipment(...)을 호출하면,
# 👉 이미 DB 세션이 연결된 상태의 ShipmentsServices 인스턴스를 통해,
# 👉 그 안에 정의된 list_shipment() 메서드를 실행됨.

def get_services(db:AsyncSession =Depends(get_db)) -> RepliesServices:
    return RepliesServices(db)


@router.get('/{post_id}', response_model=replies_schemas.ReplyPageOut, status_code=200)
async def list_replies(
        post_id: int,  # URL에서 post_id를 가져옴
        page: int = 1,  # page 를 기본값을 1을줌
        size: int = 10,  # 리스트 사이즈를 10개를줌
        _:users_models.User=Depends(dependencies.user_only),
        service: RepliesServices = Depends(get_services)
    ):
        return await service.list_replies(
            post_id=post_id,
            page=page,
            size=size,
        )
@router.post('/{post_id}', response_model=replies_schemas.ReplyOut, status_code=201)
async def create_reply(
        post_id: int,
        payload: replies_schemas.ReplyCreate,
        current_user: users_models.User = Depends(dependencies.user_only),
        service:RepliesServices=Depends(get_services)
    ):
        return await service.create_reply(
            post_id=post_id,
            payload=payload,
            current_user=current_user,
        )
@router.put('/{reply_id}', response_model=replies_schemas.ReplyOut, status_code=200)
async def update_reply(
        reply_id: int,
        payload: replies_schemas.ReplyUpdate,
        current_user: users_models.User = Depends(dependencies.user_only),
        service:RepliesServices=Depends(get_services)
    ):
        return await service.update_reply(
            reply_id=reply_id,
            payload=payload,
            current_user=current_user,
        )
@router.delete('/{reply_id}', status_code=204)
async def delete_reply(
        reply_id: int,
        current_user: users_models.User = Depends(dependencies.user_only),
        service:RepliesServices=Depends(get_services)
    ):
        await service.delete_reply(
            reply_id=reply_id,
            current_user=current_user,
        )
