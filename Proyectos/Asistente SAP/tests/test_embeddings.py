"""
Tests unitarios para servicios de embeddings
Wiki Inteligente SAP IS-U
"""
import pytest
from unittest.mock import AsyncMock, patch
from api.services.embeddings import EmbeddingService, QdrantService, MetadataExtractor


class TestMetadataExtractor:
    """Tests para extractor de metadatos"""
    
    def test_extract_tcodes(self):
        """Test extracción de t-codes"""
        text = "Usar EC85 para facturación y ES21 para alta de suministro. También XY99 (no válido)"
        tcodes = MetadataExtractor.extract_tcodes(text)
        
        assert "EC85" in tcodes
        assert "ES21" in tcodes
        assert "XY99" not in tcodes  # No está en lista blanca
    
    def test_extract_tables(self):
        """Test extracción de tablas"""
        text = "Revisar tabla EABLG y también BUT000 para datos de BP. Ignorar ABC"
        tables = MetadataExtractor.extract_tables(text)
        
        assert "EABLG" in tables
        assert "BUT000" in tables
        assert "ABC" not in tables  # Muy corto
    
    def test_detect_z_objects(self):
        """Test detección de objetos Z/Y"""
        text = "Función Z_CUSTOM_BILLING y tabla ZCUSTOM_DATA, más Y_REPORT"
        z_objects = MetadataExtractor.detect_z_objects(text)
        
        assert "Z_CUSTOM_BILLING" in z_objects
        assert "ZCUSTOM_DATA" in z_objects
        assert "Y_REPORT" in z_objects
    
    def test_infer_topic(self):
        """Test inferencia de tema"""
        # Por t-codes
        topic = MetadataExtractor.infer_topic(["EC85"], [], "")
        assert topic == "billing"
        
        # Por contenido
        topic = MetadataExtractor.infer_topic([], [], "problema con facturación")
        assert topic == "billing"
        
        # Sin coincidencias
        topic = MetadataExtractor.infer_topic([], [], "contenido genérico")
        assert topic is None


class TestEmbeddingService:
    """Tests para servicio de embeddings"""
    
    @pytest.mark.asyncio
    async def test_chunk_text(self):
        """Test división en chunks"""
        service = EmbeddingService()
        
        # Texto largo para dividir
        text = "Párrafo 1 con contenido.\n\nPárrafo 2 con más contenido.\n\nPárrafo 3 final."
        chunks = service.chunk_text(text, chunk_size=100, overlap=20)
        
        assert len(chunks) >= 1
        assert all("content" in chunk for chunk in chunks)
        assert all("index" in chunk for chunk in chunks)
        assert all("token_count" in chunk for chunk in chunks)
    
    def test_count_tokens(self):
        """Test conteo de tokens"""
        service = EmbeddingService()
        
        text = "Hola mundo"
        token_count = service.count_tokens(text)
        
        assert isinstance(token_count, int)
        assert token_count > 0
    
    def test_generate_content_hash(self):
        """Test generación de hash"""
        service = EmbeddingService()
        
        text = "Contenido de prueba"
        hash1 = service.generate_content_hash(text)
        hash2 = service.generate_content_hash(text)
        hash3 = service.generate_content_hash("Otro contenido")
        
        assert hash1 == hash2  # Mismo contenido = mismo hash
        assert hash1 != hash3  # Contenido diferente = hash diferente
        assert len(hash1) == 64  # SHA256 hex = 64 caracteres
    
    @pytest.mark.asyncio
    @patch('api.services.embeddings.AsyncOpenAI')
    async def test_get_embeddings(self, mock_openai):
        """Test obtención de embeddings"""
        # Mock de OpenAI response
        mock_response = AsyncMock()
        mock_response.data = [AsyncMock(embedding=[0.1, 0.2, 0.3])]
        
        mock_client = AsyncMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = EmbeddingService()
        service.client = mock_client
        
        embeddings = await service.get_embeddings(["test text"])
        
        assert len(embeddings) == 1
        assert embeddings[0] == [0.1, 0.2, 0.3]
        mock_client.embeddings.create.assert_called_once()


class TestQdrantService:
    """Tests para servicio Qdrant"""
    
    @pytest.mark.asyncio
    @patch('api.services.embeddings.AsyncQdrantClient')
    async def test_search(self, mock_qdrant):
        """Test búsqueda vectorial"""
        # Mock de Qdrant response
        mock_hit = AsyncMock()
        mock_hit.id = "test_id"
        mock_hit.score = 0.95
        mock_hit.payload = {"tenant": "TEST", "content": "test content"}
        
        mock_client = AsyncMock()
        mock_client.search.return_value = [mock_hit]
        mock_qdrant.return_value = mock_client
        
        service = QdrantService()
        service.client = mock_client
        
        results = await service.search(
            query_vector=[0.1, 0.2, 0.3],
            tenant_filter=["TEST"],
            top_k=5
        )
        
        assert len(results) == 1
        assert results[0]["id"] == "test_id"
        assert results[0]["score"] == 0.95
        assert results[0]["payload"]["tenant"] == "TEST"
    
    @pytest.mark.asyncio
    @patch('api.services.embeddings.AsyncQdrantClient')
    async def test_get_collection_info(self, mock_qdrant):
        """Test información de colección"""
        mock_info = AsyncMock()
        mock_info.status = "green"
        mock_info.vectors_count = 100
        mock_info.points_count = 100
        
        mock_client = AsyncMock()
        mock_client.get_collection.return_value = mock_info
        mock_qdrant.return_value = mock_client
        
        service = QdrantService()
        service.client = mock_client
        
        info = await service.get_collection_info()
        
        assert info["status"] == "green"
        assert info["points_count"] == 100


if __name__ == "__main__":
    pytest.main([__file__])
