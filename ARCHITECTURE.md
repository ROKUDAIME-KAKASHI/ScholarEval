# Architecture Overview 🏗️

## System Design

```
┌─────────────────────────────────────────────────────────┐
│                   Client (Browser)                       │
│              HTML/CSS/JavaScript UI                      │
└────────────────────────┬────────────────────────────────┘
                         │
                    HTTP/JSON
                         │
┌────────────────────────▼────────────────────────────────┐
│                    FastAPI Server                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │  HTTP Endpoints                                 │    │
│  │  • GET  /              (HTML UI)                │    │
│  │  • GET  /health        (Status check)           │    │
│  │  • POST /upload        (PDF upload)             │    │
│  │  • POST /evaluate      (Answer evaluation)      │    │
│  │  • GET  /status        (System status)          │    │
│  └─────────────────────────────────────────────────┘    │
│                         │                                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Business Logic Layer                           │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │ PDF Manager (backend/core/pdf_manager)   │   │    │
│  │  │ • Extract text from PDF (PyMuPDF)        │   │    │
│  │  │ • Handle file validation                 │   │    │
│  │  │ • Error handling                         │   │    │
│  │  └──────────────────────────────────────────┘   │    │
│  │                    │                              │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │ Text Processor (backend/core/processor)  │   │    │
│  │  │ • Clean text (normalize whitespace)      │   │    │
│  │  │ • Chunk text (sliding window)            │   │    │
│  │  └──────────────────────────────────────────┘   │    │
│  │                    │                              │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │ RAG Engine (backend/core/rag_engine)     │   │    │
│  │  │ ┌──────────────────────────────────────┐ │   │    │
│  │  │ │ Semantic Search (FAISS)              │ │   │    │
│  │  │ │ • Sentence Transformers embedding    │ │   │    │
│  │  │ │ • Vector similarity search (L2)      │ │   │    │
│  │  │ └──────────────────────────────────────┘ │   │    │
│  │  │ ┌──────────────────────────────────────┐ │   │    │
│  │  │ │ Keyword Search (BM25)                │ │   │    │
│  │  │ │ • TF-IDF based ranking               │ │   │    │
│  │  │ │ • Tokenized text matching            │ │   │    │
│  │  │ └──────────────────────────────────────┘ │   │    │
│  │  │ ┌──────────────────────────────────────┐ │   │    │
│  │  │ │ Hybrid Merge                         │ │   │    │
│  │  │ │ • Combine semantic + keyword results │ │   │    │
│  │  │ │ • Remove duplicates                  │ │   │    │
│  │  │ │ • Return top-k results               │ │   │    │
│  │  │ └──────────────────────────────────────┘ │   │    │
│  │  └──────────────────────────────────────────┘   │    │
│  │                    │                              │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │ LLM Service (backend/core/llm_service)   │   │    │
│  │  │ • Format evaluation prompt               │   │    │
│  │  │ • Call Mistral API                       │   │    │
│  │  │ • Parse & validate JSON response         │   │    │
│  │  │ • Return structured result               │   │    │
│  │  └──────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────┘    │
│                         │                                 │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
     External APIs    File System        LLM API
        │                │                │
   Mistral AI         PDF Files      Mistral Large
                      (data/)        (API call)
```

## Data Flow

### Upload Process

```
1. User uploads PDF
   ↓
2. FastAPI receives file
   ↓
3. Validate filename & size
   ↓
4. Save to disk (data/)
   ↓
5. PDF Manager extracts text
   ↓
6. Text Processor chunks text
   ↓
7. RAG Engine:
   • Generate embeddings (Sentence Transformers)
   • Build FAISS index (ANN search)
   • Build BM25 index (keyword search)
   ↓
8. Return success with chunk count
```

### Evaluation Process

```
1. User submits question + answer
   ↓
2. FastAPI validates input
   ↓
3. Check RAG ready
   ↓
4. RAG Engine retrieves context:
   • Generate query embedding
   • FAISS semantic search → top k
   • BM25 keyword search → top k
   • Hybrid merge → final results
   ↓
5. LLM Service constructs prompt:
   [Context] + [Question] + [Answer]
   ↓
6. Call Mistral API
   ↓
7. Parse JSON response
   ↓
8. Return structured evaluation:
   - score
   - feedback
   - points_hit
   - points_missed
```

## Component Details

### PDF Manager
- **Input**: File path to PDF
- **Output**: List of text chunks
- **Error Handling**: Graceful degradation, detailed error messages
- **Dependencies**: PyMuPDF (fitz)

