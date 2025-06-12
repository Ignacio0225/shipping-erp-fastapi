# main.py
# FastAPI 서버의 기본 진입점


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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



# CORS 설정 (프론트엔드 호스트와 연결)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 또는 ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)


# 기본 루트 API 정의
@app.get('/')
def read_root():
    return {'message':'Hello from FastAPI!'}


