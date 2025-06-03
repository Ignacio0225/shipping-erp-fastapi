# create_db.py (개발용 초기 DB 생성 스크립트)
import asyncio

from app.database import engine, Base

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_models())
