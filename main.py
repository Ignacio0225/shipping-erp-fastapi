# main.py
# FastAPI 서버의 기본 진입점


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.users.auth import router as auth_router
from app.users.protected import router as protected_router
from app.posts.posts import router as post_router
from app.progress.progress import router as progress_router
from app.progress_detail_roro.progress_detail_roro import router as progress_detail_router
from app.replies.replies import router as reply_router
from app.categories.region_categories.region_categories import router as region_category_router
from app.categories.type_categories.type_categories import router as type_category_router

# 아래 코드: models.py의 모든 모델을 실제 DB 테이블로 생성 / 비동기에선 쓰지 않음
# models.Base.metadata.create_all(bind=engine)


# FastAPI 인스턴스 생성
app = FastAPI()
app.include_router(auth_router)
app.include_router(protected_router)

app.include_router(post_router)

app.include_router(progress_router)
app.include_router(progress_detail_router)

app.include_router(reply_router)
app.include_router(type_category_router)
app.include_router(region_category_router)



# CORS 설정 (프론트엔드 호스트와 연결)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 또는 ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)



