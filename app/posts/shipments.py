# app/posts/shipments.py
import math  # 수학 함수(ceil 등) 사용을 위해 import
import shutil, os  # 파일 복사/삭제(shutil), 경로 생성/조작(os)용 모듈
import uuid  # 파일명 유니크하게 할 때 사용하는 UUID 생성기

from typing import Optional  # 파라미터/타입 어노테이션에 Optional 사용

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, responses, \
    Query  # FastAPI 관련 각종 import (의존성, 파일업로드, 예외처리, 응답 등)
from pathlib import Path  # 파일 경로 객체로 변환, exists 체크용
from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 SQLAlchemy 세션
from sqlalchemy import select, update, delete, func, or_  # SQL 쿼리 빌더, 함수, OR 검색 등
from sqlalchemy.orm import selectinload  # 관계형 데이터 JOIN/프리패치용

from app.users import users_models, users_schemas  # 사용자 ORM/스키마
from app.posts import shipments_models, Shipment  # 선적 ORM 및 Shipment 엔티티
from app.posts import shipments_schemas  # 선적 스키마
from app import database  # DB 세션 의존성
from app.users import dependencies  # 로그인/권한 의존성

router = APIRouter(
    prefix='/api/posts',  # URL 공통 접두사 shipments 뒤로 나오는것에대한것
    tags=['Shipments'],  # Swagger 그룹 이름
)

UPLOAD_DIR = 'public'  # 원하는 폴더로 변경 가능


# 전체 포스트 리스트 조회 가능 (페이지네이션기능포함) (로그인된 모든 사용자)
# 전체 포스트 리스트 조회 가능 (모든 게시글 한 번에 반환)
@router.get('/shipments', response_model=shipments_schemas.ShipmentsPageOut)
async def list_shipment(
        page: int = 1,  # page 를 기본값을 1을줌
        size: int = 10,  # 리스트 사이즈를 10개를줌
        search: Optional[str] = None,
        db: AsyncSession = Depends(database.get_db),
        _: users_models.User = Depends(dependencies.user_only)  # 로그인 확인
):
    # 파라미터 방어(음수/0 등) - 장고처럼 ValueError만큼 유연하지 않음(숫자 아닌 값 오면 FastAPI가 422로 막음)
    if page < 1:  # page가 1보다 작으면
        page = 1  # 다시 page 를 0으로 만들어버림 음수나 0일 들어와버릴경우 페이지 에서 422가 나옴 그래서 방어

    if size < 1:  # 리스트가 9개 8 개 7개 올수도 있음 하지만 음수나 0이 나오면 다시 10으로 만들어버림
        size = 10
    offset = (page - 1) * size  # OFFSET 계산(몇 개를 건너뛸지)

    # page = 1  * size → offset = 0 1번째 페이지일 경우 0번부터 9번 게시글

    # page = 2 * size → offset = 10  2번째 페이지일 경우 10번부터 19번 게시글

    # page = 3 * size  → offset = 20 3번째 페이지일 경우 20번부터 29번 게시글

    # offset = 건너뛸 개수를 의미함 페이지가 2면 page -1  =  1 * 10 이니까 10번 전까지 건너뛰고 시작 한다는듯 (결국 시작 위치를 의미함)

    base_query = select(shipments_models.Shipment)  # 선적(게시글) 전체 SELECT 쿼리 생성

    # 검색어 있을 때만 필터링
    if search:  # 프론트엔드 파라미터에서 search 한 문자열을 받아옴
        # 제목 또는 설명에 검색어 포함된 데이터만!
        base_query = base_query.where(
            or_(  # SQL or 을 쓰는 방법, 파이썬 or을 쓰면 True/False 로 반환 or_ = 둘중하나라도 있으면 이라는의미
                shipments_models.Shipment.title.ilike(f"%{search}%"),  # 타이틀에서 검색어를 찾아옴
                shipments_models.Shipment.description.ilike(f"%{search}%"),  # 디스크립션에서 검색어를 찾아옴
                func.array_to_string(shipments_models.Shipment.file_paths, ',').ilike(f"%{search}%")  # 배열검색 방법
            )
        )  # search가 없으면, 위 조건문을 건너뜀!

    # → 모든 게시글을 최신순으로 페이지네이션해서 반환
    base_query = base_query.order_by(
        shipments_models.Shipment.created_at.desc()
    ).offset(offset).limit(size)  # limit = size <-항상 요청한 페이지당 최대 개수만큼만 반환 사이즈는 무조건 10(게시글이 10개만나옴)

    base_query = base_query.options(
        selectinload(shipments_models.Shipment.creator))  # 작성자 정보(creator)를 JOIN 해서 한 번에 가져오도록 설정

    result = await db.execute(base_query)  # 쿼리 실행해서 결과 받아옴

    shipments = result.scalars().all()  # 전체 레코드 가져오기

    items = [
        shipments_schemas.ShipmentOut(
            id=s.id,
            title=s.title,
            description=s.description,
            created_at=s.created_at,
            file_paths=s.file_paths,
            creator=users_schemas.UserOut(
                id=s.creator.id,
                email=s.creator.email,
                role=s.creator.role,
                username=s.creator.username
            )
        )
        for s in shipments  # 모든 shipments(게시글) 객체를 Pydantic 스키마로 변환, 작성자 정보 포함
    ]

    # 검색 조건이 있으면 필터링된 총 개수를 가져옴
    if search:
        total_count_query = select(func.count()).where(
            or_( # SQL or 을 쓰는 방법, 파이썬 or을 쓰면 True/False 로 반환 or_ = 둘중하나라도 있으면 이라는의미
                shipments_models.Shipment.title.ilike(f"%{search}%"),
                shipments_models.Shipment.description.ilike(f"%{search}%"),
                func.array_to_string(shipments_models.Shipment.file_paths, ',').ilike(f"%{search}%")  # 배열검색 방법

            )
        )
    else:
        total_count_query = select(func.count()).select_from(shipments_models.Shipment)
    total_count = await db.scalar(total_count_query)  # 전체 게시글 개수 집계

    return {
        "items": items,  # 실제 데이터 (리스트)
        "total": total_count,  # 전체 게시글 수
        "page": page,  # 현재 페이지
        "size": size,  # 페이지당 게시글 수
        "total_pages": math.ceil(total_count / size)  # ceil 올림 함수 , 전체페이지 수를 계산함.
    }


