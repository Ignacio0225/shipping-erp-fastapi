# app/users/protected.py
# JWT 인증된 사용자만 접근 할 수 있는 보호된 API 라우터(비동기)


from fastapi import APIRouter, Depends

from app.users import users_models
from app.users import users_schemas
from app.users.dependencies import admin_only, staff_only

router = APIRouter() # FastAPI의 라우터 인스턴스 생성 (여기서 경로들을 관리)



# 스태프 전용기능 만들기위함
@router.get('/protected',response_model=users_schemas.UserOut)
async def protected_route(
        current_user:users_models.User = Depends(staff_only)):
    return current_user




# 어드민 페이지를 만들기 위함
@router.get("/admin-only", response_model=users_schemas.UserOut)
async def only_admin_route(current_user: users_models.User = Depends(admin_only)):
    return current_user  # 관리자만 접근 가능