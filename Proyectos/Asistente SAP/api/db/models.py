"""
Modelos de datos SQLAlchemy
Wiki Inteligente SAP IS-U
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Text, Integer, DateTime, Boolean, 
    ForeignKey, ARRAY, JSON, UUID, CheckConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    timezone = Column(String(50), default="Europe/Nicosia")
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    users = relationship("User", back_populates="tenant")
    documents = relationship("Document", back_populates="tenant_rel")


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), CheckConstraint("role IN ('admin', 'user')"), nullable=False)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relaciones
    tenant = relationship("Tenant", back_populates="users")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_slug = Column(String(50), nullable=False)
    scope = Column(String(20), CheckConstraint("scope IN ('STANDARD', 'CLIENT_SPECIFIC')"), nullable=False)
    type = Column(String(20), CheckConstraint("type IN ('incidencia', 'doc', 'nota', 'manual')"), nullable=False)
    system = Column(String(50))  # 'IS-U', 'CRM', etc.
    topic = Column(String(100))  # 'billing', 'move-in', 'dunning', etc.
    tcodes = Column(ARRAY(String))  # ['EC85', ...]
    tables = Column(ARRAY(String))  # ['EABLG', 'BUT000', ...]
    title = Column(Text)
    root_cause = Column(Text)
    steps = Column(ARRAY(Text))  # array de pasos
    risks = Column(ARRAY(Text))
    tags = Column(ARRAY(String))
    source = Column(Text)  # ruta, URL interna o 'nota-personal'
    version = Column(Integer, default=1)
    hash = Column(String(64))  # para deduplicación
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relaciones
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    tenant_rel = relationship("Tenant", back_populates="documents")
    
    # Índices
    __table_args__ = (
        Index('idx_docs_tenant_scope', 'tenant_slug', 'scope'),
        Index('idx_docs_topic', 'topic'),
        Index('idx_docs_tcodes', 'tcodes', postgresql_using='gin'),
        Index('idx_docs_tables', 'tables', postgresql_using='gin'),
        Index('idx_docs_created', 'created_at'),
        Index('idx_docs_hash', 'hash'),
    )


class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
    qdrant_point_id = Column(String(100))  # ID del punto en Qdrant
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    document = relationship("Document", back_populates="chunks")
    
    # Índices
    __table_args__ = (
        Index('idx_chunks_document', 'document_id'),
        Index('idx_chunks_qdrant', 'qdrant_point_id'),
    )


class EvalQuery(Base):
    __tablename__ = "eval_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_slug = Column(String(50), nullable=False)
    question = Column(Text, nullable=False)
    expected_sources = Column(ARRAY(String))  # IDs de documentos esperados
    category = Column(String(50))  # billing, move-in, etc.
    difficulty = Column(String(20))  # easy, medium, hard
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EvalRun(Base):
    __tablename__ = "eval_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_slug = Column(String(50))
    run_at = Column(DateTime(timezone=True), server_default=func.now())
    total_queries = Column(Integer)
    metric_ndcg = Column(Integer)  # nDCG@5 * 100 (para evitar decimales)
    hit_at_5 = Column(Integer)  # hit@5 * 100
    avg_response_time = Column(Integer)  # en milisegundos
    details = Column(JSON)  # resultados detallados por query
    
    # Índices
    __table_args__ = (
        Index('idx_eval_runs_tenant', 'tenant_slug'),
        Index('idx_eval_runs_date', 'run_at'),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    tenant_slug = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)  # ingest, search, chat, admin
    resource_type = Column(String(50))  # document, query, etc.
    resource_id = Column(String(100))
    metadata = Column(JSON)  # datos adicionales sin info sensible
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Índices
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_tenant', 'tenant_slug'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_timestamp', 'timestamp'),
    )
