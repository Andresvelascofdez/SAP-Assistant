"""
Configuración de Alembic
Wiki Inteligente SAP IS-U
"""
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine

# Añadir el directorio padre al path para imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db.models import Base
from config import settings

# Configuración de Alembic
config = context.config

# Configurar logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadatos del modelo
target_metadata = Base.metadata


def get_url():
    """Obtener URL de base de datos"""
    return settings.database_url.replace("+asyncpg", "")


def run_migrations_offline() -> None:
    """Ejecutar migraciones en modo offline"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Ejecutar migraciones con conexión"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Ejecutar migraciones async"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = AsyncEngine(
        engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Ejecutar migraciones en modo online"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
