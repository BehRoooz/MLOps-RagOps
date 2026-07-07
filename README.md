# RAGOps — Production RAG Pipeline

[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docs.docker.com/compose/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112-green)](https://fastapi.tiangolo.com)
[![Meilisearch](https://img.shields.io/badge/Meilisearch-1.16-orange)](https://www.meilisearch.com)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-Proxy-purple)](https://docs.litellm.ai)

RAGOps is a production-oriented **Retrieval-Augmented Generation (RAG)** platform. It ingests documents, indexes them with hybrid vector + keyword search, and answers questions using retrieved context and a hosted LLM — all orchestrated as containerized microservices with persistent storage, caching, and observability.

---

## Overview

RAGOps solves a common production problem: **how to let an LLM answer questions grounded in your own documents**, not just its training data.

The system provides:

- **Document ingestion** — JSON text, single PDF, and batch PDF pipelines
- **Hybrid retrieval** — BM25 keyword search combined with semantic vector search (Meilisearch)
- **RAG Q&A** — retrieve relevant chunks, synthesize an answer via Groq (through LiteLLM)
- **Object storage** — raw files persisted in MinIO (S3-compatible)
- **Metadata catalog** — document records tracked in PostgreSQL
- **Performance layer** — Redis caching for embeddings and RAG responses
- **Observability** — Prometheus metrics, Grafana dashboards, optional LangSmith tracing

The API is the primary interface. Interactive documentation is available at `/docs` once the stack is running.

---

## Architecture

```
┌──────────────┐     ┌─────────────────────────────────────────────────────────────┐
│   Client     │────▶│                    FastAPI Backend (:18000)                 │
│  (curl/SDK)  │     │  ingest · search · RAG · upload · metadata · metrics        │
└──────────────┘     └──────┬──────────┬──────────┬──────────┬──────────┬──────────┘
                            │          │          │          │          │
              ┌─────────────┘          │          │          │          └─────────────┐
              ▼                        ▼          ▼          ▼                        ▼
     ┌────────────────┐      ┌──────────────┐ ┌────────┐ ┌────────┐      ┌────────────────┐
     │  Meilisearch   │      │   LiteLLM    │ │ Redis  │ │ MinIO  │      │   PostgreSQL   │
     │  documents +   │      │   Proxy      │ │ Cache  │ │  S3    │      │   metadata     │
     │  chunks index  │      └──────┬───────┘ └────────┘ └────────┘      └────────────────┘
     └────────────────┘             │
                                    ▼
                          ┌─────────────────┐
                          │  Groq LLM       │       ┌────────────────────┐
                          │  (external)     │───────│  TEI Embeddings    │
                          └─────────────────┘       │ (CPU, 384-dim)     │
                                                    └────────────────────┘

     Observability:  Prometheus (:9090)  →  Grafana (:3000)
```

### Data stores and responsibilities

| Store | Role | Production purpose |
|-------|------|--------------------|
| **Meilisearch** | Search index (`documents` + `chunks` with vectors) | Fast hybrid retrieval at query time |
| **MinIO** | Raw file storage (`s3://documents/...`) | Durable object store for uploaded/ingested files |
| **PostgreSQL** | Document metadata catalog | Auditable record of what was uploaded and where |
| **Redis** | Embedding + RAG response cache | Reduced latency and lower LLM/embedding cost |

### Request flows

**Ingestion**

```
Document/PDF → Chunking → Embeddings (TEI via LiteLLM) → Meilisearch
              └→ MinIO (raw file) + Postgres (metadata)   [PDF/upload paths]
```

**RAG query**

```
Question → Query embedding → Hybrid search (Meilisearch) → Context assembly → LLM (Groq) → Answer + sources
```

---

## Production features

| Area | Implementation |
|------|----------------|
| **Service isolation** | Each concern (search, embeddings, LLM, storage) runs as its own container |
| **Health checks** | All core services expose health endpoints; backend validates embedding pipeline on `/health` |
| **Restart policies** | `unless-stopped` / `always` on stateful and critical services |
| **Persistent volumes** | Meilisearch, Redis, TEI model cache, Postgres, and MinIO data survive restarts |
| **Model abstraction** | LiteLLM proxy decouples the backend from specific LLM/embedding providers |
| **Caching** | Redis caches embeddings (1 h TTL) and RAG answers (10 min TTL) |
| **Metrics** | Prometheus scrapes `/metrics` from the FastAPI instrumentator |
| **Tracing** | LangSmith callbacks configured in LiteLLM for LLM observability |
| **CPU deployment** | TEI serves `all-MiniLM-L6-v2` embeddings without a GPU |
| **Index bootstrap** | `meili-init` job configures Meilisearch indexes and vector settings on startup |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Docker & Docker Compose | Latest stable versions |
| 4 GB+ RAM | 8 GB recommended (TEI model download on first boot) |
| 2 GB+ disk | Models, indexes, and object storage |
| Groq API key | Required for LLM completions ([console.groq.com](https://console.groq.com)) |
| LangSmith API key | Optional; enables tracing and RAGAS evaluation |

---

## Quick start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set GROQ_API_KEY, MEILI_KEY, and PROXY_KEY
```

### 2. Build images

The backend image is built locally from `backend/Dockerfile`. Other services use public images from Docker Hub / GHCR.

```bash
make build
# or: docker compose build
```

### 3. Start the stack

```bash
make up
# or: docker compose up -d
```

First startup may take several minutes while TEI downloads the embedding model.

### 4. Verify health

```bash
curl -s http://localhost:18000/health | jq .
docker compose ps
```

Expected health response:

```json
{
  "status": "healthy",
  "embeddings_available": true,
  "embedding_dimensions": 384
}
```

### 5. Load sample documents (optional)

```bash
docker compose --profile manual run --rm seed
```

### 6. Ask a question

```bash
curl -s -X POST http://localhost:18000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is retrieval-augmented generation?", "k": 5}' | jq .
```

---

## Configuration

All configuration is driven by environment variables. See [`.env.example`](.env.example) for the full template.

### Required variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for LLM completions |
| `MEILI_KEY` | Meilisearch master key |
| `PROXY_KEY` | LiteLLM proxy master key |
| `LITELLM_MODEL` | Chat model alias (default: `groq-llama3`) |
| `EMBEDDING_MODEL_NAME` | Embedding model alias (default: `local-embeddings`) |

### Infrastructure variables (Docker defaults)

| Variable | Default | Service |
|----------|---------|---------|
| `MEILI_URL` | `http://meilisearch:7700` | Meilisearch |
| `PROXY_URL` | `http://litellm:4000` | LiteLLM |
| `REDIS_URL` | `redis://redis:6379` | Redis |
| `POSTGRES_URL` | `postgresql://ragops:ragops@postgres:5432/metadata` | PostgreSQL |
| `MINIO_ENDPOINT` | `http://minio:9000` | MinIO |
| `MINIO_BUCKET` | `documents` | MinIO bucket name |
| `EMBED_DIM` | `384` | Must match TEI model output |

Model routing is defined in [`litellm/config.yaml`](litellm/config.yaml). Model aliases in `.env` must match the `model_name` entries in that file.

> **Security:** Never commit `.env` to version control. Rotate `MEILI_KEY`, `PROXY_KEY`, and MinIO credentials before any non-local deployment.

---

## Services

| Service | Host port | Health | Description |
|---------|-----------|--------|-------------|
| **backend** | 18000 | `GET /health` | FastAPI application — main API entry point |
| **meilisearch** | 7700 | `GET /health` | Hybrid search engine (documents + chunks indexes) |
| **litellm** | 4000 | `GET /health` | LLM and embedding proxy (Groq + TEI) |
| **tei-embeddings** | — (internal) | `GET /health` | CPU embedding inference (`all-MiniLM-L6-v2`) |
| **redis** | 6379 | TCP | Embedding and RAG response cache |
| **postgres** | 5432 | `pg_isready` | Document metadata catalog |
| **minio** | 9000 / 9001 | `GET /minio/health/live` | Object storage / web console |
| **prometheus** | 9090 | — | Metrics collection |
| **grafana** | 3000 | — | Dashboards (`admin` / `admin`) |
| **meili-init** | — | — | One-shot index configuration job |

**Useful URLs after startup:**

| URL | Purpose |
|-----|---------|
| http://localhost:18000/docs | Swagger UI — interactive API |
| http://localhost:18000/metrics | Prometheus metrics endpoint |
| http://localhost:3000 | Grafana dashboards |
| http://localhost:9001 | MinIO console |

---

## API reference

### Health and administration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health + embedding pipeline check |
| `GET` | `/stats` | Meilisearch document and chunk index statistics |
| `POST` | `/init-index` | Create/reconfigure Meilisearch indexes with vector settings |
| `POST` | `/test-embeddings` | Validate embedding generation |

### Ingestion (search index)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest` | Ingest JSON documents (`[{id, text, metadata}]`) |
| `POST` | `/ingest-pdf` | Ingest a single PDF (chunk, embed, index + store) |
| `POST` | `/ingest-pdf-batch` | Batch PDF ingestion |

### File storage and metadata

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload a file to MinIO and record metadata in Postgres |
| `GET` | `/metadata/{document_id}` | Retrieve document metadata by ID |

### Search and generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/search` | Full RAG — retrieve chunks and generate an LLM answer |
| `POST` | `/search-chunks` | Retrieve relevant chunks without LLM synthesis |
| `POST` | `/search-direct` | Direct document-level search |
| `POST` | `/search-rerank` | Hybrid search with cosine-similarity reranking |
| `POST` | `/chat` | Direct LLM chat (no retrieval) |

### Example: ingest text

```bash
curl -X POST http://localhost:18000/ingest \
  -H "Content-Type: application/json" \
  -d '[{
    "id": "doc-001",
    "text": "Retrieval-Augmented Generation combines search with language models.",
    "metadata": {"title": "RAG Overview", "category": "ai"}
  }]'
```

### Example: ingest a PDF

```bash
curl -X POST http://localhost:18000/ingest-pdf \
  -F "file=@pdf_files/linear_algebra.pdf"
```

### Example: RAG query

```bash
curl -X POST http://localhost:18000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain matrix multiplication", "k": 5, "use_embeddings": true}'
```

Response shape:

```json
{
  "answer": "...",
  "chunks": [{"id": "...", "document_id": "...", "content": "...", "chunk_index": 0}],
  "total_chunks_found": 5,
  "cached": false,
  "search_method": "hybrid"
}
```

---

## Operations

### Makefile commands

```bash
make help        # Show available commands
make build       # Build Docker images
make up          # Start all services
make down        # Stop all services
make restart     # Restart the stack
make logs        # Follow backend logs
make test        # Run comprehensive test suite
make clean       # Remove containers and volumes
make dev-reset   # Full reset: wipe volumes, restart, re-init indexes
```

### Docker Compose profiles

| Profile | Command | Purpose |
|---------|---------|---------|
| `manual` | `docker compose --profile manual run --rm seed` | Load sample documents |
| `eval` | `docker compose --profile eval run --rm ragas_eval` | Run RAGAS evaluation |

### Database schema

PostgreSQL is initialized from [`db/init.sql`](db/init.sql) on first container start:

```sql
CREATE TABLE documents (
  document_id   SERIAL PRIMARY KEY,
  filename      TEXT NOT NULL,
  upload_time   TIMESTAMP DEFAULT NOW(),
  chunk_count   INTEGER,
  embedding_model TEXT,
  minio_path    TEXT NOT NULL
);
```

> If the Postgres volume was created before `db/init.sql` existed, recreate it with `make dev-reset` or `docker compose down -v`.

---

## Monitoring and observability

### Prometheus

Scrapes the backend `/metrics` endpoint every 15 seconds. Configuration: [`monitoring/prometheus/prometheus.yml`](monitoring/prometheus/prometheus.yml).

### Grafana

Pre-provisioned datasource and dashboard. Access at http://localhost:3000 (default credentials: `admin` / `admin`). Dashboard: [`monitoring/grafana/dashboards/simple_rag_dashboard.json`](monitoring/grafana/dashboards/simple_rag_dashboard.json).

### LangSmith

LiteLLM is configured with LangSmith success/failure callbacks. Set `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, and `LANGSMITH_BASE_URL` in `.env` to enable distributed tracing of LLM calls.

### Structured logging

The backend emits structured JSON logs via the `ragops` logger. View with:

```bash
docker compose logs -f backend
```

---

## Testing

```bash
# Comprehensive integration tests (requires running stack)
make test

# Metadata / MinIO / Postgres tests
pytest tests/test_metadata.py

# Chunking validation
python tests/chunking_validation.py

# Quick RAG smoke test
python tests/test_rag_quick.py
```

---

## Production deployment guide

### Before going live

1. **Rotate all secrets** — `MEILI_KEY`, `PROXY_KEY`, MinIO credentials, Postgres password
2. **Restrict port exposure** — bind internal services (Redis, Postgres, Meilisearch) to private networks only
3. **Use external secrets management** — Docker secrets, Vault, or cloud provider secret stores instead of plain `.env` files
4. **Enable TLS** — terminate HTTPS at an ingress (Traefik, Nginx, cloud load balancer)
5. **Back up persistent volumes** — Meilisearch indexes, Postgres, and MinIO data
6. **Set resource limits** — define CPU/memory limits per service in Compose or your orchestrator

### Scaling considerations

| Component | Strategy |
|-----------|----------|
| **backend** | Horizontally scalable behind a load balancer (stateless) |
| **meilisearch** | Single instance or Meilisearch Cloud for HA |
| **redis** | Single instance; use Redis Sentinel/Cluster for HA |
| **tei-embeddings** | Scale replicas; consider GPU instances for higher throughput |
| **litellm** | Scale replicas; configure provider rate limits and fallbacks |
| **postgres** | Managed database service recommended for production |
| **minio** | Distributed MinIO or cloud S3 for durability |

### Recommended resource allocation

| Service | Memory | CPU |
|---------|--------|-----|
| backend | 1–2 GB | 1 core |
| meilisearch | 1–2 GB | 1 core |
| tei-embeddings | 2–4 GB | 2 cores |
| litellm | 512 MB–1 GB | 0.5 core |
| postgres | 512 MB–1 GB | 0.5 core |
| minio | 512 MB | 0.5 core |
| redis | 256 MB | 0.25 core |

### Backup procedures

```bash
# Meilisearch documents dump
curl -H "Authorization: Bearer $MEILI_KEY" \
  "http://localhost:7700/indexes/documents/documents" > backup_documents.json

# Meilisearch chunks dump
curl -H "Authorization: Bearer $MEILI_KEY" \
  "http://localhost:7700/indexes/chunks/documents" > backup_chunks.json

# Postgres metadata
docker compose exec postgres pg_dump -U ragops metadata > backup_metadata.sql
```

---

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── core/             # Config, clients, logging
│   │   ├── eval/             # RAGAS evaluation
│   │   ├── models/           # Pydantic request/response schemas
│   │   ├── services/         # Business logic (ingestion, RAG, storage)
│   │   └── utils/            # Caching, hashing
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed_data.py          # Sample document loader
├── db/
│   └── init.sql              # Postgres schema (runs on first start)
├── litellm/
│   └── config.yaml           # LLM routing, caching, LangSmith callbacks
├── monitoring/
│   ├── prometheus/
│   └── grafana/
├── pdf_files/                # Sample PDFs for testing
├── scripts/
│   └── meili-init.sh         # Meilisearch index bootstrap
├── tests/
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `/health` returns `embeddings_available: false` | TEI still starting or LiteLLM misconfigured | Wait 2–3 min; check `docker compose logs tei-embeddings litellm` |
| `relation "documents" does not exist` | Postgres volume created before `db/init.sql` | `make dev-reset` or `docker compose down -v && docker compose up -d` |
| `500` on `/upload` or `/ingest-pdf` | MinIO or Postgres unreachable | Verify `docker compose ps`; check backend logs |
| Empty search results | No documents ingested | Run seed profile or ingest documents manually |
| LLM errors (`502`) | Invalid or missing `GROQ_API_KEY` | Verify key in `.env` and restart LiteLLM |
| Slow first query | Cold start: model load + cache miss | Expected; subsequent queries benefit from Redis cache |

```bash
# Diagnose a failing service
docker compose ps
docker compose logs backend --tail 50
docker compose logs tei-embeddings litellm postgres minio --tail 30
```

---

## Technology stack

| Layer | Technology |
|-------|------------|
| API | FastAPI 0.112, Uvicorn, Pydantic v2 |
| Search | Meilisearch 1.16 (hybrid BM25 + vector) |
| Embeddings | TEI (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim) |
| LLM | Groq `llama-3.1-8b-instant` via LiteLLM |
| Object storage | MinIO (S3-compatible) |
| Metadata DB | PostgreSQL 15 |
| Cache | Redis 7 |
| PDF processing | LangChain PyPDFLoader + RecursiveCharacterTextSplitter |
| Metrics | Prometheus + Grafana |
| Evaluation | RAGAS |
| Runtime | Python 3.11, Docker Compose |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.
