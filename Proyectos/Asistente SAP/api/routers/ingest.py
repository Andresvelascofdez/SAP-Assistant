"""
Router de ingesta de documentos
Wiki Inteligente SAP IS-U
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..db.models import User
from ..models.schemas import (
    DocumentIngest, DocumentResponse, DocumentDetail, DocumentList,
    FileProcessResult, ScopeEnum, DocumentTypeEnum
)
from ..services.auth import get_current_active_user, require_tenant_access
from ..services.ingest import DocumentProcessor
from ..utils.logging import get_logger
from ..utils.parsers import FileParser

logger = get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["Document Ingestion"])


@router.post("/text", response_model=DocumentResponse)
async def ingest_text(
    document: DocumentIngest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Ingestar documento de texto"""
    # Verificar acceso al tenant
    require_tenant_access(document.tenant_slug)(current_user)
    
    if not document.text or len(document.text.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail="Text content is required and must be at least 10 characters"
        )
    
    try:
        processor = DocumentProcessor()
        result = await processor.process_document(document, db, current_user.id)
        
        logger.info(
            "Document ingested",
            document_id=str(result.id),
            tenant=document.tenant_slug,
            user_id=str(current_user.id)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest document: {str(e)}"
        )


@router.post("/text-public", response_model=DocumentResponse)
async def ingest_text_public(
    document: DocumentIngest,
    db: AsyncSession = Depends(get_db)
):
    """Ingestar documento de texto sin autenticación para uso personal"""
    if not document.text or len(document.text.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail="Text content is required and must be at least 10 characters"
        )
    
    try:
        processor = DocumentProcessor()
        # Usar un user_id por defecto para uso personal
        result = await processor.process_document(document, db, "personal-user")
        
        logger.info(
            "Document ingested (public)",
            document_id=str(result.id),
            tenant=document.tenant_slug
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest document: {str(e)}"
        )


@router.post("/files", response_model=List[FileProcessResult])
async def ingest_files(
    tenant_slug: str = Form(...),
    scope: Optional[ScopeEnum] = Form(None),
    document_type: DocumentTypeEnum = Form(DocumentTypeEnum.INCIDENCIA),
    force_scope: bool = Form(False),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Ingestar múltiples archivos"""
    # Verificar acceso al tenant
    require_tenant_access(tenant_slug)(current_user)
    
    if len(files) > 10:
        raise HTTPException(
            status_code=422,
            detail="Maximum 10 files allowed per request"
        )
    
    results = []
    processor = DocumentProcessor()
    file_parser = FileParser()
    
    for file in files:
        try:
            # Validar tipo de archivo
            if not FileParser.is_supported(file.filename):
                results.append(FileProcessResult(
                    filename=file.filename,
                    success=False,
                    error=f"Unsupported file type: {file.filename}"
                ))
                continue
            
            # Validar tamaño (máximo 10MB)
            if file.size and file.size > 10 * 1024 * 1024:
                results.append(FileProcessResult(
                    filename=file.filename,
                    success=False,
                    error="File too large (max 10MB)"
                ))
                continue
            
            # Guardar archivo temporalmente
            temp_file = f"/tmp/{uuid.uuid4()}_{file.filename}"
            with open(temp_file, "wb") as f:
                content = await file.read()
                f.write(content)
            
            try:
                # Parsear archivo
                parsed = file_parser.parse_file(temp_file, file.content_type)
                
                # Crear documento
                document_data = DocumentIngest(
                    tenant_slug=tenant_slug,
                    scope=scope,
                    type=document_type,
                    text=parsed['content'],
                    source=f"file:{file.filename}",
                    force_scope=force_scope
                )
                
                result = await processor.process_document(document_data, db, current_user.id)
                
                results.append(FileProcessResult(
                    filename=file.filename,
                    success=True,
                    document_id=result.id,
                    warnings=result.warnings
                ))
                
            finally:
                # Limpiar archivo temporal
                import os
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            results.append(FileProcessResult(
                filename=file.filename,
                success=False,
                error=str(e)
            ))
    
    logger.info(
        "Files processed",
        total_files=len(files),
        successful=sum(1 for r in results if r.success),
        tenant=tenant_slug,
        user_id=str(current_user.id)
    )
    
    return results


@router.get("/documents/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener detalle de documento"""
    from sqlalchemy import select
    from api.db.models import Document
    
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verificar acceso al tenant
    require_tenant_access(document.tenant_slug)(current_user)
    
    return DocumentDetail(
        id=document.id,
        tenant_slug=document.tenant_slug,
        scope=document.scope,
        type=document.type,
        title=document.title,
        system=document.system,
        topic=document.topic,
        tcodes=document.tcodes or [],
        tables=document.tables or [],
        version=document.version,
        chunks_count=len(document.chunks) if document.chunks else 0,
        created_at=document.created_at,
        root_cause=document.root_cause,
        steps=document.steps or [],
        risks=document.risks or [],
        tags=document.tags or [],
        source=document.source,
        hash=document.hash
    )


@router.get("/documents", response_model=DocumentList)
async def list_documents(
    tenant_slug: str = None,
    topic: str = None,
    system: str = None,
    scope: ScopeEnum = None,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar documentos con filtros"""
    from sqlalchemy import select, func
    from api.db.models import Document
    
    # Construir query base
    stmt = select(Document)
    count_stmt = select(func.count(Document.id))
    
    # Aplicar filtros
    conditions = []
    
    if tenant_slug:
        # Verificar acceso al tenant
        require_tenant_access(tenant_slug)(current_user)
        conditions.append(Document.tenant_slug == tenant_slug)
    else:
        # Si no se especifica tenant, mostrar solo los accesibles
        if current_user.role != "admin":
            user_tenant = current_user.tenant.slug if current_user.tenant else None
            if user_tenant:
                conditions.append(Document.tenant_slug.in_([user_tenant, "STANDARD"]))
            else:
                conditions.append(Document.tenant_slug == "STANDARD")
    
    if topic:
        conditions.append(Document.topic == topic)
    if system:
        conditions.append(Document.system == system)
    if scope:
        conditions.append(Document.scope == scope)
    
    # Aplicar condiciones
    for condition in conditions:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    
    # Obtener total
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # Aplicar paginación
    offset = (page - 1) * size
    stmt = stmt.offset(offset).limit(size).order_by(Document.created_at.desc())
    
    # Ejecutar query
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    # Formatear respuesta
    doc_responses = []
    for doc in documents:
        doc_responses.append(DocumentResponse(
            id=doc.id,
            tenant_slug=doc.tenant_slug,
            scope=doc.scope,
            type=doc.type,
            title=doc.title,
            system=doc.system,
            topic=doc.topic,
            tcodes=doc.tcodes or [],
            tables=doc.tables or [],
            version=doc.version,
            chunks_count=len(doc.chunks) if doc.chunks else 0,
            created_at=doc.created_at
        ))
    
    return DocumentList(
        documents=doc_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )
