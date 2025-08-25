# 🔍 SAP IS-U Smart Wiki

A complete multi-tenant RAG (Retrieval-Augmented Generation) solution for SAP IS-U consultants that provides intelligent search, document management, and specialized conversational assistant with **ChatGPT-style interface**.

## 🌟 Key Features

### 🎯 Core Functionalities

- **🤖 ChatGPT-Style Interface**: Modern conversational UI with real-time responses
- **📝 Incident Management**: Save and retrieve SAP IS-U incidents as structured knowledge
- **🔍 Multi-tenant RAG**: Complete client isolation with STANDARD and CLIENT_SPECIFIC scopes
- **🧠 Intelligent Search**: Vector embeddings with Qdrant and OpenAI GPT-4o-mini
- **💬 Conversational Chat**: SAP IS-U specialized assistant with contextual memory
- **📚 Document Management**: Automatic processing of PDF, DOCX, HTML, MD files
- **🔐 Flexible Authentication**: JWT system or public mode for single-user deployment
- **🚀 Complete REST API**: FastAPI with automatic documentation
- ✅ Automatic SAP metadata extraction (t-codes, tables, topics)
- ✅ Persistent knowledge base across sessions
- ✅ Production-ready Docker deployment

## 🏗️ Architecture

```
[ChatGPT Interface] → [FastAPI] → [PostgreSQL]
                                → [Qdrant Vector DB]
                                → [OpenAI API]
```

## 🤖 AI Configuration

This system leverages **GPT-4o-mini** for cost-effective conversational capabilities and **text-embedding-3-small** for semantic search. Key AI features:

- **💡 Smart Reasoning**: GPT-4o-mini provides excellent understanding of SAP IS-U technical concepts
- **📖 Source Attribution**: All responses include precise citations to source documents
- **🧠 Context Awareness**: Maintains conversation history and domain-specific knowledge
- **🌍 Multi-language Support**: Works with Spanish, English, and technical SAP terminology
- **💾 Persistent Memory**: Incidents and knowledge accumulate over time

### OpenAI Models Used
- **LLM**: `gpt-4o-mini` - For chat responses and content structuring
- **Embeddings**: `text-embedding-3-small` - For semantic search and similarity matching
- **API Key**: See [OpenAI Configuration Guide](docs/OPENAI_CONFIG.md) for setup instructions

## 🚀 Quick Installation

### ⚡ One-Click Startup (Recommended)

**Windows (PowerShell):**
```powershell
# 1. Clone repository
git clone https://github.com/Andresvelascofdez/SAP-Assistant.git
cd SAP-Assistant

# 2. Configure API key
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. One-click start!
.\start-sapisu-wiki.ps1
```

**Linux/macOS:**
```bash
# 1. Clone repository
git clone https://github.com/Andresvelascofdez/SAP-Assistant.git
cd SAP-Assistant

# 2. Configure API key
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. One-click start!
chmod +x start-sapisu-wiki.sh
./start-sapisu-wiki.sh
```

**What the script does:**
- ✅ Stops any existing services
- ✅ Verifies all prerequisites 
- ✅ Starts Docker services (PostgreSQL + Qdrant)
- ✅ Configures Python environment
- ✅ Launches FastAPI server
- ✅ Opens browser automatically
- ✅ Monitors services continuously

### Option 1: Single-User Setup

```bash
git clone https://github.com/Andresvelascofdez/SAP-Assistant.git
cd SAP-Assistant
cp .env.example .env
# Edit .env with your OpenAI API key (see docs/OPENAI_CONFIG.md)
```

### Option 2: Multi-Tenant Setup

```bash
# Same as above, then configure authentication
# See docs/DEPLOYMENT.md for full multi-tenant setup
```

## 🖥️ Usage

### 💬 Chat Interface

1. **Open your browser**: Navigate to `http://localhost:8000`
2. **Start chatting**: Ask questions about SAP IS-U directly
3. **Save incidents**: Click "💾 Guardar Incidencia" to store new knowledge
4. **Upload documents**: Use 📎 button to process PDF/Word files

### 📝 Incident Management

1. **Click "💾 Guardar Incidencia"**
2. **Fill the form**:
   - Title: Brief description
   - System: IS-U, CRM, FI, SD, etc.
   - Topic: billing, move-in, readings, etc.
   - Description: Detailed incident information
   - Tags: Keywords for better search
3. **Save**: Knowledge is permanently stored
4. **Query later**: Chat will find and use stored incidents

### 🔍 Examples

**Query**: "¿Cómo resolver errores de facturación en IS-U?"
**Response**: AI searches stored incidents and provides contextual answers

**Save**: Document a billing issue resolution for future reference
**Retrieve**: System automatically suggests similar solutions

## 🐳 Docker Deployment

### Quick Start (Single-User)

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Start application
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# 4. Access application
# Open http://localhost:8000
```

### Production Deployment

```bash
# Full Docker setup with Traefik
docker-compose -f docker-compose.prod.yml up -d
```

## 🛠️ Development Setup

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

4. **Access interfaces**

- **Main Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
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
