"""
Router de búsqueda y chat
Wiki Inteligente SAP IS-U
"""
import time
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.db.models import User
from api.models.schemas import (
    SearchRequest, SearchResponse, SearchHit,
    ChatRequest, ChatResponse, ChatSource
)
from api.services.auth import get_current_active_user, require_tenant_access
from api.services.embeddings import EmbeddingService, QdrantService
from api.services.llm import LLMService
from api.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/search", tags=["Search & Chat"])


@router.post("/vector", response_model=SearchResponse)
async def vector_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Búsqueda vectorial con filtros"""
    # Verificar acceso al tenant
    require_tenant_access(request.tenant_slug)(current_user)
    
    start_time = time.time()
    
    try:
        embedding_service = EmbeddingService()
        qdrant_service = QdrantService()
        
        # Obtener embedding de la query
        query_embedding = await embedding_service.get_embedding(request.query)
        
        # Preparar filtros de tenant (incluir STANDARD)
        tenant_filter = [request.tenant_slug]
        if request.tenant_slug != "STANDARD":
            tenant_filter.append("STANDARD")
        
        # Preparar filtros adicionales
        search_filters = {}
        if request.filters:
            if request.filters.scope:
                search_filters["scope"] = request.filters.scope
            if request.filters.system:
                search_filters["system"] = request.filters.system
            if request.filters.topic:
                search_filters["topic"] = request.filters.topic
        
        # Realizar búsqueda en Qdrant
        search_results = await qdrant_service.search(
            query_vector=query_embedding,
            tenant_filter=tenant_filter,
            top_k=request.top_k,
            filters=search_filters
        )
        
        # Formatear resultados
        hits = []
        for result in search_results:
            payload = result["payload"]
            hits.append(SearchHit(
                document_id=payload.get("doc_id"),
                chunk_id=result["id"],
                content=payload.get("content", ""),
                score=result["score"],
                metadata=payload,
                source=payload.get("source"),
                title=payload.get("title")
            ))
        
        query_time = int((time.time() - start_time) * 1000)
        
        logger.info(
            "Vector search completed",
            tenant=request.tenant_slug,
            query_length=len(request.query),
            results_count=len(hits),
            query_time_ms=query_time
        )
        
        return SearchResponse(
            hits=hits,
            total_found=len(hits),
            query_time_ms=query_time
        )
    
    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Chat con RAG"""
    # Verificar acceso al tenant
    require_tenant_access(request.tenant_slug)(current_user)
    
    start_time = time.time()
    
    try:
        embedding_service = EmbeddingService()
        qdrant_service = QdrantService()
        llm_service = LLMService()
        
        # 1. Búsqueda vectorial para recuperar contexto
        query_embedding = await embedding_service.get_embedding(request.query)
        
        # Preparar filtros de tenant
        tenant_filter = [request.tenant_slug]
        if request.tenant_slug != "STANDARD":
            tenant_filter.append("STANDARD")
        
        # Preparar filtros adicionales
        search_filters = {}
        if request.filters:
            if request.filters.scope:
                search_filters["scope"] = request.filters.scope
            if request.filters.system:
                search_filters["system"] = request.filters.system
            if request.filters.topic:
                search_filters["topic"] = request.filters.topic
        
        # Buscar chunks relevantes
        from api.config import settings
        search_results = await qdrant_service.search(
            query_vector=query_embedding,
            tenant_filter=tenant_filter,
            top_k=settings.top_k_initial,
            filters=search_filters
        )
        
        # 2. Filtrar y preparar contexto
        context_chunks = []
        for result in search_results[:settings.top_k_final]:
            context_chunks.append({
                "content": result["payload"].get("content", ""),
                "metadata": result["payload"],
                "score": result["score"]
            })
        
        # 3. Generar respuesta con LLM
        llm_response = await llm_service.generate_chat_response(
            query=request.query,
            context_chunks=context_chunks,
            tenant_slug=request.tenant_slug
        )
        
        # 4. Preparar fuentes citadas
        sources = []
        seen_docs = set()
        for chunk in context_chunks:
            doc_id = chunk["metadata"].get("doc_id")
            if doc_id and doc_id not in seen_docs:
                seen_docs.add(doc_id)
                sources.append(ChatSource(
                    document_id=doc_id,
                    source=chunk["metadata"].get("source"),
                    title=chunk["metadata"].get("title"),
                    tenant=chunk["metadata"].get("tenant"),
                    scope=chunk["metadata"].get("scope"),
                    relevance_score=chunk["score"]
                ))
        
        response_time = int((time.time() - start_time) * 1000)
        
        # 5. Preparar trace si se solicita
        trace = None
        if request.include_trace:
            trace = {
                "query_embedding_time": "~200ms",
                "search_results_count": len(search_results),
                "context_chunks_used": len(context_chunks),
                "llm_tokens": "~500",
                "total_time_ms": response_time
            }
        
        logger.info(
            "Chat completed",
            tenant=request.tenant_slug,
            query_length=len(request.query),
            context_chunks=len(context_chunks),
            sources_count=len(sources),
            confidence=llm_response["confidence"],
            response_time_ms=response_time
        )
        
        return ChatResponse(
            answer=llm_response["answer"],
            sources=sources,
            confidence=llm_response["confidence"],
            response_time_ms=response_time,
            trace=trace,
            needs_clarification=llm_response.get("needs_clarification", False),
            clarification_questions=llm_response.get("questions", [])
        )
    
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.post("/save-response")
async def save_chat_response_as_standard(
    response_text: str,
    title: str,
    tenant_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Guardar respuesta de chat como documento STANDARD"""
    # Verificar acceso al tenant
    require_tenant_access(tenant_slug)(current_user)
    
    try:
        from api.models.schemas import DocumentIngest, DocumentTypeEnum, ScopeEnum
        from api.services.ingest import DocumentProcessor
        
        # Crear documento STANDARD desde la respuesta
        document_data = DocumentIngest(
            tenant_slug="STANDARD",
            scope=ScopeEnum.STANDARD,
            type=DocumentTypeEnum.NOTA,
            text=response_text,
            source=f"chat-response:{tenant_slug}",
            structured={
                "title": title,
                "root_cause": "Información extraída de consulta de chat",
                "steps": [],
                "risks": []
            }
        )
        
        processor = DocumentProcessor()
        result = await processor.process_document(document_data, db, current_user.id)
        
        logger.info(
            "Chat response saved as STANDARD document",
            document_id=str(result.id),
            original_tenant=tenant_slug,
            user_id=str(current_user.id)
        )
        
        return {
            "success": True,
            "document_id": str(result.id),
            "message": "Response saved as STANDARD document"
        }
    
    except Exception as e:
        logger.error(f"Error saving chat response: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save response: {str(e)}"
        )
