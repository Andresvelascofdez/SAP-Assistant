"""
Modelos Pydantic para validación de datos
Wiki Inteligente SAP IS-U
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class ScopeEnum(str, Enum):
    STANDARD = "STANDARD"
    CLIENT_SPECIFIC = "CLIENT_SPECIFIC"


class DocumentTypeEnum(str, Enum):
    INCIDENCIA = "incidencia"
    DOC = "doc"
    NOTA = "nota"
    MANUAL = "manual"


class RoleEnum(str, Enum):
    ADMIN = "admin"
    USER = "user"


# --- Modelos de autenticación ---

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: RoleEnum
    tenant_slug: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    tenant_slug: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: UUID
    email: str
    role: str
    tenant_slug: Optional[str]


# --- Modelos de tenant ---

class TenantCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(..., min_length=2, max_length=200)
    timezone: str = "Europe/Nicosia"


class TenantResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    timezone: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Modelos de documentos ---

class DocumentMetadata(BaseModel):
    """Metadatos extraídos automáticamente"""
    tenant_slug: str
    scope: ScopeEnum = ScopeEnum.STANDARD
    system: Optional[str] = None
    topic: Optional[str] = None
    tcodes: List[str] = Field(default_factory=list)
    tables: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class DocumentStructured(BaseModel):
    """Documento estructurado extraído por LLM"""
    title: Optional[str] = None
    root_cause: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
    questions: List[str] = Field(default_factory=list)


class DocumentIngest(BaseModel):
    """Request para ingesta de documento"""
    tenant_slug: str
    scope: Optional[ScopeEnum] = None
    type: DocumentTypeEnum = DocumentTypeEnum.INCIDENCIA
    text: Optional[str] = None
    source: Optional[str] = "manual"
    metadata: Optional[DocumentMetadata] = None
    structured: Optional[DocumentStructured] = None
    force_scope: bool = False  # Forzar scope aunque se detecten objetos Z


class DocumentResponse(BaseModel):
    """Response de documento creado"""
    id: UUID
    tenant_slug: str
    scope: str
    type: str
    title: Optional[str]
    system: Optional[str]
    topic: Optional[str]
    tcodes: List[str]
    tables: List[str]
    version: int
    chunks_count: int
    created_at: datetime
    warnings: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class DocumentDetail(DocumentResponse):
    """Detalle completo de documento"""
    root_cause: Optional[str]
    steps: List[str]
    risks: List[str]
    tags: List[str]
    source: Optional[str]
    hash: Optional[str]


class DocumentList(BaseModel):
    """Lista paginada de documentos"""
    documents: List[DocumentResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Modelos de búsqueda y chat ---

class SearchFilters(BaseModel):
    """Filtros para búsqueda"""
    system: Optional[str] = None
    topic: Optional[str] = None
    tcodes: List[str] = Field(default_factory=list)
    tables: List[str] = Field(default_factory=list)
    scope: Optional[ScopeEnum] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SearchRequest(BaseModel):
    """Request de búsqueda"""
    tenant_slug: str
    query: str
    filters: Optional[SearchFilters] = None
    top_k: int = Field(default=5, ge=1, le=20)


class SearchHit(BaseModel):
    """Resultado de búsqueda"""
    document_id: UUID
    chunk_id: UUID
    content: str
    score: float
    metadata: Dict[str, Any]
    source: Optional[str]
    title: Optional[str]


class SearchResponse(BaseModel):
    """Response de búsqueda"""
    hits: List[SearchHit]
    total_found: int
    query_time_ms: int


class ChatRequest(BaseModel):
    """Request de chat"""
    tenant_slug: str
    query: str
    filters: Optional[SearchFilters] = None
    include_trace: bool = False


class ChatSource(BaseModel):
    """Fuente citada en respuesta de chat"""
    document_id: UUID
    source: Optional[str]
    title: Optional[str]
    tenant: str
    scope: str
    relevance_score: float


class ChatResponse(BaseModel):
    """Response de chat"""
    answer: str
    sources: List[ChatSource]
    confidence: float = Field(ge=0.0, le=1.0)
    response_time_ms: int
    trace: Optional[Dict[str, Any]] = None
    needs_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)


# --- Modelos de evaluación ---

class EvalQueryCreate(BaseModel):
    """Query de evaluación"""
    tenant_slug: str
    question: str
    expected_sources: List[str]  # IDs de documentos esperados
    category: Optional[str] = None
    difficulty: Optional[str] = "medium"


class EvalResult(BaseModel):
    """Resultado de evaluación"""
    query_id: UUID
    question: str
    expected_sources: List[str]
    retrieved_sources: List[str]
    hit_at_5: bool
    ndcg_score: float
    response_time_ms: int


class EvalRunResponse(BaseModel):
    """Resultado de ejecución de evaluación"""
    id: UUID
    tenant_slug: Optional[str]
    run_at: datetime
    total_queries: int
    metric_ndcg: float
    hit_at_5: float
    avg_response_time: int
    results: List[EvalResult]

    class Config:
        from_attributes = True


# --- Modelos de admin ---

class HealthCheck(BaseModel):
    """Estado de salud del sistema"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    metrics: Dict[str, Any]


class SystemMetrics(BaseModel):
    """Métricas del sistema"""
    documents_count: int
    chunks_count: int
    tenants_count: int
    users_count: int
    storage_size_mb: float
    last_backup: Optional[datetime]
    eval_metrics: Optional[Dict[str, float]]


# --- Modelos de archivos ---

class FileUpload(BaseModel):
    """Metadatos de archivo subido"""
    filename: str
    content_type: str
    size: int
    tenant_slug: str
    scope: Optional[ScopeEnum] = None


class FileProcessResult(BaseModel):
    """Resultado de procesamiento de archivo"""
    filename: str
    success: bool
    document_id: Optional[UUID] = None
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
