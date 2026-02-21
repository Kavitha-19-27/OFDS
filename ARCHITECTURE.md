# RAG SaaS Architecture Documentation

## Project Structure

```
rag-saas/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry
│   │   ├── config.py                  # Configuration management
│   │   ├── database.py                # Database connection & session
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                # Dependency injection
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py          # API v1 router aggregator
│   │   │   │   ├── auth.py            # Authentication endpoints
│   │   │   │   ├── users.py           # User management endpoints
│   │   │   │   ├── tenants.py         # Tenant management endpoints
│   │   │   │   ├── documents.py       # Document upload/management
│   │   │   │   └── chat.py            # RAG chat endpoint
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py            # JWT, password hashing
│   │   │   ├── exceptions.py          # Custom exceptions
│   │   │   └── middleware.py          # Rate limiting, error handling
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # Base model with tenant scope
│   │   │   ├── tenant.py              # Tenant model
│   │   │   ├── user.py                # User model
│   │   │   ├── document.py            # Document model
│   │   │   └── chat_log.py            # Chat history model
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # Auth request/response schemas
│   │   │   ├── user.py                # User schemas
│   │   │   ├── tenant.py              # Tenant schemas
│   │   │   ├── document.py            # Document schemas
│   │   │   └── chat.py                # Chat schemas
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py        # Authentication logic
│   │   │   ├── user_service.py        # User CRUD operations
│   │   │   ├── tenant_service.py      # Tenant CRUD operations
│   │   │   ├── document_service.py    # Document management
│   │   │   ├── embedding_service.py   # OpenAI embeddings
│   │   │   ├── vector_service.py      # FAISS operations
│   │   │   ├── rag_service.py         # RAG pipeline orchestration
│   │   │   └── llm_service.py         # LLM interaction
│   │   │
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # Base repository pattern
│   │   │   ├── user_repository.py     # User data access
│   │   │   ├── tenant_repository.py   # Tenant data access
│   │   │   ├── document_repository.py # Document data access
│   │   │   └── chat_repository.py     # Chat log data access
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── pdf_processor.py       # PDF text extraction
│   │       ├── text_chunker.py        # Deterministic chunking
│   │       ├── logger.py              # Structured logging
│   │       └── validators.py          # Input validation helpers
│   │
│   ├── data/
│   │   ├── faiss_indexes/             # Per-tenant FAISS indexes
│   │   └── uploads/                   # Temporary file uploads
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_documents.py
│   │   └── test_chat.py
│   │
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── public/
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── main.jsx                   # React entry point
│   │   ├── App.jsx                    # Root component
│   │   ├── index.css                  # Global styles
│   │   │
│   │   ├── api/
│   │   │   ├── client.js              # Axios instance with interceptors
│   │   │   ├── auth.js                # Auth API calls
│   │   │   ├── documents.js           # Document API calls
│   │   │   └── chat.js                # Chat API calls
│   │   │
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Button.jsx
│   │   │   │   ├── Input.jsx
│   │   │   │   ├── Modal.jsx
│   │   │   │   ├── Spinner.jsx
│   │   │   │   └── Toast.jsx
│   │   │   │
│   │   │   ├── layout/
│   │   │   │   ├── Header.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   └── Layout.jsx
│   │   │   │
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.jsx
│   │   │   │   ├── RegisterForm.jsx
│   │   │   │   └── ProtectedRoute.jsx
│   │   │   │
│   │   │   ├── documents/
│   │   │   │   ├── DocumentList.jsx
│   │   │   │   ├── DocumentUpload.jsx
│   │   │   │   └── DocumentCard.jsx
│   │   │   │
│   │   │   └── chat/
│   │   │       ├── ChatWindow.jsx
│   │   │       ├── ChatMessage.jsx
│   │   │       └── ChatInput.jsx
│   │   │
│   │   ├── contexts/
│   │   │   ├── AuthContext.jsx        # Auth state management
│   │   │   └── ToastContext.jsx       # Toast notifications
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.js
│   │   │   ├── useDocuments.js
│   │   │   └── useChat.js
│   │   │
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Documents.jsx
│   │   │   ├── Chat.jsx
│   │   │   └── Settings.jsx
│   │   │
│   │   └── utils/
│   │       ├── constants.js
│   │       ├── helpers.js
│   │       └── validators.js
│   │
│   ├── .env.example
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
└── README.md
```

