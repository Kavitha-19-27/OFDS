# RAG SaaS Application - Project Report

**Project Name:** RAG-based SaaS Document Intelligence Platform  
**Version:** 1.0.0  
**Report Date:** February 17, 2026  
**Development Status:** Production Ready (MVP)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Technology Stack](#2-technology-stack)
3. [Architecture Overview](#3-architecture-overview)
4. [Features & Functionality](#4-features--functionality)
5. [API Endpoints](#5-api-endpoints)
6. [Database Schema](#6-database-schema)
7. [Security Implementation](#7-security-implementation)
8. [RAG Pipeline Details](#8-rag-pipeline-details)
9. [Frontend Application](#9-frontend-application)
10. [Configuration & Environment](#10-configuration--environment)
11. [Performance Optimizations](#11-performance-optimizations)
12. [Scalability Roadmap](#12-scalability-roadmap)
13. [File Structure](#13-file-structure)
14. [Deployment](#14-deployment)
15. [Current Status & Metrics](#15-current-status--metrics)

---

## 1. Executive Summary

### What is RAG SaaS?

RAG SaaS is a **multi-tenant Retrieval-Augmented Generation (RAG) platform** that enables organizations to upload PDF documents, extract knowledge from them, and chat with an AI assistant that answers questions based **exclusively** on the uploaded documents.

### Key Value Proposition

- **Document Intelligence:** Transform static PDFs into queryable knowledge bases
- **Anti-Hallucination:** AI responses are grounded strictly in provided documents
- **Multi-Tenant Isolation:** Complete data separation between organizations
- **Cost-Effective:** Uses local embeddings (free) + Groq LLM (fast & affordable)

### Use Cases

| Use Case | Description |
|----------|-------------|
| **HR Policies** | Employees query company handbooks and policies |
| **Legal Review** | Search through contracts and legal documents |
| **Technical Docs** | Query product manuals and specifications |
| **Research** | Extract insights from academic papers |
| **Customer Support** | Agents query knowledge base for answers |

---

## 2. Technology Stack

### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | FastAPI | 0.109.2 | High-performance async REST API |
| **Runtime** | Python | 3.11 | Core language |
| **Server** | Uvicorn | 0.27.1 | ASGI server |
| **Database** | SQLite (aiosqlite) | 0.19.0 | Async database operations |
| **ORM** | SQLAlchemy | 2.0.25 | Async ORM with type hints |
| **Migrations** | Alembic | 1.13.1 | Database schema migrations |
| **Validation** | Pydantic | 2.6.1 | Data validation & serialization |

### AI/ML Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **LLM Provider** | Groq | SDK | Fast inference (llama-3.3-70b-versatile) |
| **Embeddings** | Sentence-Transformers | Local | all-MiniLM-L6-v2 (384 dimensions) |
| **Vector Store** | FAISS-CPU | 1.7.4 | Similarity search |
| **Tokenizer** | Tiktoken | 0.6.0 | Token counting |
| **PDF Processing** | PyMuPDF | 1.23.22 | PDF text extraction |

### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | React | 18.2.0 | UI library |
| **Build Tool** | Vite | 5.0.8 | Development & bundling |
| **Language** | TypeScript | 5.3.3 | Type safety |
| **Styling** | Tailwind CSS | 3.3.6 | Utility-first CSS |
| **State** | Zustand | 4.4.7 | State management |
| **HTTP Client** | Axios | 1.6.2 | API communication |
| **Routing** | React Router | 6.21.0 | Client-side routing |
| **UI Components** | Headless UI | 1.7.17 | Accessible components |
| **Icons** | Heroicons | 2.1.1 | Icon library |
| **Notifications** | React Hot Toast | 2.4.1 | Toast notifications |
| **File Upload** | React Dropzone | 14.2.3 | Drag-and-drop uploads |
| **Markdown** | React Markdown | 9.0.1 | Render markdown responses |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Containerization** | Docker | Container deployment |
| **Orchestration** | Docker Compose | Multi-service management |
| **Web Server** | Nginx | Reverse proxy, static serving |

---

## 3. Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite + TypeScript)             │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Auth UI │  │  Documents   │  │   Chat UI    │  │  Settings    │    │
│  └────┬─────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│       └───────────────┴─────────────────┴─────────────────┘             │
│                               │                                          │
│                    ┌──────────▼──────────┐                              │
│                    │   Axios API Client  │                              │
│                    │    (JWT Auth)       │                              │
│                    └──────────┬──────────┘                              │
└───────────────────────────────┼─────────────────────────────────────────┘
                                │ HTTP/HTTPS (Port 3000 → 8001)
                                │
┌───────────────────────────────┼─────────────────────────────────────────┐
│                        BACKEND (FastAPI)                                 │
│                                │                                         │
│  ┌─────────────────────────────▼───────────────────────────────────┐    │
│  │                    MIDDLEWARE LAYER                              │    │
│  │  ┌────────────┐  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │    CORS    │  │ Rate Limiter │  │  JWT Auth    │             │    │
│  │  └────────────┘  └──────────────┘  └──────────────┘             │    │
│  └─────────────────────────────┬───────────────────────────────────┘    │
│                                │                                         │
│  ┌─────────────────────────────▼───────────────────────────────────┐    │
│  │                    API ENDPOINTS (v1)                            │    │
│  │  /auth  │  /users  │  /tenants  │  /documents  │  /chat         │    │
│  └─────────────────────────────┬───────────────────────────────────┘    │
│                                │                                         │
│  ┌─────────────────────────────▼───────────────────────────────────┐    │
│  │                    SERVICE LAYER                                 │    │
│  │  AuthService │ DocumentService │ RAGService │ VectorService      │    │
│  └─────────────────────────────┬───────────────────────────────────┘    │
│                                │                                         │
│  ┌─────────────────────────────▼───────────────────────────────────┐    │
│  │                    DATA LAYER                                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐      │    │
│  │  │   SQLite     │  │ FAISS Index  │  │  Groq LLM API     │      │    │
│  │  │  (Database)  │  │ (Per-Tenant) │  │  (Chat Response)  │      │    │
│  │  └──────────────┘  └──────────────┘  └───────────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Multi-Tenant Data Isolation

```
┌─────────────────────────────────────────────────────────┐
│                 TENANT ISOLATION                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  DATABASE LEVEL:                                         │
│  • All tables include tenant_id column                   │
│  • Repository layer auto-filters by tenant_id            │
│  • Foreign keys enforce referential integrity            │
│                                                          │
│  VECTOR STORE LEVEL:                                     │
│  data/faiss_indexes/                                     │
│  ├── tenant_abc123/                                      │
│  │   ├── index.faiss                                     │
│  │   └── index.pkl (chunk ID mapping)                    │
│  ├── tenant_def456/                                      │
│  │   ├── index.faiss                                     │
│  │   └── index.pkl                                       │
│  └── tenant_ghi789/                                      │
│      ├── index.faiss                                     │
│      └── index.pkl                                       │
│                                                          │
│  FILE STORAGE LEVEL:                                     │
│  data/uploads/                                           │
│  ├── tenant_abc123/                                      │
│  ├── tenant_def456/                                      │
│  └── tenant_ghi789/                                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Features & Functionality

### Core Features

#### 4.1 Authentication & Authorization

| Feature | Description |
|---------|-------------|
| **JWT Authentication** | Secure token-based auth with access/refresh tokens |
| **User Registration** | Self-registration with email validation |
| **Login/Logout** | Secure authentication flow |
| **Role-Based Access** | Three roles: Admin, Tenant Admin, User |
| **Password Security** | Bcrypt hashing with cost factor 12 |
| **Token Refresh** | Automatic token refresh mechanism |

#### 4.2 Document Management

| Feature | Description |
|---------|-------------|
| **PDF Upload** | Drag-and-drop or click-to-upload interface |
| **File Validation** | MIME type, magic bytes, and size validation |
| **Document List** | View all uploaded documents with status |
| **Document Status** | PENDING → PROCESSING → COMPLETED/FAILED |
| **Reprocessing** | Retry failed document processing |
| **Document Deletion** | Remove documents and associated vectors |
| **Storage Quota** | Per-tenant storage limits |

#### 4.3 RAG Chat System

| Feature | Description |
|---------|-------------|
| **Document Q&A** | Ask questions about uploaded documents |
| **Source Citations** | See which documents were used for answers |
| **Multi-Session** | Multiple chat sessions per user |
| **Chat History** | Persistent conversation history |
| **Greeting Detection** | Smart handling of casual greetings |
| **Anti-Hallucination** | Strict grounding in document content |
| **Markdown Responses** | Rich formatted AI responses |

#### 4.4 Multi-Tenancy

| Feature | Description |
|---------|-------------|
| **Tenant Isolation** | Complete data separation |
| **Per-Tenant Indexes** | Separate vector stores |
| **Resource Quotas** | Document and storage limits |
| **Tenant Management** | Create and manage tenants |

### Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| **Login** | `/auth/login` | User authentication |
| **Register** | `/auth/register` | New user registration |
| **Dashboard** | `/dashboard` | Overview and quick actions |
| **Documents** | `/documents` | Upload and manage PDFs |
| **Chat** | `/chat` | AI-powered document Q&A |
| **Settings** | `/settings` | User preferences |

---

## 5. API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Authenticate user | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | Yes |
| POST | `/api/v1/auth/logout` | Invalidate tokens | Yes |
| GET | `/api/v1/auth/me` | Get current user | Yes |

### User Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/users` | List all users (admin) | Yes |
| GET | `/api/v1/users/{id}` | Get user details | Yes |
| PUT | `/api/v1/users/{id}` | Update user | Yes |
| DELETE | `/api/v1/users/{id}` | Delete user (admin) | Yes |

### Document Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/documents` | Upload PDF document | Yes |
| GET | `/api/v1/documents` | List user's documents | Yes |
| GET | `/api/v1/documents/{id}` | Get document details | Yes |
| DELETE | `/api/v1/documents/{id}` | Delete document | Yes |
| POST | `/api/v1/documents/{id}/reprocess` | Reprocess failed doc | Yes |

### Chat Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/chat` | Send question, get answer | Yes |
| GET | `/api/v1/chat/sessions` | List chat sessions | Yes |
| GET | `/api/v1/chat/sessions/{id}` | Get session history | Yes |
| DELETE | `/api/v1/chat/sessions/{id}` | Delete chat session | Yes |

### Tenant Endpoints (Admin)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/tenants` | Create tenant | Admin |
| GET | `/api/v1/tenants` | List all tenants | Admin |
| GET | `/api/v1/tenants/{id}` | Get tenant details | Admin |
| PUT | `/api/v1/tenants/{id}` | Update tenant | Admin |
| DELETE | `/api/v1/tenants/{id}` | Delete tenant | Admin |

### Health Endpoint

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | No |

---

## 6. Database Schema

### Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────┐
│     TENANTS      │       │      USERS       │
├──────────────────┤       ├──────────────────┤
│ id (PK, UUID)    │───┐   │ id (PK, UUID)    │
│ name             │   │   │ tenant_id (FK)   │◄──┐
│ slug             │   │   │ email            │   │
│ is_active        │   │   │ hashed_password  │   │
│ max_documents    │   │   │ full_name        │   │
│ max_storage_mb   │   │   │ role (ENUM)      │   │
│ created_at       │   │   │ is_active        │   │
│ updated_at       │   │   │ created_at       │   │
└──────────────────┘   │   │ last_login       │   │
                       │   └──────────────────┘   │
                       │           │              │
                       │           ▼ 1:N          │
                       │   ┌──────────────────┐   │
                       │   │    DOCUMENTS     │   │
                       │   ├──────────────────┤   │
                       ├──►│ id (PK, UUID)    │   │
                       │   │ tenant_id (FK)   │◄──┤
                       │   │ uploaded_by (FK) │   │
                       │   │ filename         │   │
                       │   │ original_name    │   │
                       │   │ file_size        │   │
                       │   │ file_hash        │   │
                       │   │ status (ENUM)    │   │
                       │   │ page_count       │   │
                       │   │ chunk_count      │   │
                       │   │ error_message    │   │
                       │   │ created_at       │   │
                       │   └──────────────────┘   │
                       │           │              │
                       │           ▼ 1:N          │
                       │   ┌──────────────────┐   │
                       │   │ DOCUMENT_CHUNKS  │   │
                       │   ├──────────────────┤   │
                       ├──►│ id (PK, UUID)    │   │
                       │   │ document_id (FK) │   │
                       │   │ tenant_id (FK)   │◄──┤
                       │   │ chunk_index      │   │
                       │   │ content (TEXT)   │   │
                       │   │ token_count      │   │
                       │   │ page_number      │   │
                       │   │ embedding_id     │──►│ FAISS Index
                       │   │ created_at       │   │
                       │   └──────────────────┘   │
                       │                          │
                       │   ┌──────────────────┐   │
                       │   │    CHAT_LOGS     │   │
                       │   ├──────────────────┤   │
                       └──►│ id (PK, UUID)    │   │
                           │ tenant_id (FK)   │◄──┘
                           │ user_id (FK)     │
                           │ session_id       │
                           │ question (TEXT)  │
                           │ answer (TEXT)    │
                           │ context_chunks   │
                           │ model_used       │
                           │ tokens_used      │
                           │ latency_ms       │
                           │ created_at       │
                           └──────────────────┘
```

### Document Status Enum

| Status | Description |
|--------|-------------|
| `PENDING` | Document uploaded, awaiting processing |
| `PROCESSING` | Currently extracting text and embeddings |
| `COMPLETED` | Successfully processed and indexed |
| `FAILED` | Processing failed (see error_message) |

### User Roles Enum

| Role | Permissions |
|------|-------------|
| `ADMIN` | Full system access |
| `TENANT_ADMIN` | Manage tenant users and settings |
| `USER` | Upload documents, chat, view own data |

---

## 7. Security Implementation

### Implemented Security Measures

#### Authentication & Authorization

| Measure | Implementation |
|---------|----------------|
| **JWT Tokens** | HS256 signing, 15-min access / 7-day refresh |
| **Password Hashing** | Bcrypt with cost factor 12 |
| **RBAC** | Role-based access control (Admin/TenantAdmin/User) |
| **Token Storage** | localStorage (consider HttpOnly cookies) |

#### API Security

| Measure | Implementation |
|---------|----------------|
| **Rate Limiting** | 60 requests/minute per IP (configurable) |
| **CORS** | Explicit origin allowlist |
| **Input Validation** | Pydantic schemas for all requests |
| **File Validation** | MIME type, magic bytes, size limits |

#### Data Security

| Measure | Implementation |
|---------|----------------|
| **SQL Injection** | Prevented via SQLAlchemy ORM |
| **XSS Prevention** | React's default escaping |
| **Tenant Isolation** | All queries scoped by tenant_id |
| **File Segregation** | Per-tenant upload directories |

#### Infrastructure Security

| Measure | Implementation |
|---------|----------------|
| **Docker** | Non-root user, multi-stage builds |
| **Secrets** | Environment variables, not hardcoded |
| **Error Handling** | No stack traces in production |

### Security Headers

```nginx
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

---

## 8. RAG Pipeline Details

### Document Processing Flow

```
PDF Upload
     │
     ▼
┌────────────────────┐
│  1. VALIDATE FILE  │
│  • MIME type check │
│  • Size limit (10MB)│
│  • Compute file hash │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  2. EXTRACT TEXT   │
│  • PyMuPDF parser  │
│  • Page-by-page    │
│  • Preserve layout │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  3. CHUNK TEXT     │
│  • 450 tokens/chunk│
│  • 80 token overlap│
│  • Sentence bounds │
│  • Page tracking   │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  4. EMBED CHUNKS   │
│  • all-MiniLM-L6-v2│
│  • 384 dimensions  │
│  • Batch process   │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  5. STORE VECTORS  │
│  • FAISS IndexFlatIP│
│  • Per-tenant index│
│  • Save to disk    │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  6. UPDATE DB      │
│  • Store chunks    │
│  • Link embeddings │
│  • Set status=DONE │
└────────────────────┘
```

### Chat Request Flow

```
User Question: "What is the dress code?"
           │
           ▼
┌──────────────────────────┐
│  1. GREETING DETECTION   │
│  • Is it casual greeting?│
│  • If yes → friendly msg │
│  • If no → continue RAG  │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│  2. GENERATE EMBEDDING   │
│  • Embed the question    │
│  • Same model as docs    │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│  3. FAISS SIMILARITY     │
│  • Search tenant's index │
│  • Retrieve top-4 chunks │
│  • Get chunk IDs         │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│  4. FETCH CHUNK CONTENT  │
│  • Load from database    │
│  • Include metadata      │
│  • Build context         │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│  5. CONSTRUCT PROMPT     │
│  • Anti-hallucination    │
│  • Include context       │
│  • Add user question     │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│  6. LLM INFERENCE        │
│  • Groq API call         │
│  • llama-3.3-70b-versatile│
│  • Grounded response     │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│  7. LOG & RETURN         │
│  • Store chat history    │
│  • Return with sources   │
└──────────────────────────┘
```

### Anti-Hallucination Prompt

```
You are a helpful assistant that answers questions based 
STRICTLY on the provided context.

RULES:
1. Only use information from the CONTEXT section below
2. If the context doesn't contain the answer, say:
   "I don't have enough information to answer this question"
3. Do not make up information or use external knowledge
4. Quote relevant parts of the context when helpful
5. Be concise but complete

CONTEXT:
---
{retrieved_chunks}
---

USER QUESTION: {question}

Provide a helpful answer based ONLY on the context above:
```

### Chunking Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `chunk_size` | 450 tokens | Target chunk size |
| `chunk_overlap` | 80 tokens | Overlap between chunks |
| `min_chunk_size` | 100 tokens | Minimum chunk size |
| `tokenizer` | cl100k_base | Tiktoken encoder |

### Embedding Configuration

| Parameter | Value |
|-----------|-------|
| **Model** | all-MiniLM-L6-v2 (sentence-transformers) |
| **Dimensions** | 384 |
| **Location** | Local (no API calls) |
| **Index Type** | FAISS IndexFlatIP |
| **Retrieval Count** | Top-4 similar chunks |

### LLM Configuration

| Parameter | Value |
|-----------|-------|
| **Provider** | Groq |
| **Model** | llama-3.3-70b-versatile |
| **Context Window** | 128K tokens |
| **Response Speed** | ~500 tokens/second |

---

## 9. Frontend Application

### Component Architecture

```
src/
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── ProtectedRoute.tsx
│   │
│   ├── chat/
│   │   ├── ChatInput.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── ChatMessages.tsx
│   │   ├── ChatSidebar.tsx
│   │   └── index.ts
│   │
│   ├── documents/
│   │   ├── DocumentCard.tsx
│   │   ├── DocumentList.tsx
│   │   ├── DocumentUpload.tsx
│   │   └── index.ts
│   │
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   └── index.ts
│   │
│   └── common/
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Modal.tsx
│       ├── Spinner.tsx
│       └── Toast.tsx
│
├── pages/
│   ├── auth/
│   │   ├── LoginPage.tsx
│   │   └── RegisterPage.tsx
│   ├── ChatPage.tsx
│   ├── DashboardPage.tsx
│   ├── DocumentsPage.tsx
│   └── SettingsPage.tsx
│
├── stores/
│   ├── authStore.ts
│   ├── chatStore.ts
│   └── documentStore.ts
│
├── api/
│   ├── client.ts (Axios instance)
│   ├── auth.ts
│   ├── chat.ts
│   └── documents.ts
│
└── App.tsx

```

### State Management (Zustand)

| Store | Purpose |
|-------|---------|
| `authStore` | User authentication state, tokens, user info |
| `chatStore` | Chat messages, sessions, loading state |
| `documentStore` | Document list, upload progress, status |

### UI Features

| Feature | Library |
|---------|---------|
| **Styling** | Tailwind CSS utility classes |
| **Icons** | Heroicons React components |
| **Toasts** | React Hot Toast notifications |
| **Modals** | Headless UI Dialog |
| **Dropdowns** | Headless UI Menu |
| **File Upload** | React Dropzone |
| **Markdown** | React Markdown renderer |

---

## 10. Configuration & Environment

### Backend Environment Variables

```env
# Application
APP_NAME=RAG-SaaS
APP_ENV=development
DEBUG=false
API_V1_PREFIX=/api/v1

# Server
HOST=0.0.0.0
PORT=8001

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/app.db

# JWT Security
JWT_SECRET_KEY=your-32-char-minimum-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
GROQ_CHAT_MODEL=llama-3.3-70b-versatile

# Embeddings (Local)
USE_LOCAL_EMBEDDINGS=true
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2
LOCAL_EMBEDDING_DIMENSIONS=384

# FAISS Vector Store
FAISS_INDEX_PATH=./data/faiss_indexes
FAISS_CACHE_SIZE=10

# Chunking
CHUNK_SIZE=450
CHUNK_OVERLAP=80
TOP_K_RETRIEVAL=4

# File Upload
MAX_FILE_SIZE_MB=10
UPLOAD_PATH=./data/uploads
ALLOWED_EXTENSIONS=.pdf

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_ALLOW_CREDENTIALS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### API Keys Configuration (Current Setup)

> **⚠️ IMPORTANT:** The following are the actual API keys configured in this deployment. Keep these secure and rotate them before production use.

#### Active API Keys

| Service | Key | Status |
|---------|-----|--------|
| **Groq LLM** | `gsk_your_groq_api_key_here` | ⚙️ Set in Render |
| **OpenAI** | Not configured | ⚪ Optional |
| **Local Embeddings** | No API key required | ✅ Active |

#### Groq API Details

| Property | Value |
|----------|-------|
| **Provider** | [Groq Cloud](https://console.groq.com/) |
| **API Key** | Set via `GROQ_API_KEY` environment variable |
| **Model** | `llama-3.3-70b-versatile` |
| **Context Window** | 128K tokens |
| **Rate Limits** | Varies by plan (free tier: 30 RPM, 6000 tokens/minute) |
| **Pricing** | Free tier available |

#### JWT Secret Key

| Property | Value |
|----------|-------|
| **Secret** | `dev-secret-key-change-this-in-production-min-32-characters` |
| **Algorithm** | HS256 |
| **Access Token Expiry** | 15 minutes |
| **Refresh Token Expiry** | 7 days |

#### How to Get API Keys

**Groq API Key:**
1. Go to [console.groq.com](https://console.groq.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Add to `.env` file as `GROQ_API_KEY=your-key`

**OpenAI API Key (Optional):**
1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new secret key
5. Add to `.env` file as `OPENAI_API_KEY=your-key`
6. Set `LLM_PROVIDER=openai` to use OpenAI instead of Groq

### Frontend Environment Variables

```env
VITE_API_URL=http://localhost:8001/api/v1
```

---

## 11. Performance Optimizations

### Current Optimizations

| Optimization | Description |
|--------------|-------------|
| **Async Everything** | All DB and API operations are async/await |
| **FAISS LRU Cache** | Keep top 10 tenant indexes in memory |
| **Lazy Loading** | Load FAISS index only on first query |
| **Connection Pooling** | SQLAlchemy async session pool |
| **Batch Embeddings** | Process chunks in batches |
| **Background Tasks** | Document processing runs async |

### Performance Metrics

| Metric | Target |
|--------|--------|
| **API Response** | < 200ms (excluding LLM) |
| **Document Upload** | < 5s for 10-page PDF |
| **Embedding Generation** | ~100ms per chunk |
| **FAISS Search** | < 10ms for 10K vectors |
| **LLM Response** | 1-3 seconds |

---

## 12. Scalability Roadmap

### Current Capacity (MVP)

- **Users:** ~100 concurrent
- **Documents:** ~1,000 total
- **Concurrent Requests:** ~10
- **Cost:** Minimal (local embeddings + Groq free tier)

### Phase 1: Basic Production (10-100 Tenants)

- Migrate SQLite → PostgreSQL
- Add Redis for caching and rate limiting
- **Capacity:** 500 users, 10K documents, 50 concurrent

### Phase 2: Multi-Instance (100-500 Tenants)

- Multiple backend instances
- Load balancer (Nginx/Traefik)
- Centralized vector store
- **Capacity:** 2,000 users, 50K documents, 200 concurrent

### Phase 3: Enterprise Scale (500+ Tenants)

- Kubernetes deployment
- Managed vector database (Pinecone/Weaviate)
- Distributed caching
- Read replicas
- **Capacity:** 10,000+ users, unlimited documents

---

## 13. File Structure

```
rag-saas/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   ├── router.py
│   │   │   ├── tenants.py
│   │   │   └── users.py
│   │   │
│   │   ├── core/
│   │   │   ├── exceptions.py
│   │   │   ├── middleware.py
│   │   │   └── security.py
│   │   │
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   ├── chat_log.py
│   │   │   ├── document.py
│   │   │   ├── tenant.py
│   │   │   └── user.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── base.py
│   │   │   ├── chat_repository.py
│   │   │   ├── document_repository.py
│   │   │   ├── tenant_repository.py
│   │   │   └── user_repository.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── document.py
│   │   │   ├── tenant.py
│   │   │   └── user.py
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── document_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── tenant_service.py
│   │   │   ├── user_service.py
│   │   │   └── vector_service.py
│   │   │
│   │   ├── utils/
│   │   │   ├── logger.py
│   │   │   ├── pdf_processor.py
│   │   │   ├── text_chunker.py
│   │   │   └── validators.py
│   │   │
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── data/
│   │   ├── faiss_indexes/
│   │   └── uploads/
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── stores/
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── ARCHITECTURE.md
├── SECURITY_CHECKLIST.md
├── SCALABILITY_ROADMAP.md
└── .env.example
```

---

## 14. Deployment

### Development Setup

```bash
# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Docker Deployment

```bash
# Build and run all services
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| **frontend** | 3000 | React app via Nginx |
| **backend** | 8001 | FastAPI application |

---

## 15. Current Status & Metrics

### Operational Status

| Component | Status | Details |
|-----------|--------|---------|
| **Backend API** | ✅ Running | Port 8001, healthy |
| **Frontend** | ✅ Running | Port 3000 |
| **Database** | ✅ Connected | SQLite with async support |
| **FAISS** | ✅ Operational | Per-tenant indexes |
| **LLM (Groq)** | ✅ Connected | llama-3.3-70b-versatile |
| **Embeddings** | ✅ Local | all-MiniLM-L6-v2 (384 dim) |

### Document Processing Stats

| Metric | Value |
|--------|-------|
| **Total Documents** | 2 |
| **Processed Chunks** | 5 |
| **Status** | All COMPLETED |

### Sample Documents

| Document | Status | Chunks |
|----------|--------|--------|
| Govind SSA.pdf | COMPLETED | 4 |
| Discipline Rules and Regulations AY 2025-26 | COMPLETED | 1 |

### Registered User Accounts

| Email | Role | Tenant | Notes |
|-------|------|--------|-------|
| `Kama@gmail.com` | User | Default | Primary test user, owns uploaded documents |
| `testapi@example.com` | User | Default | Created for API testing |

### Tenant Information

| Tenant ID | Name | Status |
|-----------|------|--------|
| `66b063c2-ac68-4bb7-8da6-3e23b2263990` | Default Tenant | Active |

### Recent Fixes Applied

1. ✅ Fixed embedding dimension mismatch (1536 → 384)
2. ✅ Added document reprocessing capability
3. ✅ Implemented greeting detection in chat
4. ✅ Fixed ChatResponse schema validation
5. ✅ Cleared and rebuilt FAISS indexes

---

## Appendix A: API Response Examples

### Chat Response

```json
{
  "answer": "The dress code is as follows:\n\nFor Boys:\n- Full formal pants and collared formal shirts\n- Formal shoes with long socks\n- Clean-shaven appearance\n\nFor Girls:\n- Formal attire such as normal Chudithar...",
  "sources": [
    {
      "document_id": "856e5f4f-0438-4c1b-a900-2e593dd3aa97",
      "document_name": "Discipline Rules and Regulations.pdf",
      "chunk_index": 0,
      "page_number": 1,
      "relevance_score": 0.89
    }
  ],
  "question": "What is the dress code?",
  "model_used": "llama-3.3-70b-versatile"
}
```

### Document Upload Response

```json
{
  "id": "856e5f4f-0438-4c1b-a900-2e593dd3aa97",
  "filename": "document.pdf",
  "original_name": "Discipline Rules and Regulations.pdf",
  "file_size": 125000,
  "status": "PROCESSING",
  "created_at": "2026-02-17T10:30:00Z"
}
```

---

## Appendix B: Key Dependencies

### Backend (Python)

```
fastapi==0.109.2
uvicorn[standard]==0.27.1
sqlalchemy[asyncio]==2.0.25
aiosqlite==0.19.0
pydantic==2.6.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
faiss-cpu==1.7.4
pymupdf==1.23.22
tiktoken==0.6.0
sentence-transformers (local embeddings)
groq (LLM provider)
```

### Frontend (Node.js)

```
react@18.2.0
react-router-dom@6.21.0
axios@1.6.2
zustand@4.4.7
tailwindcss@3.3.6
typescript@5.3.3
vite@5.0.8
```

---

**End of Report**

*Generated: February 17, 2026*
