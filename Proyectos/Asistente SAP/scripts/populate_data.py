#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos de ejemplo
Wiki Inteligente SAP IS-U
"""
import asyncio
import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from api.db.database import AsyncSessionLocal
from api.services.ingest import DocumentProcessor
from api.models.schemas import DocumentIngest, DocumentTypeEnum, ScopeEnum
from api.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


# Datos de ejemplo para poblado inicial
SAMPLE_DOCUMENTS = [
    {
        "tenant_slug": "STANDARD",
        "scope": ScopeEnum.STANDARD,
        "type": DocumentTypeEnum.INCIDENCIA,
        "text": """
        Problema: Error en facturación masiva EC85
        
        Descripción: Al ejecutar la transacción EC85 para facturación masiva, el sistema muestra error 'No se pueden procesar las lecturas pendientes'.
        
        Causa raíz: Las lecturas en la tabla EABLG no tienen el status correcto para facturación.
        
        Solución:
        1. Verificar tabla EABLG con transacción EC03
        2. Revisar campo STATUS en registros pendientes
        3. Actualizar status con transacción EC10 si es necesario
        4. Re-ejecutar EC85
        
        Riesgos:
        - No actualizar lecturas sin verificar puede generar facturas incorrectas
        - Revisar siempre las fechas de facturación antes de procesar
        
        Tablas involucradas: EABLG, EABL, ERCH, ERCHC
        T-codes: EC85, EC03, EC10
        """,
        "source": "manual-standard"
    },
    {
        "tenant_slug": "STANDARD", 
        "scope": ScopeEnum.STANDARD,
        "type": DocumentTypeEnum.INCIDENCIA,
        "text": """
        Problema: Error en alta de suministro ES21
        
        Descripción: Al dar de alta un nuevo suministro con ES21, el sistema indica 'Business Partner no válido'.
        
        Causa raíz: El Business Partner no está correctamente configurado en BUT000 o falta información obligatoria.
        
        Solución:
        1. Verificar BP en transacción BP (BUT000)
        2. Completar datos obligatorios en pestañas:
           - Datos generales
           - Direcciones (ADRC)
           - Roles de BP
        3. Asegurar que tiene rol 'Solicitante' activo
        4. Reintentar ES21
        
        Riesgos:
        - BP mal configurado puede causar errores en facturación posterior
        - Verificar datos fiscales si es persona jurídica
        
        Tablas involucradas: BUT000, BUT020, ADRC, ESERVPROV
        T-codes: ES21, BP, ES31, ES32
        """,
        "source": "manual-standard"
    },
    {
        "tenant_slug": "STANDARD",
        "scope": ScopeEnum.STANDARD, 
        "type": DocumentTypeEnum.DOC,
        "text": """
        Guía: Proceso de move-in estándar en SAP IS-U
        
        El proceso de move-in (alta de suministro) consta de varios pasos:
        
        1. Preparación:
           - Verificar disponibilidad del punto de suministro
           - Confirmar datos del Business Partner
           - Revisar contratos existentes
        
        2. Ejecución:
           - ES21: Crear instalación
           - ES31: Crear contrato 
           - ES41: Crear orden de conexión (si aplica)
        
        3. Verificación:
           - Confirmar creación en EVER/EVERG
           - Verificar instalación en EANL/EANLG
           - Revisar datos en BUT000
        
        4. Post-procesamiento:
           - Programar primera lectura
           - Configurar ciclo de facturación
           - Activar servicios adicionales
        
        Puntos críticos:
        - Fechas de move-in no pueden ser futuras
        - BP debe tener rol 'Solicitante'
        - Verificar configuración de clase de instalación
        
        Tablas principales: EVER, EVERG, EANL, EANLG, BUT000, ESERVPROV
        """,
        "source": "manual-standard"
    },
    {
        "tenant_slug": "STANDARD",
        "scope": ScopeEnum.STANDARD,
        "type": DocumentTypeEnum.INCIDENCIA, 
        "text": """
        Problema: Aparatos no se crean automáticamente en EL31
        
        Descripción: Al ejecutar transacción EL31 para gestión de aparatos, no se crean automáticamente los aparatos para nuevas instalaciones.
        
        Causa raíz: Configuración incorrecta en tabla TE410 o TE416 para la clase de instalación.
        
        Solución:
        1. Verificar configuración en SPRO:
           - Utilities > Device Management > Device Categories
        2. Revisar tabla TE410 para clase de instalación
        3. Confirmar TE416 tiene aparato por defecto configurado
        4. Re-ejecutar EL31 o crear aparato manualmente
        
        Pasos manuales si la configuración no se puede cambiar:
        1. EL31 - Crear aparato
        2. Asignar número de serie
        3. Configurar registro de lectura
        4. Activar aparato
        
        Riesgos:
        - Aparatos mal configurados afectan lecturas automáticas
        - Verificar calibración antes de activar
        
        Tablas: TE410, TE416, EUITRANS, EQUI, EABL
        T-codes: EL31, EL32, EL33, EL34
        """,
        "source": "manual-standard"
    },
    {
        "tenant_slug": "STANDARD",
        "scope": ScopeEnum.STANDARD,
        "type": DocumentTypeEnum.NOTA,
        "text": """
        Nota técnica: Optimización de rendimiento en facturación masiva
        
        Para mejorar el rendimiento en procesos de facturación masiva:
        
        1. Configuración de sistema:
           - Ajustar parámetros de memoria en RZ10
           - Configurar jobs paralelos en SM36
           - Optimizar índices en tablas críticas
        
        2. Estrategia de ejecución:
           - Procesar por lotes pequeños (max 1000 registros)
           - Ejecutar en horarios de baja actividad
           - Monitorear con SM50/SM66
        
        3. Tablas a monitorear:
           - EABLG: Lecturas pendientes
           - ERCH: Documentos de facturación
           - DFKKOP: Partidas individuales
        
        4. Puntos de verificación:
           - Espacio en tablespace
           - Logs de sistema en SM21
           - Trabajos activos en SM37
        
        Recomendación: Implementar verificaciones automáticas con reportes custom.
        """,
        "source": "manual-standard"
    }
]


async def populate_sample_data():
    """Poblar base de datos con datos de ejemplo"""
    logger.info("Starting database population with sample data")
    
    processor = DocumentProcessor()
    
    async with AsyncSessionLocal() as db:
        # Crear un usuario ficticio para las operaciones
        from api.db.models import User
        from sqlalchemy import select
        
        # Buscar usuario admin
        stmt = select(User).where(User.email == "admin@sapisu.local")
        result = await db.execute(stmt)
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            logger.error("Admin user not found. Run setup.py first.")
            return False
        
        success_count = 0
        error_count = 0
        
        for i, doc_data in enumerate(SAMPLE_DOCUMENTS, 1):
            try:
                logger.info(f"Processing document {i}/{len(SAMPLE_DOCUMENTS)}")
                
                # Crear objeto DocumentIngest
                document = DocumentIngest(**doc_data)
                
                # Procesar documento
                result = await processor.process_document(
                    document, 
                    db, 
                    admin_user.id
                )
                
                logger.info(f"Document created: {result.id} - {result.title or 'No title'}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing document {i}: {e}")
                error_count += 1
        
        logger.info(f"Population completed: {success_count} successful, {error_count} errors")
        return error_count == 0


async def create_evaluation_queries():
    """Crear queries de evaluación"""
    logger.info("Creating evaluation queries")
    
    from api.db.models import EvalQuery
    
    eval_queries = [
        {
            "tenant_slug": "STANDARD",
            "question": "¿Cómo solucionar error en facturación masiva EC85?",
            "expected_sources": [],  # Se llenarán con IDs reales después
            "category": "billing",
            "difficulty": "medium"
        },
        {
            "tenant_slug": "STANDARD", 
            "question": "Error Business Partner no válido en ES21",
            "expected_sources": [],
            "category": "move-in",
            "difficulty": "easy"
        },
        {
            "tenant_slug": "STANDARD",
            "question": "Proceso completo de alta de suministro",
            "expected_sources": [],
            "category": "move-in", 
            "difficulty": "hard"
        },
        {
            "tenant_slug": "STANDARD",
            "question": "Aparatos no se crean automáticamente EL31",
            "expected_sources": [],
            "category": "device-management",
            "difficulty": "medium"
        },
        {
            "tenant_slug": "STANDARD",
            "question": "Optimizar rendimiento facturación masiva",
            "expected_sources": [],
            "category": "billing",
            "difficulty": "hard"
        }
    ]
    
    async with AsyncSessionLocal() as db:
        for query_data in eval_queries:
            eval_query = EvalQuery(**query_data)
            db.add(eval_query)
        
        await db.commit()
        logger.info(f"Created {len(eval_queries)} evaluation queries")


async def main():
    """Función principal"""
    logger.info("Starting sample data population")
    
    try:
        # Poblar documentos
        success = await populate_sample_data()
        
        if success:
            # Crear queries de evaluación
            await create_evaluation_queries()
            logger.info("Sample data population completed successfully")
        else:
            logger.error("Some errors occurred during population")
            
    except Exception as e:
        logger.error(f"Population failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
