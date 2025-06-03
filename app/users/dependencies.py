# app/users/dependencies.py

from fastapi import Depends, HTTPException

from . import users_models
from . import auth


async def admin_only(current_user:users_models.User = Depends(auth.get_current_user)):
    if current_user.role !='admin':
        raise HTTPException(status_code=403,detail='관리자 권한이 필요합니다.')
    return current_user

async def staff_only(current_user:users_models.User = Depends(auth.get_current_user)):
    if current_user.role not in('staff','admin'):
        raise HTTPException(status_code=403,detail='스태프 권한이 필요합니다.')
    return current_user

async def user_only(current_user:users_models.User = Depends(auth.get_current_user)):
    if current_user.role not in ('user','staff','admin'):
        raise HTTPException(status_code=403,detail='스태프 또는 관리자 권한 필요합니다.')
    return current_user



# 권한이 많아지면 이런식으로 사용 가능

# def require_roles(*allowed: str):
#     async def checker(user: models.User = Depends(auth.get_current_user)):
#         if user.role not in allowed:
#             raise HTTPException(403, "접근 권한이 없습니다.")
#         return user
#     return checker
#
# admin_only  = require_roles("admin")
# staff_only  = require_roles("admin", "staff")
# user_only   = require_roles("user",'staff','admin')