# 하나의 포스트 조회
@router.get('/shipments/{ship_id}', response_model=shipments_schemas.ShipmentOut)
async def get_shipment(
        ship_id: int,
        db: AsyncSession = Depends(database.get_db),
        _: users_models.User = Depends(dependencies.user_only)
):
    res = await db.get(shipments_models.Shipment, ship_id)  # ship_id로 해당 게시글 단건 조회
    if not res:
        raise HTTPException(status_code=404, detail='shipment not found')  # 없는 경우 404 반환
    return res  # (여기선 작성자 정보까지 제대로 반환하려면 별도 selectinload 필요, 단건 상세라면 추가로 구현해도 됨)


# 스태프 이상만 생성 (파일업로드 기능도)
@router.post('/shipments/', response_model=shipments_schemas.ShipmentOut, status_code=201)
async def create_shipment(
        title: str = Form(...),  # 파일 업로드 때문에 따로 Form 으로 설정 (multipart/form-data 형식, json 아님)
        description: str = Form(...),  # 파일 업로드 때문에 따로 Form 으로 설정 (multipart/form-data 형식, json 아님)
        files: list[UploadFile] = File(None),  # 파일이 없는 경우 대비. 기본값은 None입니다. 여러개 업로드
        db: AsyncSession = Depends(database.get_db),
        current_user: users_models.User = Depends(dependencies.staff_only),
):
    payload = shipments_schemas.ShipmentCreate(title=title, description=description)  # 입력값을 Pydantic 모델로 생성

    file_paths = None  # 파일이 없을 때 None(Null)로 저장

    if files:  # 파일이 첨부된 경우에만 아래의 코드 실행
        os.makedirs(UPLOAD_DIR, exist_ok=True)  # 업로드 폴더 없으면 새로 만듦

        new_file_paths = []  # 저장할 파일 경로들 담을 리스트

        for file in files:
            os.makedirs(UPLOAD_DIR, exist_ok=True)  # `UPLOAD_DIR = public` 폴더가 없으면 자동으로 만들어 줍니다, 이미 존재하면 그냥 넘어감.
            saved_path = os.path.join(UPLOAD_DIR,f"{uuid.uuid4()}_{file.filename}")  # 실제 저장할 파일 경로 생성, 예: `UPLOAD_DIR = public/sample.pdf`, uuid로 unique 하게 만들어줌
            with open(saved_path, 'wb') as buffer:  # 파일 저장용 스트림 열기(열어야 내용물을 알수 있기 때문) (해당 파일을 buffer라고 부르기로 약속)
                shutil.copyfileobj(file.file, buffer)  # 읽어놓은 파일을 통째로 복사해서 저장, `file.file`은 `SpooledTemporaryFile` 객체임 (stream 기반)
            new_file_paths.append(saved_path)  # 저장한 경로 리스트에 추가
        file_paths = new_file_paths  # 최종 저장 경로 리스트로 교체

    new_ship = shipments_models.Shipment(
        **payload.model_dump(exclude={'file_paths'}),  # - title / description  model_dump()는 받아온 title과 description을 각각의 객체로 나눠줌.
        file_paths=file_paths,
        creator_id=current_user.id  # - 작성자의 Foreignkey
    )
    db.add(new_ship)  # INSERT 준비
    await db.commit()  # 트랜잭션 커밋(비동기 await)
    await db.refresh(new_ship)  # DB가 채워진 PK.시간 재조회
    return new_ship  # JSON 직렬화 -> 응답


