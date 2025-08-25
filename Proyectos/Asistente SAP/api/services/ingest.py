"""
Servicio de ingesta de documentos
Wiki Inteligente SAP IS-U
"""
import re
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from qdrant_client.models import PointStruct

from ..db.models import Document, Chunk, Tenant
from ..models.schemas import DocumentIngest, DocumentMetadata, DocumentStructured, DocumentResponse
from ..services.embeddings import EmbeddingService, QdrantService
from ..services.llm import LLMService
from ..utils.logging import get_logger
from ..utils.parsers import FileParser

logger = get_logger(__name__)


class MetadataExtractor:
    """Extractor de metadatos SAP IS-U"""
    
    # Patrones regex para extracción
    TCODE_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}\b')
    TABLE_PATTERN = re.compile(r'\b[A-Z][A-Z0-9_]{3,}\b')
    Z_OBJECT_PATTERN = re.compile(r'\b[ZY][A-Z0-9_]{2,}\b')
    
    # Lista blanca de t-codes IS-U comunes
    ISU_TCODES = {
        'EC85', 'EC86', 'EC87', 'EC01', 'EC02', 'EC03', 'EC10', 'EC11',
        'ES21', 'ES22', 'ES23', 'ES31', 'ES32', 'ES33', 'ES41', 'ES42',
        'EL31', 'EL32', 'EL33', 'EL34', 'EL35', 'EL36', 'EL37', 'EL38',
        'EABL', 'EABLG', 'EORD', 'EORDG', 'EVER', 'EVERG', 'EANL', 'EANLG'
    }
    
    # Lista de tablas IS-U comunes
    ISU_TABLES = {
        'EABLG', 'EABL', 'EORDG', 'EORD', 'EVERG', 'EVER', 'EANLG', 'EANL',
        'BUT000', 'BUT020', 'ADRC', 'FKKVKP', 'FKKVK', 'ERCH', 'ERCHC',
        'DFKKKO', 'DFKKOP', 'EUITRANS', 'ESERVPROV', 'TE410', 'TE416'
    }
    
    # Mapeo de temas por t-codes
    TOPIC_MAPPING = {
        'billing': ['EC85', 'EC86', 'EC87', 'EABL', 'EABLG'],
        'move-in': ['ES21', 'ES22', 'ES23', 'ES31'],
        'move-out': ['ES32', 'ES33', 'ES41', 'ES42'],
        'device-management': ['EL31', 'EL32', 'EL33', 'EL34'],
        'dunning': ['FKKVKP', 'FKKVK', 'DFKKKO'],
        'contracts': ['EC01', 'EC02', 'EC03', 'EC10']
    }
    
    @classmethod
    def extract_tcodes(cls, text: str) -> List[str]:
        """Extraer t-codes del texto"""
        found_tcodes = cls.TCODE_PATTERN.findall(text.upper())
        # Filtrar solo t-codes IS-U conocidos
        return list(set(tcode for tcode in found_tcodes if tcode in cls.ISU_TCODES))
    
    @classmethod
    def extract_tables(cls, text: str) -> List[str]:
        """Extraer tablas del texto"""
        found_tables = cls.TABLE_PATTERN.findall(text.upper())
        # Filtrar solo tablas IS-U conocidas
        return list(set(table for table in found_tables if table in cls.ISU_TABLES))
    
    @classmethod
    def detect_z_objects(cls, text: str) -> List[str]:
        """Detectar objetos Z/Y en el texto"""
        return list(set(cls.Z_OBJECT_PATTERN.findall(text.upper())))
    
    @classmethod
    def infer_topic(cls, tcodes: List[str], tables: List[str], text: str) -> Optional[str]:
        """Inferir tema basado en t-codes, tablas y contenido"""
        text_lower = text.lower()
        
        # Buscar por t-codes
        for topic, topic_tcodes in cls.TOPIC_MAPPING.items():
            if any(tcode in tcodes for tcode in topic_tcodes):
                return topic
        
        # Buscar por palabras clave en texto
        if any(word in text_lower for word in ['factura', 'billing', 'lectura', 'consumo']):
            return 'billing'
        elif any(word in text_lower for word in ['alta', 'move-in', 'conexion', 'suministro']):
            return 'move-in'
        elif any(word in text_lower for word in ['baja', 'move-out', 'desconexion']):
            return 'move-out'
        elif any(word in text_lower for word in ['aparato', 'device', 'contador', 'medidor']):
            return 'device-management'
        elif any(word in text_lower for word in ['reclamacion', 'dunning', 'impago']):
            return 'dunning'
        elif any(word in text_lower for word in ['contrato', 'contract']):
            return 'contracts'
        
        return None
    
    @classmethod
    def infer_system(cls, tcodes: List[str], tables: List[str]) -> Optional[str]:
        """Inferir sistema basado en t-codes y tablas"""
        if tcodes or tables:
            return 'IS-U'
        return None


