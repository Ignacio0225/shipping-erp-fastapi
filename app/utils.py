# app/utils.py
# 비밀번호를 암호화(해시)하고, 비교할 수 있는 유틸 함수

from passlib.context import CryptContext

# bcrypt 해싱 알고리즘을 사용할 수 있도록 설정
# 'CryptContext`는 여러 암호화 알고리즘을 쉽게 쓸 수 있게 도와주는 도구(여기서는 `bcrypt`만 사용)
# `deprecated="auto"`는 자동으로 안전한 알고리즘만 사용
pwd_context = CryptContext(schemes=['bcrypt'],deprecated='auto')

# 비밀번호 해시 생성 함수 ,`bcrypt`로 암호화된 해시 문자열로 변환(예:  "1234" → "$2b$12$aIfgJ3G...")
def hash_password(password:str)->str:
    # .hash 메서드로 비밀번호를 해시화 함
    return pwd_context.hash(password)

# 입력한 비밀번호와 저장된 해시를 비교하는 함수 , 평문 비밀번호와 해시된 값을 비교해서  같은 비밀번호인지 확인
def verify_password(plain_password:str, hashed_password:str)->bool:
    # .verify 메서드가 비밀번호, 해시비밀번호를 비교해서 논리값으로 반환
    return pwd_context.verify(plain_password,hashed_password)