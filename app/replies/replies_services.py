import math

from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 SQLAlchemy 세션
from sqlalchemy import select, update, delete, func, or_  # SQL 쿼리 빌더, 함수, OR 검색 등
from sqlalchemy.orm import selectinload


from app.replies import replies_schemas, replies_models
from app.users import users_models, dependencies



class RepliesServices:

    def __init__(self, db:AsyncSession):
        self.db = db

    async def list_replies(
            self,
            ship_id: int,  # URL에서 ship_id를 가져옴
            page: int = 1,  # page 를 기본값을 1을줌
            size: int = 10,  # 리스트 사이즈를 10개를줌
    ):
        # 파라미터 방어(음수/0 등) - 장고처럼 ValueError만큼 유연하지 않음(숫자 아닌 값 오면 FastAPI가 422로 막음)
        if page < 1:  # page가 1보다 작으면
            page = 1  # 다시 page 를 1으로 만들어버림 음수나 0일 들어와버릴경우 페이지 에서 422에러 가 나옴 그래서 방어

        if size < 1:  # 리스트가 9개 8 개 7개 올수도 있음 하지만 음수나 0이 나오면 다시 10으로 만들어버림
            size = 10
        offset = (page - 1) * size  # OFFSET 계산(몇 개를 건너뛸지)

        # page = 1  * size → offset = 0 1번째 페이지일 경우 0번부터 9번 게시글

        # page = 2 * size → offset = 10  2번째 페이지일 경우 10번부터 19번 게시글

        # page = 3 * size  → offset = 20 3번째 페이지일 경우 20번부터 29번 게시글

        # offset = 건너뛸 개수를 의미함 페이지가 2면 page -1  =  1 * 10 이니까 10번 전까지 건너뛰고 시작 한다는듯 (결국 시작 위치를 의미함)

        base_query = select(replies_models.Reply).where(
            replies_models.Reply.shipment_id == ship_id)  # 선적(게시글) 전체 SELECT 쿼리 생성

        # 검색어 있을 때만 필터링
        # → 모든 게시글을 최신순으로 페이지네이션해서 반환

        base_query = base_query.order_by(
            replies_models.Reply.created_at.desc()
        ).offset(offset).limit(size)  # limit = size <-항상 요청한 페이지당 최대 개수만큼만 반환 사이즈는 무조건 10(게시글이 10개만나옴)

        # 관계(relationship) 이 있는 db를 불러오기 위함 shipment가 아닌 creator,category 이런데서
        base_query = base_query.options(
            selectinload(replies_models.Reply.creator),
            selectinload(replies_models.Reply.shipments),
        )  # 작성자 정보(creator), 카테고리 등을 JOIN 해서 한 번에 가져오도록 설정

        result = await self.db.execute(base_query)  # 쿼리 실행해서 결과 받아옴

        replies = result.scalars().all()  # 전체 레코드 가져오기

        items = [
            replies_schemas.ReplyOut(
                id=s.id,
                description=s.description,
                created_at=s.created_at,
                updated_at=s.updated_at,
                shipments=s.shipments,
                creator=s.creator,
            )
            for s in replies  # 모든 shipments(게시글) 객체를 Pydantic 스키마로 변환, 작성자 정보 포함
            # squares = [x * x for x in range(5)] <- 리스트 내포 표현식
            # 결과: [0, 1, 4, 9, 16]
        ]

        total_count_query = select(func.count()).where(replies_models.Reply.shipment_id == ship_id)
        total_count = await self.db.scalar(total_count_query)  # 전체 게시글 개수 집계

        return {
            "items": items,  # 실제 데이터 (리스트)
            "total": total_count,  # 전체 게시글 수
            "page": page,  # 현재 페이지
            "size": size,  # 페이지당 게시글 수
            "total_pages": math.ceil(total_count / size)  # ceil 올림 함수 , 전체페이지 수를 계산함.
        }



    async def create_reply(
            self,
            ship_id: int,
            payload: replies_schemas.ReplyCreate,
            current_user: users_models.User = Depends(dependencies.user_only),
    ):

        new_reply = replies_models.Reply(
            **payload.model_dump(),
            # - title / description  model_dump()는 받아온 title과 description을 각각의 객체로 나눠줌. exclude 여기서 사실 안해도됨 어짜피 filepath 가 payload에 포함 안돼있음
            creator_id=current_user.id,  # - 작성자의 Foreignkey
            shipment_id=ship_id,
        )

        self.db.add(new_reply)  # INSERT 준비
        await self.db.commit()  # 트랜잭션 커밋(비동기 await)

        # 관계필드까지 모두 미리 조회해서 응답으로 반환

        #  프론트에서 저장후 바로 상세페이지(get)로 리다이렉트 되는데 그곳에서 get이 get에 있는 selectinload 보다 get을 먼저 실행하게되서 오류가남 (트랜잭션이 물리적으로 완전히 반영되기 전에 GET이 먼저 실행)
        result = await self.db.execute(
            select(replies_models.Reply)
            .options(
                selectinload(replies_models.Reply.creator),  # 작성자 정보  # 지역 관계
                selectinload(replies_models.Reply.shipments)
            )
            .where(replies_models.Reply.id == new_reply.id)
        )
        reply_with_relations = result.scalar_one()

        return reply_with_relations  # JSON 직렬화 -> 응답




    async def update_reply(
            self,
            reply_id: int,
            payload: replies_schemas.ReplyUpdate,
            current_user: users_models.User = Depends(dependencies.user_only),
    ):

        reply = await self.db.get(replies_models.Reply, reply_id)
        if not reply:
            raise HTTPException(status_code=404, detail='Reply not found')
        if reply.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="작성자만 수정할 수 있습니다.")

        await self.db.execute(
            update(replies_models.Reply)
            .where(replies_models.Reply.id == reply_id)
            .values(
                **payload.model_dump(exclude_unset=True),
            )
        )

        await self.db.commit()  # 트랜잭션 커밋(비동기 await)

        # 관계필드까지 모두 미리 조회해서 응답으로 반환

        #  프론트에서 저장후 바로 상세페이지(get)로 리다이렉트 되는데 그곳에서 get이 get에 있는 selectinload 보다 get을 먼저 실행하게되서 오류가남 (트랜잭션이 물리적으로 완전히 반영되기 전에 GET이 먼저 실행)
        result = await self.db.execute(
            select(replies_models.Reply)
            .options(
                selectinload(replies_models.Reply.creator),  # 작성자 정보  # 지역 관계
                selectinload(replies_models.Reply.shipments)
            )
            .where(replies_models.Reply.id == reply_id)
        )
        reply_with_relations = result.scalar_one()

        return reply_with_relations  # JSON 직렬화 -> 응답

    async def delete_reply(
            self,
            reply_id: int,
            current_user: users_models.User = Depends(dependencies.user_only),
    ):
        reply = await self.db.get(replies_models.Reply, reply_id)
        if not reply:
            raise HTTPException(status_code=404, detail='Reply not found')
        if reply.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail='작성자만 삭제할 수 있습니다.')
        await self.db.execute(
            delete(replies_models.Reply)
            .where(replies_models.Reply.id == reply_id)
        )

        await self.db.commit()