### Text Processor
- **Input**: Raw text
- **Output**: Cleaned, chunked text
- **Algorithm**: Sliding window with overlap
- **Config**: CHUNK_SIZE (200), CHUNK_OVERLAP (50)

### RAG Engine
- **Semantic Search**: 
  - Model: `all-MiniLM-L6-v2` (384-dim embeddings)
  - Index: FAISS IndexFlatL2 (exact search)
  - Complexity: O(n) search, O(1) addition
  
- **Keyword Search**:
  - Algorithm: BM25Okapi
  - Complexity: O(n) search
  
- **Hybrid Merge**:
  - Deduplication + ranking
  - TOP_K limit: 4 (default)

### LLM Service
- **Model**: Mistral Large (latest)
- **Input**: Structured prompt with context
- **Output**: JSON-formatted evaluation
- **Error Handling**: JSON validation, fallback responses

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | HTML5, CSS3, Vanilla JS | User interface |
| Server | FastAPI, Uvicorn | REST API, async handling |
| PDF Processing | PyMuPDF | Text extraction |
| Embeddings | Sentence Transformers | Vector embeddings |
| Vector DB | FAISS | Semantic search |
| Keyword Search | rank-bm25 | BM25 ranking |
| LLM | Mistral AI | Answer evaluation |
| Config | python-dotenv | Environment management |
| Async | aiofiles | Non-blocking file I/O |

## Database Schema (In-Memory)

```
RAG Engine:
├── texts: List[str]
│   └── Stores all text chunks from PDFs
├── embeddings: numpy.ndarray [n_chunks × 384]
│   └── Vector embeddings for semantic search
├── index: FAISS.IndexFlatL2
│   └── Indexed embeddings for fast search
└── bm25: BM25Okapi
    └── BM25 index for keyword search

Upload:
└── data/: File storage
    ├── document_1.pdf
    ├── document_2.pdf
    └── ...
```

## Configuration Hierarchy

```
.env                    (local overrides)
    ↓
backend/core/config.py  (defaults + validation)
    ↓
Environment defaults
```

## Error Handling Strategy

```
User Input
    ↓
Validation Layer
├─ File size check
├─ File type check
├─ Content validation
├─ Field validation
    ↓
Processing Layer
├─ PDF parsing error → JSONResponse 400
├─ Chunking error → JSONResponse 400
├─ Embedding error → JSONResponse 500
    ↓
LLM Layer
├─ API error → JSONResponse 500
├─ JSON parse error → JSONResponse 400
├─ Invalid response → JSONResponse 400
    ↓
Response Layer
└─ Structured JSON response
```

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| PDF upload (5MB) | 1-2s | Depends on PDF complexity |
| Text extraction | 0.5-1s | PyMuPDF performance |
| Chunking (100 chunks) | 0.1s | Fast text processing |
| Embedding (100 chunks) | 2-3s | Sentence Transformers |
| FAISS indexing | 0.1s | CPU-based, scales with size |
| BM25 indexing | 0.1s | Fast tokenization |
| Query (semantic + keyword) | 0.2s | ANN search + BM25 |
| LLM evaluation | 3-5s | Network + Mistral processing |
| **Total evaluation** | **~4-6s** | End-to-end |

## Scalability Considerations

### Current State
- Single instance, in-memory RAG
- No persistence (resets on restart)
- Suitable for: Development, single user

### Scale to Multiple Users
1. Add Redis for embedding cache
2. Persist RAG index to disk
3. Load index on startup
4. Add evaluation queue (Celery/RQ)

### Scale to Enterprise
1. Database (PostgreSQL) for audit logs
2. Distributed task queue (Celery)
3. Caching layer (Redis)
4. Monitoring (Prometheus, ELK)
5. Load balancer (Nginx)
6. Multi-region deployment

## Security Model

```
Public Endpoints:
├─ GET  / (HTML)
├─ GET  /health
└─ GET  /status

Protected Endpoints (file validation):
├─ POST /upload (size, type, content checks)
└─ POST /evaluate (input validation)

Not Implemented (Future):
├─ Authentication (API keys, OAuth)
├─ Authorization (role-based access)
├─ Rate limiting (per IP/user)
└─ Audit logging (detailed event tracking)
```

## Future Enhancements

1. **Persistence**: Save/load RAG indices
2. **Caching**: Redis for embeddings
3. **Authentication**: API key / OAuth2
4. **Monitoring**: Prometheus metrics
5. **Batch Processing**: Evaluate multiple answers
6. **Multi-language**: Support non-English PDFs
7. **CustomModels**: Bring your own embedding/LLM
8. **Feedback Loop**: Learn from corrections

---

**Questions? Check the code comments and docstrings!**
