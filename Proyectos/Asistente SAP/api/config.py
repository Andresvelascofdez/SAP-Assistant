"""
Configuración principal de la aplicación FastAPI
Wiki Inteligente SAP IS-U
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # Base de datos
    database_url: str = "postgresql+asyncpg://postgres:changeme@localhost:5432/sapisu"
    postgres_password: str = "changeme"
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "sapisu_knowledge"
    
    # OpenAI
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4.1-preview"
    
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
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    allowed_methods: str = "GET,POST,PUT,DELETE,PATCH"
    allowed_headers: str = "*"
    
    @field_validator('allowed_origins')
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('allowed_methods')
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(',')]
        return v
    
    @field_validator('allowed_headers')
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(',')]
        return v
    
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
