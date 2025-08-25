# SAP IS-U Smart Wiki - Technical Documentation

---

## Executive Summary

SAP IS-U Smart Wiki is an advanced Retrieval-Augmented Generation (RAG) platform for SAP IS-U consultants. It enables secure, multi-tenant knowledge management, semantic search, and conversational assistance, leveraging state-of-the-art AI and robust backend infrastructure. This document provides a comprehensive, step-by-step technical overview, including system operation, data storage, response generation, and practical usage for onboarding and IP Box submission.

## 1. Project Overview

SAP IS-U Smart Wiki is a Retrieval-Augmented Generation (RAG) system designed for SAP IS-U consultants. It enables intelligent search, document management, and conversational assistance, with a focus on multi-tenant security and domain-specific knowledge extraction.

### Key Features

- Multi-tenant architecture for client isolation
- Secure document ingestion and metadata extraction
- Semantic search and conversational Q&A
- Source citation and document management
- Automated backups and maintenance

## 2. System Architecture & Data Flow

### 2.1 High-Level Diagram

```
[User] → [Web UI/API] → [FastAPI Backend]
    ├─> [PostgreSQL: Metadata, Users, Documents]
    ├─> [Qdrant: Vector Embeddings]
    ├─> [OpenAI API: Embeddings, LLM]
    └─> [Scheduler: Backups, Maintenance]
```

### 2.2 Component Details

- **Web UI**: SPA for document upload, search, chat, and management. Authenticates users and routes requests.
- **FastAPI Backend**: Central API server. Handles authentication, ingestion, search, chat, and document management. Implements multi-tenant logic and security.
- **PostgreSQL**: Relational DB for all metadata (users, tenants, documents, chunks, logs, queries). Ensures tenant isolation and fast lookups.
- **Qdrant**: Vector DB for semantic search. Stores embeddings for each document chunk, indexed by tenant and scope.
- **OpenAI API**: Used for generating embeddings (text-embedding-ada-002 or similar) and LLM responses (GPT-3.5/4).
- **Scheduler (APScheduler)**: Automates backups, log cleanup, and periodic maintenance tasks.

## 3. Data Model & Storage Logic

### 3.1 Main Entities

- **User**: Authenticated consultant, linked to a tenant. Has roles and access scopes.
- **Tenant**: Logical client separation. All data is isolated per tenant.
- **Document**: Uploaded knowledge (PDF, DOCX, HTML, MD, TXT, or plain text). Contains SAP IS-U metadata.
- **Chunk**: Each document is split into overlapping chunks (800-1000 tokens, 100-150 overlap) for embedding and search.
- **Embedding**: Vector representation of each chunk, generated via OpenAI API.
- **EvalQuery/EvalRun**: For evaluating RAG quality and search performance.

### 3.2 Storage Logic

- **PostgreSQL**: Stores all metadata, relations, and logs. Key tables: tenants, users, documents, chunks, eval_queries, eval_runs.
- **Qdrant**: Stores embeddings for each chunk, indexed by tenant, document, and scope (STANDARD, CLIENT_SPECIFIC).
- **Chunking & Embedding**: On ingestion, documents are split, embedded, and stored. Metadata includes SAP IS-U T-codes, tables, and custom objects (extracted via regex/domain rules).

## 4. System Operation: End-to-End Flow

### 4.1 Ingestion Pipeline (How Information is Stored)

1. **Upload**: User uploads a document or text via Web UI or API.
2. **Metadata Extraction**: System parses the document, extracting SAP IS-U metadata (T-codes, tables, custom objects) using regex and domain-specific rules.
3. **Chunking**: Document is split into overlapping chunks (800-1000 tokens, 100-150 overlap) to optimize semantic search.
4. **Embedding Generation**: Each chunk is sent to OpenAI API to generate a vector embedding.
5. **Storage**:
   - Chunks and metadata are stored in PostgreSQL (with tenant, document, and scope info).
   - Embeddings are stored in Qdrant, indexed by tenant and chunk ID.
6. **Indexing**: Chunks are indexed for fast retrieval and search.

### 4.2 Semantic Search (How Answers are Generated)

1. **Query Submission**: User enters a query via Web UI or API.
2. **Query Embedding**: Query is embedded using OpenAI API.
3. **Vector Search**: Qdrant performs a similarity search, retrieving top-N relevant chunks (filtered by tenant and scope).
4. **Re-ranking**: Results are optionally re-ranked for relevance (future: hybrid BM25 + vector, reranker models).
5. **Source Citation**: Each result includes source document, chunk, and metadata.
6. **Response Construction**: Chunks are assembled and presented to the user, with source links.