# 게시글 수정(작성자 또는 staff)
@router.put('/shipments/{ship_id}', response_model=shipments_schemas.ShipmentOut)
async def update_shipment(
        ship_id: int,
        title: str = Form(None),
        description: str = Form(None),  # 멀티파츠 라서 Form으로 줘야함
        keep_file_paths: list[str] = Form(None),
        new_file_paths: list[UploadFile] = File(None),
        # payload: shipments_schemas.ShipmentUpdate,  # put 이기 때문에 입력된 값을 받아올 수 있음, Form(multipart) 로 설정, 수정안하면 기본값 유지
        db: AsyncSession = Depends(database.get_db),  # 비동기 DB 세션 주입
        _: users_models.User = Depends(dependencies.staff_only),
):
    payload = shipments_schemas.ShipmentUpdate(title=title, description=description)  # 수정 입력값을 Pydantic 모델로

    ship = await db.get(shipments_models.Shipment, ship_id)  # 해당 ID의 게시글(선적) 데이터를 DB에서 가져옴
    if not ship:
        raise HTTPException(404, 'Shipment not found')

    # 1.삭제할 파일들은 서버에서 삭제 기존 파일들을 집합으로 만들어줌 (리스트 해제)
    existing_file_paths = set(ship.file_paths or [])  # 기존 파일 경로 리스트 (예: 파일1,파일2,파일3)

    # 프론트엔드에서 “남길 파일 경로”로 보낸 값들의 집합(set), 예시: {public/uuid_1.pdf, public/uuid_2.xlsx}
    keep_set = set(keep_file_paths)  # 프론트에서 남기려는 파일 경로 리스트 (예: 파일1 만남길것  파일2, 파일3 은 프론트에서 x표시 해놓음)

    # (3) 삭제 대상 파일(= 기존에 있는데 남기지 않은 것)
    delete_file_paths = existing_file_paths - keep_set  # 파일1,파일2,파일3 -(빼기) 파일1   = 파일2, 파일3

    for file_path in delete_file_paths:  # 파일2, 파일3 을 for 문
        if os.path.exists(file_path):  # 파일이 실제로 존재하면 (file_path 는 파일이 아니라 실제 파일 경로 db는 파일을 저장하는게 아니라 경로를 저장 하기 때문)
            os.remove(file_path)  # 실제 파일 삭제

    # 2. 새 파일 저장 , keep_set(남길 파일) 의 집합(set)을 다시 리스트(list)로 변환한 것, SQLAlchemy 등 DB에 저장할 때는 일반적으로 리스트 타입이어야 하기 때문
    file_paths = list(keep_set)  # (삭제 안된) 파일 경로만 리스트로 변환

    if new_file_paths:  # 업로드 된 파일이 있으면
        # 파일이 한 개만 넘어오면 리스트로 감싸줌
        if isinstance(new_file_paths, UploadFile):  # 단일 파일일 때 리스트로 변환
            new_file_paths = [new_file_paths]
        for file in new_file_paths:  # for 문을 돌림
            os.makedirs(UPLOAD_DIR, exist_ok=True)  # 업로드 폴더 없으면 생성
            saved_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")  # 새 파일 저장 경로
            with open(saved_path,'wb') as buffer:  # 새로 만들 파일을 열고 'wb : write binary' 파일을 바이너리로 파일에 써줄 준비를함, 준비하고 buffer라고 부름
                shutil.copyfileobj(file.file, buffer)  # file.file의 첫 file은 for문을 도는 실제 객체 뒷 file은 바이너리 메서드 -> 를 buffer에 써줌
            file_paths.append(saved_path)  # 새 파일 경로 추가

    await db.execute(
        update(shipments_models.Shipment)  # Shipment의 모델 형식으로
        .where(shipments_models.Shipment.id == ship_id)  # Shipment.id 가 ship_id 랑같은것만
        .values(**payload.model_dump(exclude_unset=True), file_paths=file_paths)
        # value 값들로 바꿔 줘 model_dump 는 list 랑같음, exclude_unset=True 이거는 변경된 필드만 반영 한다는것
    )
    await db.commit()  # 트랜잭션 커밋
    await db.refresh(ship)  # 갱신/재조회
    return ship  # 수정된 ship 반환


