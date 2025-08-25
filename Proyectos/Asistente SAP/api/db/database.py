"""
Configuración de base de datos y conexiones
Wiki Inteligente SAP IS-U
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings

# Motor de base de datos
engine = create_async_engine(
    settings.database_url,
    echo=settings.api_log_level == "debug",
    pool_pre_ping=True,
    pool_recycle=300
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    """Dependency para obtener sesión de DB"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Inicializar base de datos"""
    from db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