## High-Level Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Auth UI   │  │  Documents  │  │  Chat UI    │  │  Settings   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │                 │
│         └────────────────┴────────┬───────┴────────────────┘                 │
│                                   │                                          │
│                          ┌────────▼────────┐                                 │
│                          │   API Client    │                                 │
│                          │  (Axios + JWT)  │                                 │
│                          └────────┬────────┘                                 │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │ HTTPS
                                    │
┌───────────────────────────────────┼─────────────────────────────────────────┐
│                           BACKEND (FastAPI)                                  │
│                                   │                                          │
│  ┌────────────────────────────────▼────────────────────────────────────┐    │
│  │                         API Gateway Layer                            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │    CORS      │  │ Rate Limiter │  │  JWT Auth    │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └────────────────────────────────┬────────────────────────────────────┘    │
│                                   │                                          │
│  ┌────────────────────────────────▼────────────────────────────────────┐    │
│  │                         API Endpoints (v1)                           │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │    │
│  │  │  /auth  │  │ /users  │  │/tenants │  │  /docs  │  │  /chat  │   │    │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │    │
│  └───────┼────────────┼───────────┼────────────┼────────────┼────────┘    │
│          │            │           │            │            │              │
│  ┌───────▼────────────▼───────────▼────────────▼────────────▼────────┐    │
│  │                         Service Layer                              │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │    │
│  │  │ AuthService │  │ DocService  │  │ RAGService  │                │    │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │    │
│  │         │                │                │                        │    │
│  │  ┌──────▼────────────────▼────────────────▼──────┐                │    │
│  │  │           Tenant-Scoped Operations            │                │    │
│  │  └───────────────────────┬───────────────────────┘                │    │
│  └──────────────────────────┼────────────────────────────────────────┘    │
│                             │                                              │
│  ┌──────────────────────────┼────────────────────────────────────────┐    │
│  │                  Repository Layer                                  │    │
│  │                          │                                         │    │
│  │    ┌─────────────────────┼─────────────────────┐                  │    │
│  │    │                     │                     │                  │    │
│  │    ▼                     ▼                     ▼                  │    │
│  │ ┌──────────┐      ┌──────────────┐      ┌───────────┐            │    │
│  │ │  SQLite  │      │ FAISS Index  │      │  OpenAI   │            │    │
│  │ │(Postgres)│      │ (Per-Tenant) │      │    API    │            │    │
│  │ └──────────┘      └──────────────┘      └───────────┘            │    │
│  └───────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
```

### Request Flow - RAG Chat

```
User Question
      │
      ▼
