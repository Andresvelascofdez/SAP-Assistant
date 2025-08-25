# 🚀 Deployment Guide - SAP IS-U Smart Wiki

## Quick Start (Single-User Mode)

### Prerequisites
- Python 3.11+
- Docker Desktop
- OpenAI API key

### Installation Steps

1. **Clone Repository**
```bash
git clone https://github.com/Andresvelascofdez/SAP-Assistant.git
cd SAP-Assistant
```

2. **Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your OpenAI API key
# OPENAI_API_KEY=sk-proj-[YOUR_API_KEY]
# LLM_MODEL=gpt-4o-mini
# EMBEDDING_MODEL=text-embedding-3-small
```

3. **Start Infrastructure**
```bash
# Start PostgreSQL and Qdrant
docker-compose up -d
```

4. **Python Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

5. **Start Application**
```bash
# Start FastAPI server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

6. **Access Application**
- **Main Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Production Deployment

### Docker Compose (Recommended)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/sapisu
      - QDRANT_URL=http://qdrant:6333
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - qdrant
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: sapisu
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

volumes:
  postgres_data:
  qdrant_data:
```

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-proj-your-key-here
DATABASE_URL=postgresql+asyncpg://postgres:changeme@localhost:5432/sapisu
QDRANT_URL=http://localhost:6333

# Optional
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
QDRANT_COLLECTION=sapisu_knowledge
JWT_SECRET=your-secret-key
```

### Health Checks

The application provides comprehensive health checks:

```bash
# Basic health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/health/detailed
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "qdrant": "connected", 
    "openai": "authenticated"
  },
  "timestamp": "2025-08-26T15:30:00Z"
}
```

## Multi-Tenant Setup

### Database Configuration

1. **Run Migrations**
```bash
cd api
alembic upgrade head
```

2. **Create Tenants**
```bash
# Use admin interface or API
POST /api/v1/admin/tenants
{
  "slug": "client-name",
  "name": "Client Display Name",
  "timezone": "Europe/Madrid"
}
```

3. **Create Users**
```bash
POST /api/v1/admin/users
{
  "email": "user@client.com",
  "password": "secure-password",
  "role": "user",
  "tenant_slug": "client-name"
}
```

### Authentication Flow

```bash
# Login
POST /api/v1/auth/login
{
  "email": "user@client.com",
  "password": "password"
}

# Use token in subsequent requests
Authorization: Bearer <jwt-token>
```

## Monitoring & Maintenance

### Logs

```bash
# Application logs
docker-compose logs -f app

# Database logs  
docker-compose logs -f postgres

# Vector database logs
docker-compose logs -f qdrant
```

### Backup Strategy

```bash
# PostgreSQL backup
docker exec sapisu_postgres pg_dump -U postgres sapisu > backup_$(date +%Y%m%d).sql

# Qdrant backup
curl -X POST "http://localhost:6333/collections/sapisu_knowledge/snapshots"
```

### Performance Tuning

1. **Database Optimization**
```sql
-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_documents_system_topic ON documents(system, topic);
CREATE INDEX CONCURRENTLY idx_chunks_content_gin ON chunks USING gin(to_tsvector('spanish', content));
```

2. **Qdrant Optimization**
```python
# Increase RAM buffer for better performance
# Edit qdrant config.yaml
storage:
  optimizers:
    deleted_threshold: 0.2
    vacuum_min_vector_number: 1000
```

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
```bash
# Check API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Verify model access
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"test"}]}' \
     https://api.openai.com/v1/chat/completions
```

2. **Database Connection**
```bash
# Test PostgreSQL
docker exec -it sapisu_postgres psql -U postgres -d sapisu -c "SELECT version();"

# Check tables
docker exec -it sapisu_postgres psql -U postgres -d sapisu -c "\dt"
```

3. **Qdrant Issues**
```bash
# Check collection
curl http://localhost:6333/collections/sapisu_knowledge

# View collection info
curl http://localhost:6333/collections/sapisu_knowledge/info
```

### Error Resolution

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing dependencies | `pip install -r requirements.txt` |
| `Connection refused` | Service not running | `docker-compose up -d` |
| `401 Unauthorized` | Invalid OpenAI key | Check `.env` file |
| `404 Model not found` | Wrong model name | Update to `gpt-4o-mini` |
| `500 Internal Error` | Database migration | Run `alembic upgrade head` |

## Security Considerations

### Production Security

1. **Environment Variables**
```bash
# Use strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)
```

2. **Network Security**
```yaml
# docker-compose.prod.yml
networks:
  internal:
    driver: bridge
    internal: true
```

3. **API Rate Limiting**
```python
# In production, add rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.add_middleware(SlowAPIMiddleware)
```

### Data Protection

- All data is stored locally (PostgreSQL + Qdrant)
- OpenAI API calls are encrypted in transit
- No data is shared between tenants
- Regular backups recommended

## Scaling Considerations

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  app:
    deploy:
      replicas: 3
    
  nginx:
    image: nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - app
```

### Database Scaling

```sql
-- Read replicas for search-heavy workloads
-- Partitioning for large datasets
CREATE TABLE documents_2025 PARTITION OF documents
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

This deployment guide ensures a robust, scalable SAP IS-U Smart Wiki installation suitable for both development and production environments.