class DocumentProcessor:
    """Procesador principal de documentos"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()
        self.llm_service = LLMService()
        self.file_parser = FileParser()
    
    async def process_document(
        self,
        ingest_data: DocumentIngest,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> DocumentResponse:
        """Procesar y almacenar documento completo"""
        
        # 1. Extraer texto si es archivo
        if ingest_data.text is None:
            raise ValueError("Text content is required")
        
        text = ingest_data.text
        
        # 2. Extraer metadatos automáticamente
        extracted_metadata = self._extract_metadata(text)
        
        # 3. Combinar con metadatos proporcionados
        final_metadata = self._merge_metadata(extracted_metadata, ingest_data.metadata)
        
        # 4. Detectar objetos Z y validar scope
        z_objects = MetadataExtractor.detect_z_objects(text)
        scope = self._determine_scope(ingest_data.scope, z_objects, ingest_data.force_scope)
        
        # 5. Estructurar contenido con LLM
        structured = await self._structure_content(text, ingest_data.structured)
        
        # 6. Validar y limpiar
        warnings = self._validate_content(scope, z_objects, text)
        
        # 7. Generar hash para deduplicación
        content_hash = self.embedding_service.generate_content_hash(text)
        
        # 8. Verificar duplicados
        existing_doc = await self._check_duplicate(content_hash, ingest_data.tenant_slug, db)
        if existing_doc:
            return await self._handle_duplicate(existing_doc, structured, db)
        
        # 9. Crear documento en DB
        document = await self._create_document(
            ingest_data, final_metadata, structured, scope, content_hash, user_id, db
        )
        
        # 10. Procesar chunks y embeddings
        chunks_count = await self._process_chunks(document, text, db)
        
        return DocumentResponse(
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
            chunks_count=chunks_count,
            created_at=document.created_at,
            warnings=warnings
        )
    
    def _extract_metadata(self, text: str) -> DocumentMetadata:
        """Extraer metadatos del texto"""
        tcodes = MetadataExtractor.extract_tcodes(text)
        tables = MetadataExtractor.extract_tables(text)
        topic = MetadataExtractor.infer_topic(tcodes, tables, text)
        system = MetadataExtractor.infer_system(tcodes, tables)
        
        return DocumentMetadata(
            tenant_slug="",  # Se asigna después
            tcodes=tcodes,
            tables=tables,
            topic=topic,
            system=system
        )
    
    def _merge_metadata(
        self, 
        extracted: DocumentMetadata, 
        provided: Optional[DocumentMetadata]
    ) -> DocumentMetadata:
        """Combinar metadatos extraídos con los proporcionados"""
        if not provided:
            return extracted
        
        return DocumentMetadata(
            tenant_slug=provided.tenant_slug or extracted.tenant_slug,
            scope=provided.scope or extracted.scope,
            system=provided.system or extracted.system,
            topic=provided.topic or extracted.topic,
            tcodes=list(set((provided.tcodes or []) + (extracted.tcodes or []))),
            tables=list(set((provided.tables or []) + (extracted.tables or []))),
            tags=provided.tags or []
        )
    
    def _determine_scope(
        self, 
        requested_scope: Optional[str], 
        z_objects: List[str], 
        force_scope: bool
    ) -> str:
        """Determinar scope final del documento"""
        has_z_objects = len(z_objects) > 0
        
        if requested_scope == "STANDARD":
            if has_z_objects and not force_scope:
                # Tiene objetos Z pero quiere STANDARD sin forzar
                return "CLIENT_SPECIFIC"
            return "STANDARD"
        elif requested_scope == "CLIENT_SPECIFIC":
            return "CLIENT_SPECIFIC"
        else:
            # Auto-detectar
            return "CLIENT_SPECIFIC" if has_z_objects else "STANDARD"
    
    async def _structure_content(
        self, 
        text: str, 
        provided_structure: Optional[DocumentStructured]
    ) -> DocumentStructured:
        """Estructurar contenido usando LLM"""
        if provided_structure:
            return provided_structure
        
        try:
            return await self.llm_service.extract_structure(text)
        except Exception as e:
            logger.warning(f"Failed to structure content with LLM: {e}")
            return DocumentStructured()
    
    def _validate_content(self, scope: str, z_objects: List[str], text: str) -> List[str]:
        """Validar contenido y generar warnings"""
        warnings = []
        
        if scope == "STANDARD" and z_objects:
            warnings.append(f"STANDARD document contains Z objects: {', '.join(z_objects[:3])}")
        
        if len(text) < 50:
            warnings.append("Document content is very short")
        
        if len(text) > 50000:
            warnings.append("Document content is very long, chunking may be suboptimal")
        
        return warnings
    
    async def _check_duplicate(
        self, 
        content_hash: str, 
        tenant_slug: str, 
        db: AsyncSession
    ) -> Optional[Document]:
        """Verificar si ya existe documento con el mismo hash"""
        stmt = select(Document).where(
            Document.hash == content_hash,
            Document.tenant_slug == tenant_slug
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _handle_duplicate(
        self, 
        existing_doc: Document, 
        new_structure: DocumentStructured, 
        db: AsyncSession
    ) -> DocumentResponse:
        """Manejar documento duplicado - posible actualización"""
        # Por ahora, solo incrementar versión si hay cambios en estructura
        if (new_structure.title and new_structure.title != existing_doc.title) or \
           (new_structure.root_cause and new_structure.root_cause != existing_doc.root_cause):
            
            existing_doc.version += 1
            if new_structure.title:
                existing_doc.title = new_structure.title
            if new_structure.root_cause:
                existing_doc.root_cause = new_structure.root_cause
            if new_structure.steps:
                existing_doc.steps = new_structure.steps
            if new_structure.risks:
                existing_doc.risks = new_structure.risks
            
            await db.commit()
        
        chunks_count = len(existing_doc.chunks) if existing_doc.chunks else 0
        
        return DocumentResponse(
            id=existing_doc.id,
            tenant_slug=existing_doc.tenant_slug,
            scope=existing_doc.scope,
            type=existing_doc.type,
            title=existing_doc.title,
            system=existing_doc.system,
            topic=existing_doc.topic,
            tcodes=existing_doc.tcodes or [],
            tables=existing_doc.tables or [],
            version=existing_doc.version,
            chunks_count=chunks_count,
            created_at=existing_doc.created_at,
            warnings=["Document already exists, updated version"]
        )
    
    async def _create_document(
        self,
        ingest_data: DocumentIngest,
        metadata: DocumentMetadata,
        structured: DocumentStructured,
        scope: str,
        content_hash: str,
        user_id: uuid.UUID,
        db: AsyncSession
    ) -> Document:
        """Crear documento en base de datos"""
        document = Document(
            tenant_slug=ingest_data.tenant_slug,
            scope=scope,
            type=ingest_data.type,
            system=metadata.system,
            topic=metadata.topic,
            tcodes=metadata.tcodes,
            tables=metadata.tables,
            title=structured.title,
            root_cause=structured.root_cause,
            steps=structured.steps,
            risks=structured.risks,
            tags=metadata.tags,
            source=ingest_data.source,
            hash=content_hash,
            created_by=user_id
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        return document
    
    async def _process_chunks(self, document: Document, text: str, db: AsyncSession) -> int:
        """Procesar texto en chunks y crear embeddings"""
        # Crear chunks
        chunks_data = self.embedding_service.chunk_text(text)
        
        if len(chunks_data) > settings.max_chunks_per_doc:
            logger.warning(f"Document {document.id} has {len(chunks_data)} chunks, truncating to {settings.max_chunks_per_doc}")
            chunks_data = chunks_data[:settings.max_chunks_per_doc]
        
        # Obtener embeddings
        chunk_texts = [chunk['content'] for chunk in chunks_data]
        embeddings = await self.embedding_service.get_embeddings(chunk_texts)
        
        # Preparar puntos para Qdrant
        qdrant_points = []
        chunk_records = []
        
        for i, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings)):
            chunk_id = str(uuid.uuid4())
            point_id = f"{document.id}_{i}"
            
            # Punto para Qdrant
            qdrant_points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "tenant": document.tenant_slug,
                    "scope": document.scope,
                    "system": document.system,
                    "topic": document.topic,
                    "tcodes": document.tcodes or [],
                    "tables": document.tables or [],
                    "date": document.created_at.isoformat(),
                    "source": document.source,
                    "doc_id": str(document.id),
                    "chunk_index": chunk_data['index'],
                    "content": chunk_data['content'][:500]  # Solo primeros 500 chars para búsqueda
                }
            ))
            
            # Registro para Postgres
            chunk_records.append(Chunk(
                id=uuid.UUID(chunk_id),
                document_id=document.id,
                chunk_index=chunk_data['index'],
                content=chunk_data['content'],
                token_count=chunk_data['token_count'],
                qdrant_point_id=point_id
            ))
        
        # Insertar en Qdrant
        await self.qdrant_service.upsert_points(qdrant_points)
        
        # Insertar chunks en Postgres
        db.add_all(chunk_records)
        await db.commit()
        
        return len(chunk_records)
