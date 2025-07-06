# app/users/auth.py
# 회원가입, 로그인, JWT 인증 등 사용자 인증 관련 API 라우터 정의

from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI의 핵심 기능들: 라우터, 의존성 주입, 예외 처리
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # OAuth2 인증용(토큰 발급·검증)

from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 DB 세션 타입
from sqlalchemy.future import select  # 비동기용 select 쿼리문
from jose import jwt, JWTError  # JWT 인코딩/디코딩, 에러 처리
from pydantic import ValidationError  # 데이터 검증 에러
from datetime import datetime, timedelta  # 시간 및 시간계산용
from dotenv import load_dotenv  # .env 파일에서 환경 변수 읽어옴
import os  # 표준 라이브러리: 환경 변수 접근

from app import database, utils  # 같은 app 디렉토리의 모듈 import
from app.users import users_models  # users/models.py (DB 테이블/ORM)
from app.users import users_schemas  # users/schemas.py (Pydantic 스키마)

# .env 파일을 불러와서 환경 변수로 등록
load_dotenv()

# 환경변수에서 JWT 관련 값 불러오기
SECRET_KEY = os.getenv('SECRET_KEY')  # JWT 서명을 위한 비밀 키 (.env에서 가져옴, 토큰 위조 방지에 반드시 필요)
ALGORITHM = os.getenv('ALGORITHM')    # JWT 서명 알고리즘 (예: HS256, .env에서 지정)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))  # 토큰 만료시간(분, .env에서 지정)

router = APIRouter()  # FastAPI 라우터 인스턴스 생성

# JWT 토큰 생성 함수
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()  # 원본 딕셔너리를 복사해서 to_encode라는 새 딕셔너리에 저장 (안정성 확보)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta  # 전달된 만료 시간만큼 현재 시간에 더함 (UTC 기준)
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # 만료 시간이 없으면 기본 15분 설정
    to_encode.update({'exp': int(expire.timestamp())})  # JWT 'exp' 필드에 만료 시간을 UNIX timestamp(int) 형태로 추가
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # JWT 토큰을 비밀키와 알고리즘으로 암호화
    return encoded_jwt  # 암호화된 JWT 문자열을 반환

# ========================= 회원가입 API =========================
@router.post("/signup", response_model=users_schemas.UserOut)
async def signup(
        user: users_schemas.UserCreate,  # (email, username, password) 요청 데이터(pydantic 모델로 검증)
        db: AsyncSession = Depends(database.get_db)  # DB 비동기 세션 (의존성 주입)
):
    result = await db.execute(select(users_models.User).where(users_models.User.email == user.email))
    existing_user = result.scalar_one_or_none()  # 이메일 중복 확인
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    hashed_pw = utils.hash_password(user.password)  # 비밀번호 해싱(복호화 불가, 안전하게 저장)
    new_user = users_models.User(username=user.username, email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)  # 새로 생성된 사용자 정보 갱신
    return new_user  # 사용자 정보 반환 (비밀번호는 제외됨)

# ========================= 로그인 API (토큰 반환) =========================
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # FastAPI가 username/password 자동 추출 (x-www-form-urlencoded만 가능)
    db: AsyncSession = Depends(database.get_db)
):
    result = await db.execute(select(users_models.User).where(users_models.User.email == form_data.username))
    db_user = result.scalar_one_or_none()

    if not db_user or not utils.verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(days=7)
    )

    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        secure=False,
        samesite="lax"
    )
    return response

@router.post("/refresh")
async def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token이 없습니다.")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="토큰 오류")
    except (JWTError, ValidationError):
        raise HTTPException(status_code=401, detail="Refresh token이 유효하지 않습니다")

    new_access_token = create_access_token(
        data={"sub": email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    response = JSONResponse({"msg": "logged out"})
    response.delete_cookie("refresh_token")
    return response

# OAuth2 스킴 설정 (토큰이 필요한 API에서 사용)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ========================= JWT 토큰으로부터 사용자 추출 =========================
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(database.get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="인증 정보가 없습니다.")
    except (JWTError, ValidationError):
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다")

    result = await db.execute(select(users_models.User).where(users_models.User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user

# ========================= 내 정보 조회 API =========================
@router.get("/me", response_model=users_schemas.UserOut)
async def read_users_me(current_user: users_models.User = Depends(get_current_user)):
    return current_user
