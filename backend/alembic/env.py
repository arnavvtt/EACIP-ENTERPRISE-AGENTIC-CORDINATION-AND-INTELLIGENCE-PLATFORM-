"""
Alembic environment configuration for EACIP.

This file configures Alembic to work with:
- Async SQLAlchemy (asyncpg driver)
- Our application's settings (database URL from environment)
- Our models' metadata (Base from app.database)

It supports both offline (SQL script generation) and online
(actual database connection) migration modes.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ----------------------------------------------------------------------
# Import our application's components
# ----------------------------------------------------------------------
# Add the project root to the Python path so we can import 'app'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings           # noqa: E402
from app.database import Base 
from app import models            # noqa: E402

# ----------------------------------------------------------------------
# Alembic Config
# ----------------------------------------------------------------------
config = context.config

# Set the database URL from our settings (overrides alembic.ini)
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configure Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
# (Abhi Base ke paas koi model nahi hai, lekin hum isko link kar rahe hain)
target_metadata = Base.metadata


# ----------------------------------------------------------------------
# Offline Mode (generate SQL script without connecting)
# ----------------------------------------------------------------------
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This generates SQL scripts without connecting to the database.
    Useful for generating migration SQL for review or for databases
    that aren't directly accessible.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ----------------------------------------------------------------------
# Online Mode (async)
# ----------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with a sync connection wrapper.

    This function is called via connection.run_sync() from the async
    engine, allowing Alembic's sync migration logic to work with our
    async database connection.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async engine and run migrations.

    Steps:
    1. Create async engine from config
    2. Connect (get a connection from the pool)
    3. Run migrations via run_sync (bridges async -> sync)
    4. Dispose the engine (cleanup)
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Entry point for online migrations.

    Runs the async migration function using asyncio.run().
    """
    asyncio.run(run_async_migrations())


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