### 4.3 Conversational Chat (RAG Pipeline)

1. **User Question**: User asks a natural language question.
2. **Context Retrieval**: System retrieves relevant chunks using semantic search (as above).
3. **LLM Generation**: OpenAI LLM (GPT-3.5/4) receives the question and retrieved context, generating a detailed answer.
4. **Source Attribution**: Answer includes citations to source documents/chunks.

### 4.4 Multi-Tenant Security

- All data access is filtered by tenant and scope (STANDARD, CLIENT_SPECIFIC).
- JWT authentication and role-based access control.
- Strict isolation: No cross-tenant data leakage.

### 4.5 Document Management

- Upload, view, and manage documents per tenant.
- Automatic extraction of SAP IS-U metadata.
- Support for PDF, DOCX, HTML, Markdown, TXT.

### 4.6 Backups & Maintenance

- APScheduler automates backups of PostgreSQL and Qdrant.
- Periodic log cleanup and reindexing.
- Manual and scheduled backup options.

---

## 4.7 Example User Flows

### A. Adding Knowledge

1. Log in via Web UI.
2. Upload a SAP IS-U document (PDF, DOCX, TXT, etc.).
3. System extracts metadata, splits into chunks, generates embeddings, and stores all data securely.
4. Document is now searchable and available for chat.

### B. Searching for Information

1. Enter a query in the search bar (e.g., "How to configure rate categories in SAP IS-U?").
2. System embeds the query, retrieves relevant chunks, and displays results with source citations.

### C. Conversational Assistance

1. Ask a question in the chat interface.
2. System retrieves context, sends to LLM, and returns a detailed answer with sources.

### D. Managing Documents

1. View, edit, or delete documents in the UI.
2. Download or export documents as needed.

### E. Backups & Maintenance

1. Backups run automatically; manual backup available via API or script.
2. Admins can restore from backup if needed.

## 5. Integration Points

### 5.1 OpenAI API

- Used for embeddings and chat responses.
- Configurable API key and model selection.

### 5.2 Qdrant Vector DB

- Stores all document and chunk embeddings.
- Supports metadata filtering for tenant isolation.

### 5.3 PostgreSQL

- Stores all metadata, user info, and document relations.
- Alembic used for migrations.

---

## 6. Extensibility & Customization

- Modular FastAPI backend: easy to add new endpoints or services.
- Pluggable parsers for new document formats.
- Customizable chunking and embedding strategies.
- Future support for hybrid search (BM25 + vector) and re-ranking.
- Export to PDF/Word via python-docx, reportlab, or pandoc.

---

## 7. Security & Compliance

- JWT authentication and refresh tokens.
- Strict tenant isolation enforced at all layers.
- CORS and rate limiting for API security.
- GDPR compliance: data portability, deletion, privacy by design.
- AES-256 encryption at rest, TLS 1.3 in transit.

---

## 8. Usage Guide

### 8.1 Setup

- Clone repo, configure `.env`, install dependencies.
- Run `docker-compose up` for full stack.
- Access Web UI at `http://localhost:3000`.

### 8.2 Adding Knowledge

- Use Web UI or API to upload documents or text.
- System extracts metadata and chunks automatically.
- Chunks are embedded and stored for search.

### 8.3 Searching & Chat

- Use Web UI to search or ask questions.
- Results are filtered by tenant and scope.
- Chat answers cite sources and can be saved as documents.

### 8.4 Backups & Maintenance

- Backups run automatically via scheduler.
- Manual backup available via API or script.

---

## 9. Future Improvements

- Hybrid search (BM25 + vector)
- Re-ranking with bge-reranker or GPT
- Export answers to PDF/Word
- Feedback system for answer quality
- Multi-language support
- Advanced analytics (personal productivity dashboard)

---

## 10. References & Dependencies

- FastAPI, SQLAlchemy, Alembic
- Qdrant-client
- OpenAI, tiktoken
- python-docx, pdfminer.six, beautifulsoup4
- APScheduler, bcrypt, python-jose, slowapi
- pytest, httpx

---

## 11. Contact & Support

- For technical questions, refer to the README or contact the project owner.
- For onboarding, see the installation and usage guides above.

---

_This documentation is suitable for IP Box submission and onboarding of third-party users or developers._
