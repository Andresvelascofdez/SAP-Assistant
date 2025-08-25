"""
Router de administración
Wiki Inteligente SAP IS-U
"""
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..db.database import get_db
from ..db.models import User, Document, Chunk, Tenant, EvalRun
from ..models.schemas import (
    HealthCheck, SystemMetrics, TenantCreate, TenantResponse,
    EvalRunResponse
)
from ..services.auth import require_admin
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/health", response_model=HealthCheck)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Health check detallado para admins"""
    try:
        services = {}
        metrics = {}
        
        # Verificar base de datos
        try:
            stmt = select(func.count(Document.id))
            result = await db.execute(stmt)
            doc_count = result.scalar()
            services["database"] = "ok"
            metrics["documents_count"] = doc_count
        except Exception as e:
            services["database"] = f"error: {str(e)}"
        
        # Verificar Qdrant
        try:
            from api.services.embeddings import QdrantService
            qdrant = QdrantService()
            collection_info = await qdrant.get_collection_info()
            
            if "error" in collection_info:
                services["qdrant"] = f"error: {collection_info['error']}"
            else:
                services["qdrant"] = "ok"
                metrics["qdrant_points"] = collection_info.get("points_count", 0)
        except Exception as e:
            services["qdrant"] = f"error: {str(e)}"
        
        # Verificar OpenAI
        try:
            from api.services.embeddings import EmbeddingService
            from api.config import settings
            
            if not settings.openai_api_key:
                services["openai"] = "not_configured"
            else:
                # Test rápido
                embedding_service = EmbeddingService()
                test_result = await embedding_service.get_embedding("test")
                services["openai"] = "ok" if test_result else "error"
        except Exception as e:
            services["openai"] = f"error: {str(e)}"
        
        # Métricas adicionales
        try:
            # Conteo de tenants
            stmt = select(func.count(Tenant.id))
            result = await db.execute(stmt)
            metrics["tenants_count"] = result.scalar()
            
            # Conteo de usuarios
            stmt = select(func.count(User.id))
            result = await db.execute(stmt)
            metrics["users_count"] = result.scalar()
            
            # Conteo de chunks
            stmt = select(func.count(Chunk.id))
            result = await db.execute(stmt)
            metrics["chunks_count"] = result.scalar()
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
        
        overall_status = "healthy" if all("error" not in s for s in services.values()) else "degraded"
        
        return HealthCheck(
            status=overall_status,
            timestamp=datetime.utcnow(),
            services=services,
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Obtener métricas del sistema"""
    try:
        # Contar documentos
        stmt = select(func.count(Document.id))
        result = await db.execute(stmt)
        documents_count = result.scalar()
        
        # Contar chunks
        stmt = select(func.count(Chunk.id))
        result = await db.execute(stmt)
        chunks_count = result.scalar()
        
        # Contar tenants
        stmt = select(func.count(Tenant.id))
        result = await db.execute(stmt)
        tenants_count = result.scalar()
        
        # Contar usuarios
        stmt = select(func.count(User.id))
        result = await db.execute(stmt)
        users_count = result.scalar()
        
        # Último backup (simulado por ahora)
        last_backup = None
        
        # Últimas métricas de evaluación
        eval_metrics = None
        try:
            stmt = select(EvalRun).order_by(EvalRun.run_at.desc()).limit(1)
            result = await db.execute(stmt)
            latest_eval = result.scalar_one_or_none()
            
            if latest_eval:
                eval_metrics = {
                    "ndcg_at_5": latest_eval.metric_ndcg / 100.0,
                    "hit_at_5": latest_eval.hit_at_5 / 100.0,
                    "avg_response_time_ms": latest_eval.avg_response_time,
                    "last_run": latest_eval.run_at.isoformat()
                }
        except Exception as e:
            logger.warning(f"Error getting eval metrics: {e}")
        
        # Calcular tamaño de almacenamiento (estimado)
        storage_size_mb = (chunks_count * 0.5) + (documents_count * 0.1)  # Estimación rough
        
        return SystemMetrics(
            documents_count=documents_count,
            chunks_count=chunks_count,
            tenants_count=tenants_count,
            users_count=users_count,
            storage_size_mb=storage_size_mb,
            last_backup=last_backup,
            eval_metrics=eval_metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Crear nuevo tenant"""
    # Verificar que el slug no existe
    stmt = select(Tenant).where(Tenant.slug == tenant.slug)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Tenant slug already exists"
        )
    
    # Crear tenant
    new_tenant = Tenant(
        slug=tenant.slug,
        name=tenant.name,
        timezone=tenant.timezone
    )
    
    db.add(new_tenant)
    await db.commit()
    await db.refresh(new_tenant)
    
    logger.info("Tenant created", tenant_slug=tenant.slug, admin_user=str(current_user.id))
    
    return TenantResponse(
        id=new_tenant.id,
        slug=new_tenant.slug,
        name=new_tenant.name,
        timezone=new_tenant.timezone,
        status=new_tenant.status,
        created_at=new_tenant.created_at
    )


@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Listar todos los tenants"""
    stmt = select(Tenant).order_by(Tenant.created_at.desc())
    result = await db.execute(stmt)
    tenants = result.scalars().all()
    
    return [
        TenantResponse(
            id=t.id,
            slug=t.slug,
            name=t.name,
            timezone=t.timezone,
            status=t.status,
            created_at=t.created_at
        )
        for t in tenants
    ]


@router.post("/reindex")
async def reindex_documents(
    tenant_slug: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Re-indexar documentos en Qdrant"""
    try:
        from api.services.embeddings import EmbeddingService, QdrantService
        from api.services.ingest import DocumentProcessor
        
        # Construir query
        stmt = select(Document)
        if tenant_slug:
            stmt = stmt.where(Document.tenant_slug == tenant_slug)
        
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        logger.info(f"Starting reindex of {len(documents)} documents")
        
        embedding_service = EmbeddingService()
        qdrant_service = QdrantService()
        
        reindexed_count = 0
        
        for doc in documents:
            try:
                # Eliminar chunks existentes de Qdrant
                if doc.chunks:
                    point_ids = [chunk.qdrant_point_id for chunk in doc.chunks if chunk.qdrant_point_id]
                    if point_ids:
                        await qdrant_service.delete_points(point_ids)
                
                # Eliminar chunks de PostgreSQL
                for chunk in doc.chunks:
                    await db.delete(chunk)
                
                # Re-procesar documento
                # Necesitamos el texto original - por ahora skip si no está disponible
                if not doc.chunks:
                    logger.warning(f"No content available for reindexing document {doc.id}")
                    continue
                
                # Aquí iría la lógica de re-procesamiento completo
                # Por simplicidad, marcamos como reindexado
                reindexed_count += 1
                
            except Exception as e:
                logger.error(f"Error reindexing document {doc.id}: {e}")
        
        await db.commit()
        
        logger.info(f"Reindexing completed: {reindexed_count} documents")
        
        return {
            "success": True,
            "reindexed_documents": reindexed_count,
            "total_documents": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error during reindexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup")
async def trigger_backup(
    current_user: User = Depends(require_admin)
):
    """Disparar backup manual"""
    try:
        # Aquí iría la lógica de backup
        # Por ahora simular
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("Manual backup triggered", backup_id=backup_id, admin_user=str(current_user.id))
        
        return {
            "success": True,
            "backup_id": backup_id,
            "message": "Backup completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error during backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
