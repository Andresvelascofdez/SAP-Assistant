# 📝 Incident Management System

## Overview

The SAP IS-U Smart Wiki includes a complete incident management system that allows users to save, categorize, and retrieve technical knowledge as persistent, searchable content.

## Features

### 💾 Incident Storage
- **Structured Input**: Modal form with SAP-specific categorization
- **Free-text Description**: Full incident details with root cause analysis
- **Automatic Metadata**: System, topic, tags, and timestamps
- **Persistent Storage**: PostgreSQL + Qdrant vector database

### 🔍 Intelligent Retrieval
- **Semantic Search**: Find incidents by context, not just keywords
- **Multi-modal Matching**: Title, description, tags, and content
- **Confidence Scoring**: Relevance indicators for each match
- **Source Attribution**: Clear references to original incidents

## Usage Workflow

### 1. Saving Incidents

1. **Click "💾 Guardar Incidencia"** in the chat interface
2. **Fill the structured form**:
   - **Title**: Brief, descriptive incident name
   - **System**: SAP module (IS-U, CRM, FI, SD, Other)
   - **Topic**: Functional area (billing, move-in, readings, etc.)
   - **Description**: Detailed incident information including:
     - Problem description
     - Root cause analysis
     - Solution steps
     - TCodes and tables involved
     - Preventive measures
   - **Tags**: Keywords for enhanced searchability
3. **Save**: Incident is processed and stored permanently

### 2. Retrieving Knowledge

**Through Chat Interface**:
- Ask questions naturally: "¿Cómo resolver errores de facturación automática?"
- System searches stored incidents using semantic similarity
- Responses include relevant incident context and sources

**Automatic Context**:
- New questions automatically search previous incidents
- Related solutions are suggested proactively
- Knowledge builds cumulatively over time

## Technical Implementation

### Data Storage

```sql
-- PostgreSQL Schema
documents (
    id UUID PRIMARY KEY,
    tenant_slug VARCHAR(50),
    scope VARCHAR(20),
    type VARCHAR(20), -- 'incidencia'
    system VARCHAR(50), -- 'IS-U', 'CRM', etc.
    topic VARCHAR(100), -- 'billing', 'move-in', etc.
    title TEXT,
    root_cause TEXT,
    steps TEXT[],
    tags VARCHAR[],
    source TEXT,
    created_at TIMESTAMP
)

chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    content TEXT,
    qdrant_point_id VARCHAR(100)
)
```

### Vector Storage

```python
# Qdrant Collection: sapisu_knowledge
{
    "id": "unique_point_id",
    "vector": [1536_dimensional_embedding],
    "payload": {
        "document_id": "uuid",
        "tenant": "default", 
        "type": "incidencia",
        "system": "IS-U",
        "topic": "billing",
        "title": "Incident title",
        "content": "Full text content",
        "tags": ["tag1", "tag2"],
        "source": "chat-interface",
        "created_at": "2025-08-26T15:30:00Z"
    }
}
```

### API Endpoints

```bash
# Save Incident
POST /api/v1/ingest/text-public
Content-Type: application/json

{
    "tenant_slug": "default",
    "scope": "CLIENT_SPECIFIC",
    "type": "incidencia", 
    "system": "IS-U",
    "topic": "billing",
    "title": "Error en cálculo de consumo",
    "text": "Full incident description...",
    "tags": ["estimacion", "consumo", "EG02"],
    "source": "chat-interface"
}

# Search/Chat
POST /api/v1/search/chat-public
Content-Type: application/json

{
    "query": "problema con estimación de consumo",
    "tenant_slug": "default"
}
```

## Best Practices

### Writing Effective Incidents

1. **Descriptive Titles**: Use specific, searchable titles
   - ✅ "Error cálculo consumo estimado contratos GAS_INDUSTRIAL"
   - ❌ "Problema facturación"

2. **Structured Descriptions**:
   ```
   PROBLEMA:
   [Clear description of the issue]
   
   CAUSA RAÍZ:
   [Technical root cause analysis]
   
   SOLUCIÓN:
   1. [Step-by-step resolution]
   2. [Include TCodes and tables]
   3. [Validation steps]
   
   PREVENCIÓN:
   [How to avoid in the future]
   ```

3. **Comprehensive Tags**:
   - Include TCodes: `EG02`, `EC85`, `RGVVBEST`
   - Include tables: `EABLG`, `ERCH`, `EEST`
   - Include concepts: `estimacion`, `consumo`, `facturacion`
   - Include error types: `calculo`, `perfil_carga`, `gas_industrial`

### Search Optimization

1. **Use Natural Language**: Ask questions as you would to a colleague
2. **Include Context**: Mention the SAP module and functional area
3. **Use Synonyms**: System understands variations and technical terms
4. **Reference Specifics**: Mention TCodes, tables, or error messages

## Data Persistence

### Session Continuity
- **PostgreSQL**: Stores all incident metadata permanently
- **Qdrant**: Maintains vector embeddings across restarts
- **Docker Volumes**: Data persists through container restarts
- **No Data Loss**: Knowledge accumulates indefinitely

### Backup Strategy
- **Database Dumps**: Regular PostgreSQL backups
- **Vector Snapshots**: Qdrant collection exports
- **Configuration Files**: Environment and schema versioning

## Example Incident

```json
{
    "title": "Error cálculo consumo estimado contratos GAS_INDUSTRIAL",
    "system": "IS-U",
    "topic": "billing",
    "description": "Al ejecutar facturación automática, el cálculo de consumo estimado falla para contratos con perfil de carga especial. El parámetro ESTIMATION_PROFILE en EABLG no se lee correctamente cuando el tipo es 'GAS_INDUSTRIAL'.\n\nSOLUCIÓN:\n1. Verificar EG02 - configuración perfiles\n2. Revisar EABLG campos EST_PROF y EST_METHOD\n3. Ejecutar RGVVBEST en modo prueba\n4. Validar antes de producción",
    "tags": ["EG02", "EABLG", "estimacion", "consumo", "gas_industrial", "facturacion"]
}
```

This incident becomes permanently searchable and can be retrieved through queries like:
- "problema estimación gas industrial"
- "error EABLG consumo"
- "facturación automática fallos"
- "EG02 configuración estimación"

## Integration with Chat

The incident system seamlessly integrates with the conversational interface:

1. **Proactive Suggestions**: Chat automatically searches incidents for context
2. **Source Attribution**: Responses cite specific incidents as sources
3. **Continuous Learning**: Each new incident improves future responses
4. **Cross-Reference**: Related incidents are automatically linked

This creates a self-improving knowledge base where each solved problem enhances the system's ability to help with similar future issues.
