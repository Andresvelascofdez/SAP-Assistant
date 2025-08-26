"""
Router de búsqueda y chat
Wiki Inteligente SAP IS-U
"""
import time
from typing import List, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User
from models.schemas import (
    SearchRequest, SearchResponse, SearchHit,
    ChatRequest, ChatResponse, ChatSource
)
from services.auth import get_current_active_user, require_tenant_access
from services.embeddings import EmbeddingService, QdrantService
from services.llm import LLMService
from utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/search", tags=["Search & Chat"])


@router.post("/chat-public", response_model=ChatResponse)
async def chat_public(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Chat con RAG sin autenticación para uso personal"""
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
        from config import settings
        search_results = await qdrant_service.search(
            query_vector=query_embedding,
            tenant_filter=tenant_filter,
            top_k=settings.rag_context_chunks,
            filters=search_filters
        )
        
        # 2. Preparar contexto para el LLM
        context_chunks = []
        for result in search_results:
            payload = result["payload"]
            context_chunks.append({
                "content": payload.get("content", ""),
                "metadata": payload,
                "score": result["score"]
            })
        
        # LOG DE DEPURACIÓN: Mostrar contexto que se está pasando
        logger.info(
            "=== CONTEXTO PASADO AL CHAT ===",
            query=request.query,
            tenant=request.tenant_slug,
            total_chunks=len(context_chunks),
            search_results_found=len(search_results),
            has_additional_context=request.additional_context is not None,
            additional_context_length=len(request.additional_context) if request.additional_context else 0
        )
        
        # Log contexto adicional si existe
        if request.additional_context:
            logger.info(
                "=== CONTEXTO ADICIONAL (ARCHIVO SUBIDO) ===",
                content_length=len(request.additional_context),
                content_preview=request.additional_context[:300] + "..." if len(request.additional_context) > 300 else request.additional_context
            )
        
        for i, chunk in enumerate(context_chunks):
            logger.info(
                f"CHUNK {i+1}/{len(context_chunks)} (RAG)",
                score=round(chunk["score"], 3),
                source=chunk["metadata"].get("source", "N/A"),
                title=chunk["metadata"].get("title", "N/A")[:100],
                content_preview=chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                content_length=len(chunk["content"])
            )
        
        # 3. Generar respuesta con LLM
        llm_response = await llm_service.generate_chat_response(
            query=request.query,
            context_chunks=context_chunks,
            tenant_slug=request.tenant_slug,
            additional_context=request.additional_context
        )
        
        # 4. Preparar sources para la respuesta
        sources = []
        for chunk in context_chunks:
            if chunk["score"] >= 0.7:  # Solo incluir chunks relevantes
                # Obtener o generar document_id
                doc_id = chunk["metadata"].get("document_id")
                if doc_id is None:
                    doc_id = uuid4()
                elif isinstance(doc_id, str):
                    doc_id = UUID(doc_id)
                
                sources.append(ChatSource(
                    document_id=doc_id,
                    source=chunk["metadata"].get("source"),
                    title=chunk["metadata"].get("title"),
                    tenant=chunk["metadata"].get("tenant", request.tenant_slug),
                    scope=chunk["metadata"].get("scope", "CLIENT_SPECIFIC"),
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
            "Chat completed (public)",
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