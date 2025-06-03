# app/users/schemas.py
# API 요청과 응답에 사용될 Pydantic 모델을 정의하는 파일

from pydantic import BaseModel, EmailStr

# 회원가입 시 사용할 요청 모델 (예: 브라우져에서 값을 입력하고 회원가입 버튼을 누르면 BaseModel을 통해 Json으로 보내온 데이터를 파싱하고 유효성검사 하여 받아옴)
class UserCreate(BaseModel):
    username:str
    email: EmailStr
    password: str # 사용자가 입력하는 원본 비밀번호

# 사용자 정보 응답 모델 (비밀번호 제외) (예: 유저정보를 보려할때 데이터베이스에서 밖으로(브라우져로) 보낼때 사용하는 데이터 구조)
class UserOut(BaseModel): # Out은 '응답'을 의미
    id:int
    username:str
    email:EmailStr # poetry add 'pydantic[email]' 의존성 설치 해야함
    role:str

    # `User`라는 파이썬 객체를 (ORM) → JSON 응답으로 바꾸는 걸 **자동화** 해줌
    class Config:
        from_attributes = True # SQLAlchemy 모델과 호환되도록 설정