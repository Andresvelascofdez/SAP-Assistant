"""
Script de inicialización de la base de datos
SAP IS-U Smart Wiki
"""
import asyncio
import os
import sys

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import create_engine
from db.models import Base
from config import settings

def init_database():
    """Inicializar la base de datos con las tablas"""
    print("Inicializando base de datos...")
    
    # Usar la URL de configuración
    database_url = settings.database_url.replace("+asyncpg", "")
    
    # Crear engine síncrono para la inicialización
    engine = create_engine(database_url)
    
    # Crear todas las tablas
    Base.metadata.create_all(engine)
    
    print("✅ Base de datos inicializada correctamente")
    print("Tablas creadas:")
    for table in Base.metadata.tables.keys():
        print(f"  - {table}")

if __name__ == "__main__":
    init_database()