# 게시글 삭제
@router.delete('/shipments/{ship_id}', status_code=204)
async def delete_shipment(
        ship_id: int,
        db: AsyncSession = Depends(database.get_db),
        _: users_models.User = Depends(dependencies.admin_only),
):
    await db.execute(delete(shipments_models.Shipment).where(shipments_models.Shipment.id == ship_id))  # 삭제 쿼리 실행
    await db.commit()  # 실제 DB 반영


# 파일 다운로드
@router.get(
    '/shipments/{ship_id}/files/{file_index}/download')  # 파일 다운로드는 JSON 형태로 받아오는게 아니기 때문에 response_model을 설정 해줄 핋요 없음
async def download_file(
        ship_id: int,
        file_index: int,  # 파일의 ID가 아니라 여러개 파일을 올려놓은 리스트 의 인덱스 번호로 적용
        db: AsyncSession = Depends(database.get_db),
        _: users_models.User = Depends(dependencies.staff_only),
):
    shipment = await db.get(shipments_models.Shipment, ship_id)  # ship_id로 단일 게시글 조회

    # 해당 게시글 조회
    if not shipment:
        raise HTTPException(status_code=404, detail='shipment not found')  # 없는 경우 예외

    # 인덱스 범위 확인
    try:
        file_path_str = shipment.file_path[file_index]  # 인덱스에 해당하는 파일 경로 추출
        if not file_path_str:  # 빈 문자열 체크
            raise HTTPException(status_code=404, detail='File not found')
    except IndexError:
        raise HTTPException(status_code=404, detail='File index out of range')

    # 파일 존재 여부 확인
    file_path = Path(file_path_str)  # 문자열을 Path 객체로 변환

    if not file_path.exists():  # 파일이 없으면 exists = 유무 확인(True / False)
        raise HTTPException(status_code=404, detail='File not found on server')

    # fastapi.responses.FileResponse = 파일을 다운로드 해주는 패키지 메서드 (파일을 메모리에 한 번에 로드하지 않고 청크(chunk) 단위로 전송, 대용량 파일도 효율적으로 전송 가능)
    return responses.FileResponse(
        path=file_path,
        filename=file_path.name,  # UUID가 포함된 파일명 그대로 사용
        media_type='application/octet-stream'  # 범용 바이너리 파일 타입
    )