┌─────────────────┐
│  JWT Validation │ ──────► Extract tenant_id from token
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load/Cache FAISS│ ──────► Lazy load tenant-specific index
│     Index       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate Query  │ ──────► OpenAI text-embedding-3-small
│   Embedding     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FAISS Search   │ ──────► L2 distance, top-k retrieval
│   (Top-K=4)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fetch Chunk    │ ──────► Get full text from database
│    Metadata     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Build Context   │ ──────► Anti-hallucination prompt
│    Prompt       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM Call      │ ──────► GPT-4o-mini / GPT-4o
│  (OpenAI API)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Log & Return   │ ──────► Store chat history, return response
│    Response     │
└────────┴────────┘
```

### Multi-Tenancy Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TENANT ISOLATION                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Database Level:                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  All tables include tenant_id column                         │   │
│  │  Base repository auto-filters by tenant_id                   │   │
│  │  Foreign keys enforce referential integrity                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Vector Store Level:                                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  data/faiss_indexes/                                         │   │
│  │  ├── tenant_abc123/                                          │   │
│  │  │   ├── index.faiss                                         │   │
│  │  │   └── index.pkl (chunk ID mapping)                        │   │
│  │  ├── tenant_def456/                                          │   │
│  │  │   ├── index.faiss                                         │   │
│  │  │   └── index.pkl                                           │   │
│  │  └── tenant_ghi789/                                          │   │
│  │      ├── index.faiss                                         │   │
│  │      └── index.pkl                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Authentication Level:                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  JWT payload includes tenant_id                              │   │
│  │  Every request extracts and validates tenant context         │   │
│  │  Services receive tenant_id as mandatory parameter           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE SCHEMA                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│      tenants        │
├─────────────────────┤
│ id (PK, UUID)       │
│ name (VARCHAR 255)  │
│ slug (VARCHAR 100)  │──────────┐
│ is_active (BOOL)    │          │
│ max_documents (INT) │          │
│ max_storage_mb (INT)│          │
│ created_at (DATETIME│          │
│ updated_at (DATETIME│          │
└─────────────────────┘          │
         │                       │
         │ 1:N                   │
         ▼                       │
┌─────────────────────┐          │
│       users         │          │
├─────────────────────┤          │
│ id (PK, UUID)       │          │
│ tenant_id (FK)      │◄─────────┤
│ email (VARCHAR 255) │          │
│ hashed_password     │          │
│ full_name (VARCHAR) │          │
│ role (ENUM)         │          │
│ is_active (BOOL)    │          │
│ created_at          │          │
│ updated_at          │          │
│ last_login          │          │
└─────────────────────┘          │
         │                       │
         │ 1:N                   │
         ▼                       │
┌─────────────────────┐          │
│     documents       │          │
├─────────────────────┤          │
│ id (PK, UUID)       │          │
│ tenant_id (FK)      │◄─────────┤
│ uploaded_by (FK)    │          │
│ filename (VARCHAR)  │          │
│ original_name       │          │
│ file_size (INT)     │          │
│ file_hash (VARCHAR) │          │
│ mime_type (VARCHAR) │          │
│ status (ENUM)       │          │
│ page_count (INT)    │          │
│ chunk_count (INT)   │          │
│ created_at          │          │
│ updated_at          │          │
└─────────────────────┘          │
         │                       │
         │ 1:N                   │
         ▼                       │
┌─────────────────────┐          │
│   document_chunks   │          │
├─────────────────────┤          │
│ id (PK, UUID)       │          │
│ document_id (FK)    │          │
│ tenant_id (FK)      │◄─────────┤
│ chunk_index (INT)   │          │
│ content (TEXT)      │          │
│ token_count (INT)   │          │
│ page_number (INT)   │          │
│ embedding_id (INT)  │ ──► FAISS index position
│ created_at          │          │
└─────────────────────┘          │
                                 │
┌─────────────────────┐          │
│     chat_logs       │          │
├─────────────────────┤          │
│ id (PK, UUID)       │          │
│ tenant_id (FK)      │◄─────────┘
│ user_id (FK)        │
│ session_id (UUID)   │
│ question (TEXT)     │
│ answer (TEXT)       │
│ context_chunks (JSON│ ──► Retrieved chunk IDs
│ model_used (VARCHAR)│
│ tokens_used (INT)   │
│ latency_ms (INT)    │
│ created_at          │
└─────────────────────┘

┌─────────────────────┐
│    rate_limits      │
├─────────────────────┤
│ id (PK, UUID)       │
│ tenant_id (FK)      │
│ endpoint (VARCHAR)  │
│ requests_count (INT)│
│ window_start        │
│ created_at          │
└─────────────────────┘
```

### SQL Schema Definition

```sql
-- Tenants Table
CREATE TABLE tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    max_documents INTEGER DEFAULT 100,
    max_storage_mb INTEGER DEFAULT 500,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users Table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(20) DEFAULT 'USER',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE(tenant_id, email)
);

-- Documents Table
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    uploaded_by VARCHAR(36) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    mime_type VARCHAR(100) DEFAULT 'application/pdf',
    status VARCHAR(20) DEFAULT 'PENDING',
    page_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Document Chunks Table
CREATE TABLE document_chunks (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    page_number INTEGER,
    embedding_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Chat Logs Table
CREATE TABLE chat_logs (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    context_chunks JSON,
    model_used VARCHAR(50),
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Rate Limits Table
CREATE TABLE rate_limits (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36),
    ip_address VARCHAR(45),
    endpoint VARCHAR(100) NOT NULL,
    requests_count INTEGER DEFAULT 0,
    window_start TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Indexes for Performance
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(tenant_id, email);
CREATE INDEX idx_documents_tenant ON documents(tenant_id);
CREATE INDEX idx_documents_status ON documents(tenant_id, status);
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_tenant ON document_chunks(tenant_id);
CREATE INDEX idx_chat_logs_tenant ON chat_logs(tenant_id);
CREATE INDEX idx_chat_logs_user ON chat_logs(user_id);
CREATE INDEX idx_chat_logs_session ON chat_logs(session_id);
CREATE INDEX idx_rate_limits_lookup ON rate_limits(tenant_id, endpoint, window_start);
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SECURITY LAYERS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 1: Network Security                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • HTTPS only (TLS 1.3)                                              │   │
│  │  • CORS whitelist configured                                         │   │
│  │  • Rate limiting per IP and tenant                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Layer 2: Authentication                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • JWT with RS256 / HS256 signing                                    │   │
│  │  • Access token: 15 minutes expiry                                   │   │
│  │  • Refresh token: 7 days expiry                                      │   │
│  │  • Token stored in httpOnly cookies (preferred) or memory            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Layer 3: Authorization                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Role-Based Access Control (RBAC)                                  │   │
│  │  • Roles: SUPER_ADMIN, ADMIN, USER                                   │   │
│  │  • Tenant-scoped permissions                                         │   │
│  │  • Resource-level access checks                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Layer 4: Data Security                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Passwords: bcrypt with cost factor 12                             │   │
│  │  • All queries tenant-scoped                                         │   │
│  │  • File uploads validated and sandboxed                              │   │
│  │  • SQL injection prevention via ORM                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Layer 5: Input Validation                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Pydantic schema validation                                        │   │
│  │  • File type verification (magic bytes)                              │   │
│  │  • Size limits enforced                                              │   │
│  │  • Sanitized filenames                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## RAG Pipeline Details

### Document Processing Flow

```
PDF Upload
    │
    ▼
