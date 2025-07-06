# app/database.py
# PostgreSQL과 연결 및 ORM 설정을 담당하는 파일
# DB 연결, 세션 설정, 모델들이 상속받을 기본 클래스(Base) 정의


#                                       새로운 방식!!!!!!!!!!!
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = 'postgresql+asyncpg://yusunhyuk:tjsgur2399@localhost/shipping_erp_db'

engine = create_async_engine(DATABASE_URL)

# 최신 권장: async_sessionmaker 사용
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

Base = declarative_base()




#                               과거방식 !!!!!!
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession # 비동기 엔진 및 세션
# from sqlalchemy.orm import sessionmaker, declarative_base



# # 비동기 DB 연결 정보 (postgresql+asyncpg 사용)
# DATABASE_URL = 'postgresql+asyncpg://yusunhyuk:tjsgur2399@localhost/shipping_erp_db'
#
# # SQLAlchemy  비동기 엔진 생성
# engine = create_async_engine(DATABASE_URL)
#
# # 비동기 DB 세션을 생성하고 자동으로 닫아주는 의존성 함수
# # 요청이 들어오면 세션 열고, 요청이 끝나면 세션 자동 정리됨
# async def get_db():
#     async with AsyncSessionLocal() as session:
#         yield session
#
#
# # 비동기 세션 생성기
# AsyncSessionLocal = sessionmaker(
#     bind=engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autocommit=False,
#     autoflush=False,
# )
#
# # ORM 모델이 상속받을 베이스 클래스
# Base = declarative_base()


