"""
Servicio de embeddings y vectorización
Wiki Inteligente SAP IS-U
"""
import hashlib
import tiktoken
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model
        self.encoding = tiktoken.encoding_for_model("gpt-4")
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Obtener embeddings para lista de textos"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise
    
    async def get_embedding(self, text: str) -> List[float]:
        """Obtener embedding para un texto"""
        embeddings = await self.get_embeddings([text])
        return embeddings[0]
    
    def count_tokens(self, text: str) -> int:
        """Contar tokens en texto"""
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """Dividir texto en chunks con overlap"""
        chunk_size = chunk_size or settings.chunk_size
        overlap = overlap or settings.chunk_overlap
        
        # Dividir por párrafos primero
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            para_tokens = self.count_tokens(paragraph)
            
            # Si el párrafo solo ya es muy grande, dividirlo por oraciones
            if para_tokens > chunk_size:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    sentence_tokens = self.count_tokens(sentence)
                    
                    if current_tokens + sentence_tokens > chunk_size and current_chunk:
                        # Guardar chunk actual
                        chunks.append({
                            'content': current_chunk.strip(),
                            'index': chunk_index,
                            'token_count': current_tokens
                        })
                        
                        # Comenzar nuevo chunk con overlap
                        if overlap > 0 and current_chunk:
                            overlap_text = self._get_overlap_text(current_chunk, overlap)
                            current_chunk = overlap_text + " " + sentence
                            current_tokens = self.count_tokens(current_chunk)
                        else:
                            current_chunk = sentence
                            current_tokens = sentence_tokens
                        
                        chunk_index += 1
                    else:
                        if current_chunk:
                            current_chunk += ". " + sentence
                        else:
                            current_chunk = sentence
                        current_tokens += sentence_tokens
            
            # Párrafo normal
            elif current_tokens + para_tokens > chunk_size and current_chunk:
                # Guardar chunk actual
                chunks.append({
                    'content': current_chunk.strip(),
                    'index': chunk_index,
                    'token_count': current_tokens
                })
                
                # Comenzar nuevo chunk con overlap
                if overlap > 0 and current_chunk:
                    overlap_text = self._get_overlap_text(current_chunk, overlap)
                    current_chunk = overlap_text + "\n\n" + paragraph
                    current_tokens = self.count_tokens(current_chunk)
                else:
                    current_chunk = paragraph
                    current_tokens = para_tokens
                
                chunk_index += 1
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_tokens += para_tokens
        
        # Agregar último chunk si existe
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'index': chunk_index,
                'token_count': current_tokens
            })
        
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Obtener texto de overlap del final del chunk anterior"""
        words = text.split()
        if len(words) <= 20:  # Si es muy corto, devolver todo
            return text
        
        # Aproximación: tomar últimas palabras que sumen aprox overlap_tokens
        # Regla simple: 1 token ≈ 0.75 palabras
        target_words = max(10, int(overlap_tokens * 0.75))
        return " ".join(words[-target_words:])
    
    def generate_content_hash(self, content: str) -> str:
        """Generar hash del contenido para deduplicación"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


class QdrantService:
    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.qdrant_collection
    
    async def ensure_collection(self):
        """Asegurar que la colección existe"""
        try:
            await self.client.get_collection(self.collection_name)
        except Exception:
            # Crear colección si no existe
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)  # OpenAI embeddings
            )
            
            # Crear índices en payload
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="tenant",
                field_schema="keyword"
            )
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="scope",
                field_schema="keyword"
            )
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="topic",
                field_schema="keyword"
            )
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="system",
                field_schema="keyword"
            )
    
    async def upsert_points(self, points: List[PointStruct]):
        """Insertar o actualizar puntos en Qdrant"""
        await self.ensure_collection()
        await self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    
    async def search(
        self,
        query_vector: List[float],
        tenant_filter: List[str],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Buscar vectores similares con filtros"""
        
        # Construir filtros
        filter_conditions = [
            FieldCondition(
                key="tenant",
                match=MatchValue(value=tenant_filter[0]) if len(tenant_filter) == 1 
                      else MatchValue(value=tenant_filter)
            )
        ]
        
        if filters:
            if filters.get("scope"):
                filter_conditions.append(
                    FieldCondition(key="scope", match=MatchValue(value=filters["scope"]))
                )
            if filters.get("system"):
                filter_conditions.append(
                    FieldCondition(key="system", match=MatchValue(value=filters["system"]))
                )
            if filters.get("topic"):
                filter_conditions.append(
                    FieldCondition(key="topic", match=MatchValue(value=filters["topic"]))
                )
        
        search_result = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=Filter(must=filter_conditions) if filter_conditions else None,
            limit=top_k,
            with_payload=True
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in search_result
        ]
    
    async def delete_points(self, point_ids: List[str]):
        """Eliminar puntos por IDs"""
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=point_ids
        )
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Obtener información de la colección"""
        try:
            info = await self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "status": info.status,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}
