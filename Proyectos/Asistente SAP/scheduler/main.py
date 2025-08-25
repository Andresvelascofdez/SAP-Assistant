"""
Scheduler para tareas programadas
Wiki Inteligente SAP IS-U
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api.config import settings
from api.db.database import AsyncSessionLocal
from api.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


class BackupService:
    """Servicio de backups"""
    
    async def backup_postgres(self):
        """Backup de PostgreSQL"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"/app/backups/postgres_backup_{timestamp}.sql.gz"
            
            # Crear directorio si no existe
            os.makedirs("/app/backups", exist_ok=True)
            
            # Comando pg_dump
            cmd = f"""pg_dump {settings.database_url.replace('+asyncpg', '')} | gzip > {backup_file}"""
            
            result = os.system(cmd)
            
            if result == 0:
                logger.info(f"PostgreSQL backup completed: {backup_file}")
                
                # Limpiar backups antiguos (mantener últimos 7 días)
                await self._cleanup_old_backups("/app/backups", "postgres_backup_", 7)
            else:
                logger.error(f"PostgreSQL backup failed with code: {result}")
                
        except Exception as e:
            logger.error(f"Error during PostgreSQL backup: {e}")
    
    async def backup_qdrant(self):
        """Backup de Qdrant"""
        try:
            from api.services.embeddings import QdrantService
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"/app/backups/qdrant_backup_{timestamp}"
            
            # Crear directorio
            os.makedirs(backup_dir, exist_ok=True)
            
            qdrant = QdrantService()
            
            # Crear snapshot (esto es una simulación, Qdrant real tendría API específica)
            collection_info = await qdrant.get_collection_info()
            
            # Guardar información de la colección
            with open(f"{backup_dir}/collection_info.json", "w") as f:
                import json
                json.dump(collection_info, f, indent=2)
            
            logger.info(f"Qdrant backup completed: {backup_dir}")
            
            # Limpiar backups antiguos
            await self._cleanup_old_backups("/app/backups", "qdrant_backup_", 7)
            
        except Exception as e:
            logger.error(f"Error during Qdrant backup: {e}")
    
    async def _cleanup_old_backups(self, backup_dir: str, prefix: str, days_to_keep: int):
        """Limpiar backups antiguos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for item in os.listdir(backup_dir):
                if item.startswith(prefix):
                    item_path = os.path.join(backup_dir, item)
                    item_time = datetime.fromtimestamp(os.path.getmtime(item_path))
                    
                    if item_time < cutoff_date:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            import shutil
                            shutil.rmtree(item_path)
                        
                        logger.info(f"Removed old backup: {item}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")


class EvaluationService:
    """Servicio de evaluación automática"""
    
    async def run_evaluation(self):
        """Ejecutar evaluación de calidad RAG"""
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                from api.db.models import EvalQuery, Document
                from api.services.embeddings import EmbeddingService, QdrantService
                
                # Obtener queries de evaluación
                stmt = select(EvalQuery).limit(20)  # Evaluar máximo 20 queries
                result = await db.execute(stmt)
                eval_queries = result.scalars().all()
                
                if not eval_queries:
                    logger.info("No evaluation queries found")
                    return
                
                logger.info(f"Running evaluation on {len(eval_queries)} queries")
                
                embedding_service = EmbeddingService()
                qdrant_service = QdrantService()
                
                total_ndcg = 0
                total_hit_at_5 = 0
                response_times = []
                
                for query in eval_queries:
                    try:
                        start_time = datetime.now()
                        
                        # Obtener embedding
                        query_embedding = await embedding_service.get_embedding(query.question)
                        
                        # Buscar
                        tenant_filter = [query.tenant_slug]
                        if query.tenant_slug != "STANDARD":
                            tenant_filter.append("STANDARD")
                        
                        results = await qdrant_service.search(
                            query_vector=query_embedding,
                            tenant_filter=tenant_filter,
                            top_k=5
                        )
                        
                        # Calcular métricas
                        retrieved_docs = [r["payload"].get("doc_id") for r in results if r["payload"].get("doc_id")]
                        expected_docs = query.expected_sources
                        
                        # Hit@5
                        hit_at_5 = 1 if any(doc in retrieved_docs for doc in expected_docs) else 0
                        total_hit_at_5 += hit_at_5
                        
                        # nDCG@5 (simplificado)
                        ndcg = 0
                        for i, doc_id in enumerate(retrieved_docs[:5]):
                            if doc_id in expected_docs:
                                ndcg += 1 / (i + 1)  # Simplificado
                        
                        total_ndcg += ndcg
                        
                        # Tiempo de respuesta
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        response_times.append(response_time)
                        
                    except Exception as e:
                        logger.error(f"Error evaluating query {query.id}: {e}")
                
                # Calcular promedios
                avg_ndcg = total_ndcg / len(eval_queries) if eval_queries else 0
                avg_hit_at_5 = total_hit_at_5 / len(eval_queries) if eval_queries else 0
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                # Guardar resultados
                from api.db.models import EvalRun
                eval_run = EvalRun(
                    total_queries=len(eval_queries),
                    metric_ndcg=int(avg_ndcg * 100),
                    hit_at_5=int(avg_hit_at_5 * 100),
                    avg_response_time=int(avg_response_time),
                    details={}
                )
                
                db.add(eval_run)
                await db.commit()
                
                logger.info(
                    f"Evaluation completed: nDCG={avg_ndcg:.3f}, Hit@5={avg_hit_at_5:.3f}, "
                    f"AvgTime={avg_response_time:.0f}ms"
                )
                
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")


async def main():
    """Función principal del scheduler"""
    logger.info("Starting SAP IS-U Wiki Scheduler")
    
    # Crear servicios
    backup_service = BackupService()
    eval_service = EvaluationService()
    
    # Crear scheduler
    scheduler = AsyncIOScheduler()
    
    # Configurar trabajos
    if settings.backup_enabled:
        # Backup diario a las 2 AM
        scheduler.add_job(
            backup_service.backup_postgres,
            CronTrigger.from_crontab(settings.backup_schedule_cron),
            id="postgres_backup",
            name="PostgreSQL Backup"
        )
        
        scheduler.add_job(
            backup_service.backup_qdrant,
            CronTrigger.from_crontab(settings.backup_schedule_cron),
            id="qdrant_backup",
            name="Qdrant Backup"
        )
    
    # Evaluación semanal los domingos a las 3 AM
    scheduler.add_job(
        eval_service.run_evaluation,
        CronTrigger(day_of_week=0, hour=3, minute=0),
        id="weekly_evaluation",
        name="Weekly RAG Evaluation"
    )
    
    # Iniciar scheduler
    scheduler.start()
    logger.info("Scheduler started successfully")
    
    try:
        # Mantener el scheduler corriendo
        while True:
            await asyncio.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
