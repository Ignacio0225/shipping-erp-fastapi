# app/progress_roro/progress_roro_services.py

from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 DB 세션을 위한 import
from sqlalchemy.orm import selectinload  # 관계 테이블을 효율적으로 같이 불러오는 옵션
from sqlalchemy import select, update  # SQL 쿼리문 생성용 import

from fastapi import HTTPException  # FastAPI의 예외처리 (에러 발생 시 클라이언트로 코드/메시지 반환)

from app.progress_detail_roro import progress_detail_roro_models, progress_detail_roro_schemas  # 모델/스키마 import
from app.users import users_models  # 사용자 모델 import

ERROR_NOT_FOUND = 'Progress를 찾을 수 없습니다.'  # 에러 메시지 상수화


class ProgressRoRoServices:
    # 서비스 클래스 생성자 (DB 세션 주입)
    def __init__(self, db: AsyncSession):
        self.db = db  # 인스턴스의 db로 저장

    # [READ] ProgressRoRo 여러 건 조회 (progress_id 기준, 자식까지)
    async def get_progress_roro(self, progress_id: int):
        # ProgressRoRo 테이블에서 progress_id가 일치하는 데이터 조회 쿼리 생성
        base_query = await self.db.execute(
            select(progress_detail_roro_models.ProgressRoRo)
            # creator, progress_detail_roro_detail, progress 관계도 한 번에 select (N+1 쿼리 방지)
            .options(
                selectinload(progress_detail_roro_models.ProgressRoRo.creator),
                selectinload(progress_detail_roro_models.ProgressRoRo.progress)
                .selectinload(progress_detail_roro_models.ProgressRoRo.progress_detail_roro_detail),
            )
            .where(progress_detail_roro_models.ProgressRoRo.progress_id == progress_id)
        )
        base_query = base_query.scalars().all()  # 결과를 리스트로 반환 (여러 개 반환)
        return base_query  # 프론트엔드로 리턴

    # [CREATE] ProgressRoRo(마스터)와 ProgressRoRoDetail(디테일) 생성
    async def create_progress_roro(
            self,
            payload: progress_detail_roro_schemas.ProgressDetailRoRoCreate,  # 클라이언트에서 받은 데이터 (Pydantic 객체)
            current_user: users_models.User,  # 현재 로그인한 유저 정보 (권한/작성자 체크용)
            progress_id: int,  # 상위 progress 연결용 id
    ):

        small = (payload.SMALL or 0) * (payload.BUY_SMALL or 0) # 달러
        s_suv = (payload.S_SUV or 0) * (payload.BUY_S_SUV or 0) # 달러
        suv = (payload.SUV or 0) * (payload.BUY_SUV or 0) # 달러
        rv_cargo = (payload.RV_CARGO or 0) * (payload.BUY_RV_CARGO or 0) # 달러
        special = (payload.SPECIAL or 0) * (payload.BUY_SPECIAL or 0) # 달러
        cbm = (payload.CBM or 0) * (payload.BUY_CBM or 0) # 달러
        other = (payload.HC or 0) + (payload.WFG or 0) + (payload.SECURITY or 0) + (payload.CARRIER or 0) + (
                    (payload.PARTNER_FEE or 0) * (payload.RATE or 0)) # 원화
        pu = ((payload.SELL or 0) - (small + s_suv + suv + rv_cargo + special + cbm)) + (other // (payload.RATE or 0)) - (payload.OTHER or 0)
        pw = ((payload.SELL or 0) - (small + s_suv + suv + rv_cargo + special + cbm)) * (payload.RATE or 0) + other + (
                    payload.OTHER or 0)

        # ProgressRoRo(마스터) 객체 생성, 입력값을 모두 풀어서 넣음 (빈 칸은 자동 제외)
        new_progress = progress_detail_roro_models.ProgressRoRo(
            **payload.model_dump(
                exclude_unset=True,
                exclude={'progress_detail_roro_detail', 'PROFIT_USD', 'PROFIT_KRW'}),
            # 입력받은 필드만 dict로 변환
            PROFIT_USD=pu,
            PROFIT_KRW=pw,
            creator_id=current_user.id,  # 작성자 id 추가
            progress_id=progress_id  # 상위 progress 연결
        )
        self.db.add(new_progress)  # 세션에 마스터 객체 추가 (아직 DB반영X)
        await self.db.flush()  # 실제 DB에 반영(commit 전), id 자동 생성 → 이후 디테일과 연결하려면 id 필요

        # progress_detail_roro_detail(디테일) 배열을 반복, 각각 객체 생성 후 추가
        for detail in payload.progress_detail_roro_detail:
            detail_obj = progress_detail_roro_models.ProgressRoRoDetail(
                **detail.model_dump(exclude_unset=True),  # 입력받은 필드만
                progress_detail_roro_id=new_progress.id  # 마스터 id로 연결
            )
            self.db.add(detail_obj)  # 세션에 디테일 추가

        await self.db.commit()  # 모든 insert를 실제 DB에 저장

        # 새로 저장한 마스터/디테일을 selectinload로 한 번에 모두 다시 불러와서 반환 (프론트엔드 상태 동기화용)
        result = await self.db.execute(
            select(progress_detail_roro_models.ProgressRoRo)
            .options(
                selectinload(progress_detail_roro_models.ProgressRoRo.creator),
                selectinload(progress_detail_roro_models.ProgressRoRo.progress),
                selectinload(progress_detail_roro_models.ProgressRoRo.progress_detail_roro_detail),
            ).where(progress_detail_roro_models.ProgressRoRo.progress_id == progress_id)
        )
        progress_roro = result.scalars().first()  # 리스트로 반환
        return progress_roro

    # [UPDATE/PATCH] ProgressRoRo(마스터) + ProgressRoRoDetail(디테일) 동기화
    async def patch_progress_roro(
            self,
            payload: progress_detail_roro_schemas.ProgressDetailRoRoUpdate,  # 변경할 데이터
            current_user: users_models.User,  # 권한 체크용 유저 정보
            progress_roro_id: int,  # 수정할 ProgressRoRo id
    ):
        # patch_progress_roro 내부에서
        small = (payload.SMALL or 0) * (payload.BUY_SMALL or 0)
        s_suv = (payload.S_SUV or 0) * (payload.BUY_S_SUV or 0)
        suv = (payload.SUV or 0) * (payload.BUY_SUV or 0)
        rv_cargo = (payload.RV_CARGO or 0) * (payload.BUY_RV_CARGO or 0)
        special = (payload.SPECIAL or 0) * (payload.BUY_SPECIAL or 0)
        cbm = (payload.CBM or 0) * (payload.BUY_CBM or 0)
        other = (payload.HC or 0) + (payload.WFG or 0) + (payload.SECURITY or 0) + (payload.CARRIER or 0) + (
                (payload.PARTNER_FEE or 0) * (payload.RATE or 0))
        pu = ((payload.SELL or 0) - (small + s_suv + suv + rv_cargo + special + cbm)) + (
                    other // (payload.RATE or 0)) - (payload.OTHER or 0)
        pw = ((payload.SELL or 0) - (small + s_suv + suv + rv_cargo + special + cbm)) * (payload.RATE or 0) + other + (
                payload.OTHER or 0)

        # 1. 우선 마스터 객체를 DB에서 가져옴
        progress = await self.db.get(progress_detail_roro_models.ProgressRoRo, progress_roro_id)
        if not progress:
            raise HTTPException(status_code=404, detail=ERROR_NOT_FOUND)  # 없으면 404 에러

        if progress.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")  # 작성자만 수정 가능

        # 2. ProgressRoRo(마스터) 필드 먼저 업데이트 (디테일은 제외하고)
        await self.db.execute(
            update(progress_detail_roro_models.ProgressRoRo)
            .where(progress_detail_roro_models.ProgressRoRo.id == progress_roro_id)
            .values(**payload.model_dump(
                exclude_unset=True,
                exclude={'progress_detail_roro_detail', 'PROFIT_USD', 'PROFIT_KRW'}),
                    PROFIT_USD=pu,
                    PROFIT_KRW=pw,
                    )
        )

        # 3. 디테일 동기화
        incoming_ids = set()  # 프론트에서 보낸 id들만 저장 (기존 유지/수정 용도)
        if not payload.progress_detail_roro_detail:
            payload.progress_detail_roro_detail = []  # None이면 빈 배열로

        for detail in payload.progress_detail_roro_detail:
            if detail.id:
                # 이미 DB에 있던 디테일이면 → update
                await self.db.execute(
                    update(progress_detail_roro_models.ProgressRoRoDetail)
                    .where(progress_detail_roro_models.ProgressRoRoDetail.id == detail.id)
                    .values(**detail.model_dump(exclude_unset=True))
                )
                incoming_ids.add(detail.id)  # 유지/수정 id 등록
            else:
                # id가 없으면 신규 추가 (insert)
                new_detail = progress_detail_roro_models.ProgressRoRoDetail(
                    **detail.model_dump(exclude_unset=True),
                    progress_detail_roro_id=progress_roro_id
                )
                self.db.add(new_detail)

        # 4. 삭제: DB에는 있는데, 프론트에 없는 디테일만 삭제 (차대번호 등 실수로 잘못된 행만 삭제됨)
        db_details = await self.db.execute(
            select(progress_detail_roro_models.ProgressRoRoDetail).where(
                progress_detail_roro_models.ProgressRoRoDetail.progress_detail_roro_id == progress_roro_id
            )
        )
        db_details = db_details.scalars().all()
        for db_detail in db_details:
            if db_detail.id not in incoming_ids:
                await self.db.delete(db_detail)  # 프론트에 없는 id면 삭제

        await self.db.commit()  # 모든 변경사항 실제 DB에 반영

        # 5. 갱신된 마스터/디테일을 다시 selectinload로 한 번에 조회 후 반환 (최신 상태 프론트에 동기화)
        result = await self.db.execute(
            select(progress_detail_roro_models.ProgressRoRo).options(
                selectinload(progress_detail_roro_models.ProgressRoRo.creator),
                selectinload(progress_detail_roro_models.ProgressRoRo.progress),
                selectinload(progress_detail_roro_models.ProgressRoRo.progress_detail_roro_detail),
            ).where(progress_detail_roro_models.ProgressRoRo.id == progress_roro_id)
        )
        updated_progress_roro = result.scalars().first()  # 단일 객체 반환
        return updated_progress_roro  # 프론트엔드로 응답
