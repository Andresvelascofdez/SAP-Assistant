"""
Aplicación principal FastAPI
Wiki Inteligente SAP IS-U
"""
import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time

from .config import settings
from .db.database import init_db
from .utils.logging import configure_logging, get_logger, add_request_context
from .routers import auth, ingest, search
from .routers.admin import router as admin_router

# Configurar logging
configure_logging()
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    logger.info("Starting Wiki Inteligente SAP IS-U")
    
    try:
        # Inicializar base de datos
        await init_db()
        logger.info("Database initialized")
        
        # Inicializar Qdrant
        from api.services.embeddings import QdrantService
        qdrant = QdrantService()
        await qdrant.ensure_collection()
        logger.info("Qdrant collection initialized")
        
        # Verificar conexión OpenAI
        if settings.openai_api_key:
            from api.services.embeddings import EmbeddingService
            embedding_service = EmbeddingService()
            # Test simple
            test_embedding = await embedding_service.get_embedding("test")
            if test_embedding:
                logger.info("OpenAI connection verified")
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Crear aplicación FastAPI
app = FastAPI(
    title="Wiki Inteligente SAP IS-U",
    description="Sistema RAG multi-tenant para consultores SAP IS-U",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# Middleware de hosts confiables
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # En producción, especificar hosts
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware para añadir tiempo de procesamiento y logging"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Añadir contexto a logs
    user_id = None
    tenant = None
    
    # Intentar extraer usuario del token si existe
    try:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            from api.services.auth import AuthService
            token = auth_header.split(" ")[1]
            token_data = AuthService.verify_token(token)
            if token_data:
                user_id = str(token_data.user_id)
                tenant = token_data.tenant_slug
    except:
        pass
    
    add_request_context(request_id, user_id, tenant)
    
    # Procesar request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Añadir headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # Log de request
        logger.info(
            "Request processed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=process_time
        )
        raise


# Incluir routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

# Servir archivos estáticos
web_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
if os.path.exists(web_directory):
    app.mount("/static", StaticFiles(directory=web_directory), name="static")


@app.get("/")
async def root():
    """Endpoint raíz - redirige a la interfaz web"""
    from fastapi.responses import FileResponse
    web_index = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index.html")
    if os.path.exists(web_index):
        return FileResponse(web_index)
    return {
        "message": "Wiki Inteligente SAP IS-U API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Health check"""
    try:
        # Verificar base de datos
        from api.db.database import engine
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        # Verificar Qdrant
        from api.services.embeddings import QdrantService
        qdrant = QdrantService()
        collection_info = await qdrant.get_collection_info()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "database": "ok",
                "qdrant": "ok" if "error" not in collection_info else "error",
                "openai": "ok" if settings.openai_api_key else "not_configured"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.api_log_level.lower()
    )
