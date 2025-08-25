"""
Configuración principal de la aplicación FastAPI
Wiki Inteligente SAP IS-U
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # Base de datos
    database_url: str = "postgresql+asyncpg://postgres:changeme@localhost:5432/sapisu"
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "sapisu_knowledge"
    
    # OpenAI
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    api_log_level: str = "info"
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    allowed_headers: List[str] = ["*"]
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Chunk settings
    chunk_size: int = 800
    chunk_overlap: int = 150
    max_chunks_per_doc: int = 50
    
    # RAG settings
    top_k_initial: int = 30
    top_k_final: int = 5
    rerank_enabled: bool = False
    
    # Timezone
    tz: str = "Europe/Nicosia"
    
    # Backup
    backup_enabled: bool = True
    backup_schedule_cron: str = "0 2 * * *"
    backup_retention_days: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"


settings = Settings()