┌─────────────────────┐
│ Validate File       │
│ • Check MIME type   │
│ • Verify magic bytes│
│ • Check size limit  │
│ • Compute hash      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Extract Text        │
│ • PyMuPDF (fitz)    │
│ • Page-by-page      │
│ • Preserve structure│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Chunk Text          │
│ • 400-500 tokens    │
│ • 80 token overlap  │
│ • Sentence boundary │
│ • Page tracking     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Generate Embeddings │
│ • text-embedding-   │
│   3-small (1536 dim)│
│ • Batch processing  │
│ • L2 normalize      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Store in FAISS      │
│ • IndexFlatIP       │
│ • Per-tenant index  │
│ • ID mapping stored │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Update Database     │
│ • Store chunks      │
│ • Update doc status │
│ • Link embedding IDs│
└─────────────────────┘
```

### Chunking Strategy

```
Document Text
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DETERMINISTIC CHUNKING                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Parameters:                                                    │
│  • chunk_size: 450 tokens (target)                              │
│  • chunk_overlap: 80 tokens                                     │
│  • min_chunk_size: 100 tokens                                   │
│                                                                 │
│  Algorithm:                                                     │
│  1. Tokenize using tiktoken (cl100k_base)                       │
│  2. Find sentence boundaries                                    │
│  3. Build chunks respecting boundaries                          │
│  4. Apply overlap from previous chunk                           │
│  5. Track page numbers per chunk                                │
│                                                                 │
│  Example:                                                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Chunk 1 ─────────────────────────────────────────────► │    │
│  │                                    ◄── 80 overlap ──►  │    │
│  │                                    Chunk 2 ──────────► │    │
│  │                                                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Anti-Hallucination Prompt Template

```
┌─────────────────────────────────────────────────────────────────┐
│                 SYSTEM PROMPT TEMPLATE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  You are a helpful assistant that answers questions based       │
│  STRICTLY on the provided context.                              │
│                                                                 │
│  RULES:                                                         │
│  1. Only use information from the CONTEXT section below         │
│  2. If the context doesn't contain the answer, say:             │
│     "I don't have enough information to answer this question"   │
│  3. Do not make up information or use external knowledge        │
│  4. Quote relevant parts of the context when helpful            │
│  5. Be concise but complete                                     │
│                                                                 │
│  CONTEXT:                                                       │
│  ---                                                            │
│  {retrieved_chunks}                                             │
│  ---                                                            │
│                                                                 │
│  USER QUESTION: {question}                                      │
│                                                                 │
│  Provide a helpful answer based ONLY on the context above:      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Optimization

```
┌─────────────────────────────────────────────────────────────────┐
│                  PERFORMANCE STRATEGIES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. FAISS Index Caching                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • LRU cache for loaded indexes                          │   │
│  │  • Max 10 indexes in memory (configurable)               │   │
│  │  • Lazy loading on first query                           │   │
│  │  • Auto-eviction based on last access                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  2. Async Operations                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • All endpoints async/await                             │   │
│  │  • Database operations via asyncio                       │   │
│  │  • Concurrent embedding generation                       │   │
│  │  • Background task for document processing               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  3. Connection Pooling                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • SQLAlchemy async session pool                         │   │
│  │  • Pool size: 5 (configurable)                           │   │
│  │  • Max overflow: 10                                      │   │
│  │  • Connection recycling: 3600s                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  4. Batch Processing                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Batch embed chunks (max 100 per API call)             │   │
│  │  • Bulk database inserts                                 │   │
│  │  • Streaming responses for chat                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

PHASE 1 COMPLETE: Architecture documented.
