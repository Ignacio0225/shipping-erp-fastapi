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

from app.region_categories import region_categories_schemas
from app.type_categories import type_categories_schemas
from app.users import users_models, users_schemas  # 사용자 ORM/스키마
from app.posts import shipments_models  # 선적 ORM 및 Shipment 엔티티
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
@router.get('/shipments', response_model=shipments_schemas.ShipmentsPageOut, status_code=200)
async def list_shipment(
        page: int = 1,  # page 를 기본값을 1을줌
        size: int = 10,  # 리스트 사이즈를 10개를줌
        search: Optional[str] = None,
        db: AsyncSession = Depends(database.get_db),
        _: users_models.User = Depends(dependencies.user_only)  # 로그인 확인
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
        selectinload(shipments_models.Shipment.creator),
        selectinload(shipments_models.Shipment.type_category),
        selectinload(shipments_models.Shipment.region_category),
    )  # 작성자 정보(creator), 카테고리 등을 JOIN 해서 한 번에 가져오도록 설정

    result = await db.execute(base_query)  # 쿼리 실행해서 결과 받아옴

    shipments = result.scalars().all()  # 전체 레코드 가져오기

    items = [
        shipments_schemas.ShipmentOut(
            id=s.id,
            title=s.title,
            description=s.description,
            created_at=s.created_at,
            updated_at=s.updated_at,
            type_category=type_categories_schemas.CategoryOut(
                id=s.id,
                title=s.title,
                creator=s.creator,
            ),
            region_category=region_categories_schemas.CategoryOut(
                id=s.id,
                title=s.title,
                creator=s.creator,
            ),
            file_paths=s.file_paths,
            creator=users_schemas.UserOut(
                id=s.creator.id,
                email=s.creator.email,
                role=s.creator.role,
                username=s.creator.username,
            )
        )
        for s in shipments  # 모든 shipments(게시글) 객체를 Pydantic 스키마로 변환, 작성자 정보 포함
        # squares = [x * x for x in range(5)] <- 리스트 내포 표현식
        # 결과: [0, 1, 4, 9, 16]
    ]

    # 검색 조건이 있으면 필터링된 총 개수를 가져옴
    if search:
        total_count_query = select(func.count()).where(
            or_(  # SQL or 을 쓰는 방법, 파이썬 or을 쓰면 True/False 로 반환 or_ = 둘중하나라도 있으면 이라는의미
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
@router.get('/shipments/{ship_id}', response_model=shipments_schemas.ShipmentOut, status_code=200)
async def get_shipment(
        ship_id: int,
        db: AsyncSession = Depends(database.get_db),
        _: users_models.User = Depends(dependencies.user_only)
):
    base_query = select(shipments_models.Shipment)

    result = await db.execute(
        base_query.options(
        selectinload(shipments_models.Shipment.creator),
        selectinload(shipments_models.Shipment.type_category),
        selectinload(shipments_models.Shipment.region_category),
        ).where(shipments_models.Shipment.id == ship_id)
    )  # ship_id로 해당 게시글 단건 조회
    res = result.scalars().first()
    if not res:
        raise HTTPException(status_code=404, detail='shipment not found')  # 없는 경우 404 반환
    return res  # (여기선 작성자 정보까지 제대로 반환하려면 별도 selectinload 필요, 단건 상세라면 추가로 구현해도 됨)


# 스태프 이상만 생성 (파일업로드 기능도)
@router.post('/shipments/', response_model=shipments_schemas.ShipmentOut, status_code=201)
async def create_shipment(
        title: str = Form(...),  # 파일 업로드 때문에 따로 Form 으로 설정 (multipart/form-data 형식, json 아님)
        description: str = Form(...),  # 파일 업로드 때문에 따로 Form 으로 설정 (multipart/form-data 형식, json 아님)
        type_category: int = Form(...),
        region_category:int = Form(...),
        files: list[UploadFile] = File(None),  # 파일이 없는 경우 대비. 기본값은 None입니다. 여러개 업로드
        db: AsyncSession = Depends(database.get_db),
        current_user: users_models.User = Depends(dependencies.staff_only),
):
    payload = shipments_schemas.ShipmentCreate(
        title=title,
        description=description,
    )  # 입력값을 Pydantic 모델로 생성

    file_paths = None  # 파일이 없을 때 None(Null)로 저장

    if files:  # 파일이 첨부된 경우에만 아래의 코드 실행
        os.makedirs(UPLOAD_DIR, exist_ok=True)  # 업로드 폴더 없으면 새로 만듦

        new_file_paths = []  # 저장할 파일 경로들 담을 리스트

        for file in files:
            os.makedirs(UPLOAD_DIR, exist_ok=True)  # `UPLOAD_DIR = public` 폴더가 없으면 자동으로 만들어 줍니다, 이미 존재하면 그냥 넘어감.
            saved_path = os.path.join(UPLOAD_DIR,f"{uuid.uuid4()}_{file.filename}")  # 실제 저장할 파일 경로 생성, 예: `UPLOAD_DIR = public/sample.pdf`, uuid로 unique 하게 만들어줌
            with open(saved_path, 'wb') as buffer:  # 파일 저장용 스트림 열기(열어야 내용물을 알수 있기 때문) (해당 파일을 buffer라고 부르기로 약속)
                shutil.copyfileobj(file.file,buffer)  # 읽어놓은 파일을 통째로 복사해서 저장, `file.file`은 `SpooledTemporaryFile` 객체임 (stream 기반)
            new_file_paths.append(saved_path)  # 저장한 경로 리스트에 추가
        file_paths = new_file_paths  # 최종 저장 경로 리스트로 교체

    new_ship = shipments_models.Shipment(
        **payload.model_dump(exclude={'file_paths'}),
        # - title / description  model_dump()는 받아온 title과 description을 각각의 객체로 나눠줌. exclude 여기서 사실 안해도됨 어짜피 filepath 가 payload에 포함 안돼있음
        file_paths=file_paths,
        creator_id=current_user.id,  # - 작성자의 Foreignkey
        type_category_id=type_category,
        region_category_id=region_category,
    )

    db.add(new_ship)  # INSERT 준비
    await db.commit()  # 트랜잭션 커밋(비동기 await)
    await db.refresh(new_ship)  # DB가 채워진 PK.시간 재조회
    # 관계필드까지 모두 미리 조회해서 응답으로 반환

    #  프론트에서 저장후 바로 상세페이지(get)로 리다이렉트 되는데 그곳에서 get이 get에 있는 selectinload 보다 get을 먼저 실행하게되서 오류가남 (트랜잭션이 물리적으로 완전히 반영되기 전에 GET이 먼저 실행)
    result = await db.execute(
        select(shipments_models.Shipment)
        .options(
            selectinload(shipments_models.Shipment.creator),  # 작성자 정보
            selectinload(shipments_models.Shipment.type_category),  # 카테고리 관계
            selectinload(shipments_models.Shipment.region_category),  # 지역 관계
        )
        .where(shipments_models.Shipment.id == new_ship.id)
    )
    ship_with_relations = result.scalar_one()

    return ship_with_relations # JSON 직렬화 -> 응답



# 게시글 수정 (작성자 또는 staff만 가능)
@router.put('/shipments/{ship_id}', response_model=shipments_schemas.ShipmentOut,
            status_code=200)  # PUT 요청 시 이 함수 실행, 수정 후 반환 타입은 ShipmentOut 스키마
async def update_shipment(
        ship_id: int,  # URL 경로에서 전달받은 게시글 ID (정수형)
        title: str = Form(None),  # form-data로 전달된 title 값, 없으면 None (수정 안 했다는 뜻)
        description: str = Form(None),  # form-data로 전달된 description 값, 없으면 None
        type_category: int = Form(None),
        region_category:int = Form(None),
        keep_file_paths: list[str] = Form(None),  # 기존 파일 중 유지하고 싶은 파일 경로 리스트 (없으면 전부 삭제로 처리됨)
        new_file_paths: list[UploadFile] = File(None),  # 새로 업로드된 파일들 (없을 수도 있음)
        db: AsyncSession = Depends(database.get_db),  # 비동기 DB 세션을 의존성으로 주입받음 (get_db 함수에서 생성됨)
        current_user: users_models.User = Depends(dependencies.staff_only),  # 로그인한 사용자가 staff 권한인지 검사 (아니면 403 에러)
):
    shipment = await db.get(shipments_models.Shipment, ship_id)  # DB에서 Shipment 테이블에서 해당 ID의 게시글 1개 조회 (없으면 None 반환)
    if not shipment:  # 조회 결과가 없다면
        raise HTTPException(404, 'Shipment not found')  # 404 Not Found 에러 발생

    if shipment.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="작성자만 수정할 수 있습니다.")

    payload = shipments_schemas.ShipmentUpdate(
        title=title,
        description=description,
        type_category_id=type_category,
        region_category_id=region_category,
    )  # 수정할 데이터(title, description)를 Pydantic 모델로 감쌈 (None 값 포함 가능)

    existing_paths = set(shipment.file_paths or [])  # 기존에 저장된 파일 경로 리스트를 집합(set)으로 변환 (없을 경우 빈 집합)
    keep_paths = set(keep_file_paths or [])  # 프론트엔드에서 전달받은 유지할 파일 경로 리스트를 집합으로 변환 (없으면 빈 집합)
    delete_paths = existing_paths - keep_paths  # 기존 파일 중 유지하지 않는 것만 남김 (삭제 대상)

    for path in delete_paths:  # 삭제 대상 파일들을 하나씩 순회
        if os.path.exists(path):  # 파일이 실제 디스크에 존재하는지 확인
            os.remove(path)  # 존재하면 파일 삭제 (os.remove는 물리적 삭제, 복구 불가)

    saved_paths = []  # 새로 저장한 파일 경로를 저장할 리스트 (에러 시 롤백용으로 사용)

    file_paths = list(keep_paths)  # 최종적으로 DB에 저장할 파일 경로 리스트 (유지할 파일들로 초기화)

    try:
        if new_file_paths:  # 새로 업로드된 파일이 있는 경우
            os.makedirs(UPLOAD_DIR, exist_ok=True)  # 업로드 디렉토리가 없으면 생성 (기존에 있으면 생략)
            for file in new_file_paths:  # 새 파일 리스트를 하나씩 반복
                save_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")  # 고유한 파일명을 만들기 위해 UUID를 앞에 붙임

                with open(save_path, 'wb') as buffer:  # 새 파일을 바이너리 쓰기 모드로 열고 buffer라는 변수명으로 사용
                    shutil.copyfileobj(file.file, buffer)  # UploadFile 객체에서 파일을 읽어서 buffer에 씀 (실제 파일 저장)

                file_paths.append(save_path)  # 저장된 경로를 DB 저장용 리스트에 추가
                saved_paths.append(save_path)  # 롤백을 위해 따로 기록해둠

        await db.execute(  # DB에서 UPDATE 쿼리 실행 (비동기 방식)
            update(shipments_models.Shipment)  # shipments 테이블을 대상으로 업데이트 수행
            .where(shipments_models.Shipment.id == ship_id)  # 해당 ID의 행만 업데이트
            .values(
                **payload.model_dump(exclude_unset=True),  # title, description 중 변경된 값만 포함 (None은 제외)
                file_paths=file_paths,  # 파일 경로는 무조건 새 리스트로 덮어씀 (기존 파일 유지 + 새 파일 포함)
            )
        )
        await db.commit()  # 트랜잭션 커밋 → 지금까지의 변경 사항을 실제 DB에 반영
        await db.refresh(shipment)  # shipment 객체를 최신 상태로 다시 불러옴 (commit 후 갱신)

        put_result = await db.execute(
            select(shipments_models.Shipment)
            .options(
                selectinload(shipments_models.Shipment.creator),
                selectinload(shipments_models.Shipment.type_category),
                selectinload(shipments_models.Shipment.region_category),
            )
            .where(shipments_models.Shipment.id == shipment.id)
        )
        ship_with_relations_put = put_result.scalar_one()
        return ship_with_relations_put  # 최종적으로 수정된 게시글 데이터를 반환

    except Exception as e:  # 파일 저장 or DB 작업 중 에러 발생 시
        for path in saved_paths:  # 새로 저장했던 파일들 중
            if os.path.exists(path):  # 존재하는 파일만
                os.remove(path)  # 디스크에서 삭제 (롤백)

        raise HTTPException(500, f"수정 중 오류 발생: {str(e)}")  # HTTP 500 에러와 함께 에러 메시지 반환


# 게시글 삭제
@router.delete('/shipments/{ship_id}',status_code=204)  # HTTP DELETE 요청을 처리하는 라우터 설정, /shipments/123 같은 URL을 의미하며 응답 상태 코드는 204(No Content)
async def delete_shipment(
        ship_id: int,  # URL 경로에서 전달된 게시글 ID (정수형)
        db: AsyncSession = Depends(database.get_db),  # DB 세션을 비동기로 의존성 주입 (get_db 함수로부터 AsyncSession 객체를 받아옴)
        current_user: users_models.User = Depends(dependencies.admin_only),
        # admin_only 의존성을 통해 관리자 권한 확인, '_'는 이 값을 사용하지 않겠다는 의미
):
    shipment = await db.get(shipments_models.Shipment,
                            ship_id)  # DB에서 Shipment 테이블의 기본키가 ship_id인 레코드를 조회함 (없으면 None 반환)

    if not shipment:  # shipment가 None이면 → 존재하지 않는 게시글
        raise HTTPException(404, "Shipment not found")  # HTTP 404 에러 발생 (게시글을 찾을 수 없음)

    if shipment.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="작성자만 삭제할 수 있습니다.")

    # 파일 삭제
    for path in shipment.file_paths or []:  # 게시글에 연결된 파일 경로들 반복 (file_paths가 None이면 빈 리스트로 대체)
        if os.path.exists(path):  # 서버 파일 시스템에 해당 경로의 파일이 실제로 존재하는지 확인
            os.remove(path)  # 해당 경로의 파일을 실제로 삭제 (os.remove는 물리적으로 영구 삭제함)

    # DB 행 삭제
    await db.execute(  # 비동기 DB 세션에서 SQL 실행
        delete(shipments_models.Shipment)  # SQL DELETE 구문 생성: DELETE FROM shipments
        .where(shipments_models.Shipment.id == ship_id)  # 조건절: WHERE id = ship_id
    )
    await db.commit()  # 트랜잭션 커밋 → 실제로 DB에서 삭제가 반영됨


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
        file_path_str = shipment.file_paths[file_index]  # 인덱스에 해당하는 파일 경로 추출
        if not file_path_str:  # 빈 문자열 체크
            raise HTTPException(status_code=404, detail='File not found')
    except IndexError:
        raise HTTPException(status_code=404, detail='파일 인덱스가 파일리스트 길이를 벗어남')

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
