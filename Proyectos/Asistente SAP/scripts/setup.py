#!/usr/bin/env python3
"""
Script de setup inicial para Wiki Inteligente SAP IS-U
"""
import asyncio
import os
import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from api.config import settings
from api.db.database import init_db, AsyncSessionLocal
from api.db.models import Tenant, User
from api.services.auth import AuthService
from api.services.embeddings import QdrantService
from api.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def create_initial_data():
    """Crear datos iniciales"""
    async with AsyncSessionLocal() as db:
        # Crear tenant STANDARD
        from sqlalchemy import select
        
        # Verificar si ya existe
        stmt = select(Tenant).where(Tenant.slug == "STANDARD")
        result = await db.execute(stmt)
        standard_tenant = result.scalar_one_or_none()
        
        if not standard_tenant:
            standard_tenant = Tenant(
                slug="STANDARD",
                name="Conocimiento Estándar SAP IS-U",
                timezone="Europe/Nicosia"
            )
            db.add(standard_tenant)
            logger.info("Created STANDARD tenant")
        
        # Crear usuario admin
        stmt = select(User).where(User.email == "admin@sapisu.local")
        result = await db.execute(stmt)
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            hashed_password = AuthService.get_password_hash("admin123")
            admin_user = User(
                email="admin@sapisu.local",
                hashed_password=hashed_password,
                role="admin",
                tenant_id=standard_tenant.id
            )
            db.add(admin_user)
            logger.info("Created admin user: admin@sapisu.local / admin123")
        
        await db.commit()


async def setup_qdrant():
    """Configurar Qdrant"""
    try:
        qdrant_service = QdrantService()
        await qdrant_service.ensure_collection()
        logger.info("Qdrant collection initialized")
        
        # Verificar info
        info = await qdrant_service.get_collection_info()
        logger.info(f"Qdrant collection info: {info}")
        
    except Exception as e:
        logger.error(f"Error setting up Qdrant: {e}")
        raise


async def run_database_migrations():
    """Ejecutar migraciones de base de datos"""
    try:
        # Verificar si alembic está disponible
        import subprocess
        
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=project_root / "api",
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Database migrations completed successfully")
        else:
            logger.error(f"Migration failed: {result.stderr}")
            
    except FileNotFoundError:
        logger.warning("Alembic not found, skipping migrations")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")


def create_env_file():
    """Crear archivo .env si no existe"""
    env_file = project_root / ".env"
    example_file = project_root / ".env.example"
    
    if not env_file.exists() and example_file.exists():
        import shutil
        shutil.copy(example_file, env_file)
        logger.info("Created .env file from .env.example")
        logger.warning("Please edit .env file with your actual configuration")
        return False
    elif env_file.exists():
        logger.info(".env file already exists")
        return True
    else:
        logger.error("No .env.example file found")
        return False


def check_requirements():
    """Verificar dependencias"""
    missing = []
    
    try:
        import fastapi
    except ImportError:
        missing.append("fastapi")
    
    try:
        import sqlalchemy
    except ImportError:
        missing.append("sqlalchemy")
    
    try:
        import qdrant_client
    except ImportError:
        missing.append("qdrant-client")
    
    try:
        import openai
    except ImportError:
        missing.append("openai")
    
    if missing:
        logger.error(f"Missing required packages: {', '.join(missing)}")
        logger.error("Run: pip install -r requirements.txt")
        return False
    
    logger.info("All required packages are installed")
    return True


async def main():
    """Función principal de setup"""
    logger.info("Starting Wiki Inteligente SAP IS-U setup")
    
    # 1. Verificar requirements
    if not check_requirements():
        sys.exit(1)
    
    # 2. Crear archivo .env
    if not create_env_file():
        logger.warning("Please configure .env file and run setup again")
        sys.exit(1)
    
    # 3. Verificar configuración crítica
    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY not configured in .env")
        sys.exit(1)
    
    if not settings.jwt_secret or settings.jwt_secret == "your_very_long_and_secure_secret_key_here_change_in_production":
        logger.error("JWT_SECRET not properly configured in .env")
        sys.exit(1)
    
    try:
        # 4. Inicializar base de datos
        logger.info("Initializing database...")
        await init_db()
        
        # 5. Ejecutar migraciones
        logger.info("Running database migrations...")
        await run_database_migrations()
        
        # 6. Configurar Qdrant
        logger.info("Setting up Qdrant...")
        await setup_qdrant()
        
        # 7. Crear datos iniciales
        logger.info("Creating initial data...")
        await create_initial_data()
        
        logger.info("Setup completed successfully!")
        logger.info("You can now start the API with: uvicorn api.main:app --reload")
        logger.info("Default admin credentials: admin@sapisu.local / admin123")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
