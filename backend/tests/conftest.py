"""
Pytest fixtures for EACIP tests.

Loop strategy (with pytest-asyncio 0.26+):
- Both test loop and fixture loop are session-scoped (see pytest.ini).
- This keeps SQLAlchemy async engine's connection pool aligned with
  a single event loop for the entire test session.
"""

from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _dispose_engine_at_session_end():
    """Cleanup: dispose engine pool at end of test session."""
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fresh DB session for each test (same DB shared across tests)."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client bound to the FastAPI app (in-process, no network)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c