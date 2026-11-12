import logging
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.config import settings

logger = logging.getLogger(__name__)

# Convert SQLAlchemy URL (postgresql+asyncpg://) to standard psycopg URL (postgresql://)
_POSTGRES_DSN = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None

async def get_langgraph_checkpointer() -> AsyncPostgresSaver:
    global _pool, _checkpointer
    
    if _checkpointer is not None:
        return _checkpointer

    logger.info("Initializing LangGraph Postgres Checkpointer...")
    
    # PgBouncer compatibility and async setup
    _pool = AsyncConnectionPool(
        conninfo=_POSTGRES_DSN,
        open=False,
        kwargs={"autocommit": True, "prepare_threshold": 0}
    )
    await _pool.open()
    
    _checkpointer = AsyncPostgresSaver(_pool)
    await _checkpointer.setup()  # Creates checkpoints tables automatically
    
    logger.info("LangGraph Checkpointer initialized successfully.")
    return _checkpointer

async def close_checkpointer():
    global _pool, _checkpointer
    if _pool:
        await _pool.close()
        _pool = None
        _checkpointer = None
        logger.info("LangGraph Checkpointer closed.")