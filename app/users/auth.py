# app/users/auth.py
# 회원가입, 로그인, JWT 인증 등 사용자 인증 관련 API 라우터 정의

from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI의 핵심 기능들: 라우터, 의존성 주입, 예외 처리
from fastapi.security import OAuth2PasswordBearer  # OAuth2 인증용(토큰 발급·검증)
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
SECRET_KEY = os.getenv('SECRET_KEY')  # JWT 서명을 위한 비밀 키
ALGORITHM = os.getenv('ALGORITHM')    # JWT 서명 알고리즘 (예: HS256)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))  # 토큰 만료시간(분)

router = APIRouter()  # FastAPI 라우터 인스턴스 생성

# JWT 토큰 생성 함수
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()  # 원본 수정 방지용 복사
    if expires_delta:
        expire = datetime.utcnow() + expires_delta  # 전달된 만료시간 적용
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # 기본 15분 만료
    to_encode.update({'exp': expire})  # 만료 시간 추가
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # JWT 토큰 생성
    return encoded_jwt  # 인코딩된 JWT 문자열 반환

# ========================= 회원가입 API =========================
@router.post("/signup", response_model=users_schemas.UserOut)
async def signup(
        user: users_schemas.UserCreate,  # (email, username, password)
        db: AsyncSession = Depends(database.get_db)
):
    # 이메일 중복 체크
    result = await db.execute(select(users_models.User).where(users_models.User.email == user.email))
    existing_user = result.scalar_one_or_none()  # 이미 있으면 반환, 없으면 None
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    hashed_pw = utils.hash_password(user.password)  # 비밀번호 해싱
    # 새 사용자 객체 생성 (비밀번호는 해시 값으로 저장)
    new_user = users_models.User(username=user.username, email=user.email, hashed_password=hashed_pw)
    db.add(new_user)       # 세션에 추가
    await db.commit()      # DB에 반영
    await db.refresh(new_user)  # PK 등 자동값 재조회
    return new_user        # 사용자 정보 반환

# ========================= 로그인 API (토큰 반환) =========================
@router.post("/login")
async def login(
        user: users_schemas.UserCreate,  # (email, password)
        db: AsyncSession = Depends(database.get_db)
):
    # email로 사용자 조회
    result = await db.execute(select(users_models.User).where(users_models.User.email == user.email))
    db_user = result.scalar_one_or_none()
    # 사용자가 없거나 비밀번호 불일치시 예외 발생
    if not db_user or not utils.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    # JWT 토큰 생성, 데이터는 {"sub": db_user.email}
    access_token = create_access_token(
        data={"sub": db_user.email},  # sub는 토큰의 subject(이 토큰이 누구 것인지), 여기서는 email을 고유값으로 사용
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}  # 토큰 반환

# OAuth2 방식: 토큰이 필요한 API에서 토큰을 추출하는 역할
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")  # /login에서 토큰 발급

# ========================= JWT 토큰 → 현재 사용자 추출 =========================
async def get_current_user(
        token: str = Depends(oauth2_scheme),  # 요청의 Authorization 헤더에서 토큰을 자동 추출
        db: AsyncSession = Depends(database.get_db)
):
    try:
        # 토큰 디코딩
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")  # sub 필드에서 email 꺼냄
        if email is None:
            raise HTTPException(status_code=401, detail="인증 정보가 없습니다.")
    except (JWTError, ValidationError):
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다")

    # 토큰에서 추출한 email로 사용자 DB 조회
    result = await db.execute(select(users_models.User).where(users_models.User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user  # DB의 사용자 객체 반환

# ========================= 내 정보 확인 API (토큰 인증 필요) =========================
@router.get("/me", response_model=users_schemas.UserOut)
async def read_users_me(current_user: users_models.User = Depends(get_current_user)):
    return current_user

