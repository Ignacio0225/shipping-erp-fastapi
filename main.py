# main.py
# FastAPI 서버의 기본 진입점


from fastapi import FastAPI
from app.users.auth import router as auth_router
from app.users.protected import router as protected_router
from app.posts.shipments import router as shipment_router

# 아래 코드: models.py의 모든 모델을 실제 DB 테이블로 생성 / 비동기에선 쓰지 않음
# models.Base.metadata.create_all(bind=engine)


# FastAPI 인스턴스 생성
app = FastAPI()
app.include_router(auth_router)
app.include_router(protected_router)

app.include_router(shipment_router)

# 기본 루트 API 정의
@app.get('/')
def read_root():
    return {'message':'Hello from FastAPI!ㅃ'}


