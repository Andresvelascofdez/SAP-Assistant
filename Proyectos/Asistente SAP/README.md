# 🔍 SAP IS-U Smart Wiki

A complete multi-tenant RAG (Retrieval-Augmented Generation) solution for SAP IS-U consultants that provides intelligent search, document management, and specialized conversational assistant.

## 🌟 Key Features

### 🎯 Core Functionalities

- **Multi-tenant RAG**: Complete client isolation with STANDARD and CLIENT_SPECIFIC scopes
- **Intelligent Search**: Vector embeddings with Qdrant and OpenAI
- **Conversational Chat**: SAP IS-U specialized assistant with GPT-3.5-turbo
- **Document Management**: Automatic processing of PDF, DOCX, HTML, MD
- **JWT Authentication**: Secure system with user roles
- **Complete REST API**: FastAPI with automatic documentation
- ✅ Automatic SAP metadata extraction (t-codes, tables, topics)
- ✅ Single window UI with Add/Ask modes
- ✅ Automated backups and quality metrics

## Architecture

```
[Client] → [Traefik] → [FastAPI] → [PostgreSQL]
                                 → [Qdrant]
                                 → [APScheduler]
```

## Quick Installation

1. **Clone and configure environment**

```bash
git clone <repo>
cd Asistente-SAP
cp .env.example .env
# Edit .env with your credentials
```

2. **Launch with Docker Compose**

```bash
docker-compose up -d
```

3. **Access the application**

- Web UI: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development Installation

1. **Install dependencies**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure database**

```bash
# Start PostgreSQL and Qdrant
docker-compose up -d postgres qdrant

# Run migrations
cd api
alembic upgrade head
```

3. **Run API**

```bash
cd api
uvicorn main:app --reload --port 8000
```

4. **Run frontend (optional)**

```bash
cd web
npm install
npm run dev
```

## Basic Usage

### Adding content

1. Select client (tenant)
2. Switch to "Add" mode
3. Write incident or drag file
4. System automatically extracts metadata (t-codes, tables, topic)
5. Confirm and save

### Querying knowledge

1. Select client (tenant)
2. Switch to "Ask" mode
3. Write question in natural language
4. Receive response with detailed steps and cited sources

### Special commands

- `/add` - Switch to add mode
- `/ask` - Switch to ask mode
- `/tenant CLIENT_X` - Change tenant
- `/std` - Switch to STANDARD tenant

## Project Structure

```
├── api/                    # FastAPI Backend
│   ├── routers/           # REST Endpoints
│   ├── models/            # Pydantic Models
│   ├── db/                # SQLAlchemy + Alembic
│   ├── services/          # Business Logic
│   └── utils/             # Utilities
├── scheduler/             # Scheduled Tasks
├── scripts/               # Utility Scripts
├── deploy/               # Docker Compose
├── tests/                # Unit and Integration Tests
└── CHANGELOG.md          # Project Changelog
```

## Security

- ✅ JWT authentication with refresh tokens
- ✅ Strict tenant segregation (never leaks information between clients)
- ✅ Rate limiting per IP and user
- ✅ Input validation and sanitization
- ✅ Audit logs without sensitive information
- ✅ Automatic Z/Y object detection to prevent leaks

## Metrics and Quality

- ✅ Automatic RAG evaluation (hit@k, nDCG@k)
- ✅ Anti-leak canaries between tenants
- ✅ Usage and performance metrics
- ✅ Automatic daily backups

## Development

### Tests

```bash
pytest tests/ -v --cov=api
```

### Linting

```bash
ruff check api/
black api/
mypy api/
```

### DB Migrations

```bash
cd api
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Advanced Configuration

This project includes all necessary configuration files. The system is ready to run with the provided setup scripts and docker-compose configuration.

For production deployment, ensure proper environment variables are set in `.env` file and SSL certificates are configured for Traefik.

## License

Proprietary - Do not redistribute without authorization

## Support

For issues and questions, create a ticket in the internal repository.
