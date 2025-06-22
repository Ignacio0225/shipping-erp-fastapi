# alembic/env.py  (동기 엔진만 사용하여 autogenerate/upgrade)
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ─────────────────────────────
# Alembic 설정 읽기 & 로깅
# ─────────────────────────────
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# ─────────────────────────────
# 모델 메타데이터 등록
# ─────────────────────────────
from app.database import Base          # ↙ 모델들이 Base 상속
from app.users import users_models               # noqa: F401 (import 해야 메타데이터에 등록됨)
from app.posts import shipments_models           # noqa: F401 (import 해야 메타데이터에 등록됨)
from app.replies import replies_models           # noqa: F401 (import 해야 메타데이터에 등록됨)

target_metadata = Base.metadata

# ─────────────────────────────
# 공통: URL을 동기 드라이버(psycopg2)로 바꿔주기
#      alembic.ini 에는  async  URL이 있어도 좋지만
#      여기서는 강제로 수정해 줌
# ─────────────────────────────
ASYNC_URL = config.get_main_option("sqlalchemy.url")          # e.g.  postgresql+asyncpg://...
SYNC_URL  = ASYNC_URL.replace("+asyncpg", "")                 # → postgresql://...

config.set_main_option("sqlalchemy.url", SYNC_URL)

# ─────────────────────────────
def run_migrations_offline() -> None:
    """←  sql 스크립트만 뽑을 때"""
    context.configure(
        url=SYNC_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """←  실제 DB에 적용할 때 (동기 엔진)"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
