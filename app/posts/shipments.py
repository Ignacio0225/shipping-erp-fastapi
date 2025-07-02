# app/posts/shipments.py
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, UploadFile, File, Form # FastAPI 관련 각종 import (의존성, 파일업로드, 예외처리, 응답 등)

from app.database import get_db
from app.posts import shipments_schemas  # 선적 스키마
from app.posts.shipments_services import ShipmentsServices
from app.users import dependencies
from app.users import users_models


router = APIRouter(
    prefix='/api/posts',  # URL 공통 접두사 shipments 뒤로 나오는것에대한것
    tags=['Shipments'],  # Swagger 그룹 이름
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


def get_services(db:AsyncSession =Depends(get_db)) -> ShipmentsServices:
    return ShipmentsServices(db)


# 전체 포스트 리스트 조회 가능 (페이지네이션기능포함) (로그인된 모든 사용자)
# 전체 포스트 리스트 조회 가능 (모든 게시글 한 번에 반환)
@router.get('/shipments', response_model=shipments_schemas.ShipmentsPageOut, status_code=200)
async def list_shipments(
    page: int = 1,
    size: int = 10,
    type_category: int = None,
    region_category: int = None,
    search: str = None,
    _: users_models.User = Depends(dependencies.user_only),
    service: ShipmentsServices = Depends(get_services), # 의존성 주입으로 비동기 세션 db 생성
):
    return await service.list_shipment(
        page=page,
        size=size,
        type_category=type_category,
        region_category=region_category,
        search=search,
    )

@router.get('/shipments/personal', response_model=shipments_schemas.ShipmentsPageOut, status_code=200)
async def list_shipments_personal(
    page: int = 1,
    size: int = 10,
    type_category: int = None,
    region_category: int = None,
    search: str = None,
    current_user: users_models.User = Depends(dependencies.user_only), # 의존성 주입으로 비동기 세션 db 생성
    service: ShipmentsServices = Depends(get_services),
):
    return await service.list_shipment_personal(
        page=page,
        size=size,
        type_category=type_category,
        region_category=region_category,
        search=search,
        current_user=current_user,
    )

# 하나의 포스트 조회
@router.get('/shipments/{ship_id}', response_model=shipments_schemas.ShipmentOut, status_code=200)
async def get_shipment(
        ship_id:int,
        _:users_models.User = Depends(dependencies.user_only),
        service:ShipmentsServices = Depends(get_services),
):
    return await service.get_shipment(
        ship_id=ship_id
    )
# 스태프 이상만 생성 (파일업로드 기능도)
@router.post('/shipments', response_model=shipments_schemas.ShipmentOut, status_code=201)
async def create_shipment(
        title: str = Form(...),  # 파일 업로드 때문에 따로 Form 으로 설정 (multipart/form-data 형식, json 아님)
        description: str = Form(...),  # 파일 업로드 때문에 따로 Form 으로 설정 (multipart/form-data 형식, json 아님)
        type_category: int = Form(...),
        region_category: int = Form(...),
        files: list[UploadFile] = File(None),  # 파일이 없는 경우 대비. 기본값은 None입니다. 여러개 업로드
        current_user: users_models.User = Depends(dependencies.staff_only),
        service:ShipmentsServices = Depends(get_services), # 의존성 주입으로 비동기 세션 db 생성
    ):
    return await service.create_shipment(
        title=title,
        description=description,
        type_category=type_category,
        region_category=region_category,
        files=files,
        current_user=current_user,
    )

# 게시글 수정 (작성자 또는 staff만 가능)
@router.put('/shipments/{ship_id}', response_model=shipments_schemas.ShipmentOut,status_code=200)  # PUT 요청 시 이 함수 실행, 수정 후 반환 타입은 ShipmentOut 스키마
async def update_shipment(
        ship_id: int,  # URL 경로에서 전달받은 게시글 ID (정수형)
        title: str = Form(None),  # form-data로 전달된 title 값, 없으면 None (수정 안 했다는 뜻)
        description: str = Form(None),  # form-data로 전달된 description 값, 없으면 None
        type_category: int = Form(None),
        region_category: int = Form(None),
        keep_file_paths: list[str] = Form(None),  # 기존 파일 중 유지하고 싶은 파일 경로 리스트 (없으면 전부 삭제로 처리됨)
        new_file_paths: list[UploadFile] = File(None),  # 새로 업로드된 파일들 (없을 수도 있음)
        current_user: users_models.User = Depends(dependencies.staff_only),  # 로그인한 사용자가 staff 권한인지 검사 (아니면 403 에러)
        service:ShipmentsServices=Depends(get_services), # 의존성 주입으로 비동기 세션 db 생성
    ):
        return await service.update_shipment(
            ship_id=ship_id,
            title=title,
            description=description,
            type_category=type_category,
            region_category=region_category,
            keep_file_paths=keep_file_paths,
            new_file_paths=new_file_paths,
            current_user=current_user,

        )

# 게시글 삭제
@router.delete('/shipments/{ship_id}',status_code=204)  # HTTP DELETE 요청을 처리하는 라우터 설정, /shipments/123 같은 URL을 의미하며 응답 상태 코드는 204(No Content)
async def delete_shipment(
        ship_id: int,  # URL 경로에서 전달된 게시글 ID (정수형)
        current_user: users_models.User = Depends(dependencies.admin_only),
        # admin_only 의존성을 통해 관리자 권한 확인, '_'는 이 값을 사용하지 않겠다는 의미
        service:ShipmentsServices=Depends(get_services) # 의존성 주입으로 비동기 세션 db 생성
    ):
        return await service.delete_shipment(
            ship_id=ship_id,
            current_user=current_user,
        )

# 파일 다운로드
@router.get('/shipments/{ship_id}/files/{file_index}/download')  # 파일 다운로드는 JSON 형태로 받아오는게 아니기 때문에 response_model을 설정 해줄 핋요 없음
async def download_file(
        ship_id: int,
        file_index: int,  # 파일의 ID가 아니라 여러개 파일을 올려놓은 리스트 의 인덱스 번호로 적용
        _: users_models.User = Depends(dependencies.user_only),
        service:ShipmentsServices=Depends(get_services) # 의존성 주입으로 비동기 세션 db 생성
    ):
        return await service.download_file(
            ship_id=ship_id,
            file_index=file_index,
        )