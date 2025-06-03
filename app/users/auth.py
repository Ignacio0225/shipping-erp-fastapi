# app/users/auth.py
# 회원가입, 로그인 기능 및 JWT 토큰 발급을 처리하는 API 라우터


from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI의 핵심 기능들: 라우터, 의존성 주입, 예외 처리
from fastapi.security import OAuth2PasswordBearer  # OAuth2 방식의 인증 처리기
from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 세션
# from sqlalchemy.orm import Session  # SQLAlchemy의 DB 세션 타입(동기)
from sqlalchemy.future import select  # SQL 쿼리문을 비동기로 작성
from jose import jwt, JWTError  # JWT 토큰 생성 및 디코딩
from pydantic import ValidationError  # Pydantic 모델 검증 에러 처리
from datetime import datetime, timedelta  # 현재 시간 및 시간 연산용
from dotenv import load_dotenv  # .env 파일을 읽어오는 라이브러리
import os  # 환경변수를 가져오기 위한 표준 라이브러리


from app import database, utils  # 같은 app 디렉토리 안의 파일들 불러오기
from app.users import users_models
from app.users import users_schemas
# .env 파일 불러오기
load_dotenv()  # .env 파일에 저장된 설정값들을 환경변수로 로딩

# 환경변수 사용 (.env 의 설정을 가져오는 것)
SECRET_KEY = os.getenv('SECRET_KEY')  # JWT 서명을 위한 비밀 키
ALGORITHM = os.getenv('ALGORITHM')  # JWT 서명 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))  # 토큰 만료 시간(분)

router = APIRouter()  # FastAPI의 라우터 인스턴스 생성 (여기서 경로들을 관리)


# SQLAlchemy에서 Session이란
# "데이터베이스에 연결되어 있는 작업 공간"입니다.
# → 데이터를 조회하고, 추가하고, 수정하고, 삭제하는 모든 작업의 단위


# JWT 액세스 토큰 생성 함수
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()  # 입력 데이터를 복사해 수정, 원본데이터를 직접 수정하지 않기 위해

    if expires_delta:
        expire = datetime.utcnow() + expires_delta  # 전달된 만료 시간 사용
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # 기본 만료 시간 15분

    to_encode.update({'exp': expire})  # 토큰에 만료 시간 추가
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # JWT 토큰 생성 (encode : 암호화)
    return encoded_jwt



# 회원가입 API (비동기)
@router.post("/signup", response_model=users_schemas.UserOut)
async def signup(
        user: users_schemas.UserCreate,
        db: AsyncSession = Depends(database.get_db)
):
    result = await db.execute(select(users_models.User).where(users_models.User.email == user.email))  # 이메일 존재 여부 확인, where 에서 email을 찾고 select로 선택
    existing_user = result.scalar_one_or_none() # 결과가 정확히 하나면 그 값을 리턴, 결과가 없으면 None 리턴, 결과가 여러 개면 에러 발생 (MultipleResultsFound)
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    hashed_pw = utils.hash_password(user.password)  # 비밀번호 해시화
    new_user = users_models.User(username=user.username, email=user.email, hashed_password=hashed_pw)
    db.add(new_user)  # 세션에 추가
    await db.commit()  # 커밋
    await db.refresh(new_user)  # 객체 갱신 (id 값 등)
    return new_user  # 응답 반환



# 로그인 API (비동기)
@router.post("/login")
async def login(
        user: users_schemas.UserCreate,
        db: AsyncSession = Depends(database.get_db)
):
    result = await db.execute(select(users_models.User).where(users_models.User.email == user.email))
    db_user = result.scalar_one_or_none()  # 유저 검색
    if not db_user or not utils.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}  # 토큰 반환



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")  # 로그인 URL을 통해 토큰을 발급받도록 설정


# 현재 로그인한 사용자 가져오기 (비동기)
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(database.get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # 토큰 복호화
        email: str = payload.get("sub") # 인증을 위해 email로 지정
        if email is None:
            raise HTTPException(status_code=401, detail="인증 정보가 없습니다.")
    except (JWTError, ValidationError):
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다")

    result = await db.execute(select(users_models.User).where(users_models.User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user

# 현재 로그인한 사용자 정보 조회 API
@router.get("/me", response_model=users_schemas.UserOut)
# models.User는 타입을 의미함
async def read_users_me(current_user: users_models.User = Depends(get_current_user)):
    return current_user
