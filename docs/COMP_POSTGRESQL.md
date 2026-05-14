# Component: PostgreSQL + pgvector Integration

## Overview

| Field | Value |
| ----- | ----- |
| **Component ID** | `COMP-PG` |
| **Status** | 🟡 Code written, not yet deployed |
| **Category** | Data Persistence & Vector Search |
| **Migration Target** | `usr/plugins/a0_postgresql/` |
| **Migration Action** | **KEEP** — package as v1.7 plugin |

## Official Plugin Relationship

> **Overlap: NONE with official plugins**
>
> No official Agent Zero plugin provides persistent database storage, workflow caching, vector similarity search, or routing analytics. The official `_memory` plugin uses FAISS (in-memory/file-based) for vector search — our PostgreSQL + pgvector integration provides a **complementary** persistent storage layer with SQL querying, connection pooling, and knowledge base RAG.

## Purpose & Value

Provides Agent Zero with a persistent PostgreSQL database (with pgvector extension) for workflow caching, vector similarity search, routing analytics, step result caching, and a knowledge base for RAG retrieval. Runs as a separate Docker container accessible on `localhost:5433`.

### External Dependencies

| Dependency | Current Version | Latest Available | Notes |
| ---------- | --------------- | ---------------- | ----- |
| **pgvector Docker** | `pgvector/pgvector:0.8.1-pg17-trixie` | **0.8.2-pg18** | Update image tag in `docker-compose.yml` |
| **asyncpg** | ≥0.29 | **0.31.0** | Async PostgreSQL client |
| **psycopg2** | (in `database_tool.py`) | **2.9.10** | Sync client, not yet integrated |
| **sentence-transformers** | 3.0.1 | **5.3.0** | Embedding model for knowledge indexer |

> See [EXTERNAL_DEPENDENCIES.md](EXTERNAL_DEPENDENCIES.md) for full version registry.

**Key value propositions:**

- **Workflow caching** — stores successful workflow definitions for pattern-matched reuse
- **Vector RAG** — semantic search across indexed documentation via pgvector (384-dim, all-MiniLM-L6-v2)
- **Routing analytics** — records Smart Router decisions for analysis and optimization
- **Step caching** — avoids redundant computation by caching step results (SHA256 input hash, TTL)
- **Knowledge base** — chunked document storage with vector embeddings for contextual retrieval
- **Metrics tracking** — latency, token usage, cost, and success rates per workflow
- **Connection pooling** — async `asyncpg` pool (2-10 connections) for high throughput

## Infrastructure

### Docker Compose

| Service | Image | Port | Purpose |
| ------- | ----- | ---- | ------- |
| `agent_zero_pgvector` | `pgvector/pgvector:0.8.1-pg17-trixie` | `5433:5432` | PostgreSQL 17 + pgvector |
| `agent_zero_pgadmin` | `dpage/pgadmin4:latest` | `5050:80` | pgAdmin web UI |

### Database Schema

| Table | Schema | Purpose |
| ----- | ------ | ------- |
| `workflows.workflows` | `workflows` | Cached workflow definitions (id, pattern, steps, tags, routing) |
| `workflows.workflow_metrics` | `workflows` | Execution metrics (latency, tokens, cost, success) |
| `workflows.workflow_embeddings` | `workflows` | Vector embeddings for workflow similarity search |
| `workflows.step_cache` | `workflows` | Cached step results (input hash → output, TTL, hit count) |
| `workflows.routing_decisions` | `workflows` | Smart Router decision history (category, model, confidence) |
| `workflows.knowledge_chunks` | `workflows` | Chunked documents with vector embeddings for RAG |
| `workflows.knowledge_activity` | `workflows` | Search activity logs for monitoring |

### Extensions Enabled

- **`pg_trgm`** — trigram indexes for fuzzy text matching
- **`vector`** — pgvector for cosine similarity search on 384-dim embeddings

## File Inventory

### Configuration

| File | Role |
| ---- | ---- |
| `projects/phase_7_postgresql/docker-compose.yml` | Docker Compose for pgvector + pgAdmin |
| `projects/phase_7_postgresql/config/database.yaml` | Connection config (host, port, credentials, pool) |
| `projects/phase_7_postgresql/environment.yml` | Conda environment definition |
| `projects/phase_7_postgresql/requirements.txt` | Python dependencies |

### SQL Migrations

| File | Role |
| ---- | ---- |
| `projects/phase_7_postgresql/sql/001_create_database.sql` | Create `agent_zero` database + `workflows` schema |
| `projects/phase_7_postgresql/sql/002_enable_pgvector.sql` | Enable `pg_trgm` + `vector` extensions |
| `projects/phase_7_postgresql/sql/003_create_tables.sql` | Create all 5 workflow tables |
| `projects/phase_7_postgresql/sql/004_create_indexes.sql` | Create performance indexes (trigram, vector, B-tree) |
| `projects/phase_7_postgresql/sql/005_create_knowledge_chunks.sql` | Create knowledge base table + vector index |
| `projects/phase_7_postgresql/sql/006_create_activity_table.sql` | Create knowledge activity log table |

### Python Client

| File | Role |
| ---- | ---- |
| `projects/phase_7_postgresql/python/postgres_client.py` | Async PostgreSQL client with connection pooling (508 lines) |
| `projects/phase_7_postgresql/python/index_knowledge.py` | Knowledge base indexer — chunks markdown, generates embeddings, stores in pgvector |

### Agent Integration (not yet connected)

| File | Role |
| ---- | ---- |
| `extensions/tools/database_tool.py` | Simple sync SQL executor via psycopg2 (not registered as A0 tool) |

### API & Monitoring

| File | Role |
| ---- | ---- |
| `projects/phase_7_postgresql/api/knowledge_monitoring.py` | Flask API handlers for knowledge stats, activity, popular queries |

### Scripts & Tests

| File | Role |
| ---- | ---- |
| `projects/phase_7_postgresql/scripts/init_db.ps1` | PowerShell: start Docker, wait for healthy, run SQL migrations |
| `projects/phase_7_postgresql/tests/test_connection.py` | Connection tests (Docker + native, pgvector, schema) |
| `projects/phase_7_postgresql/tests/test_knowledge_base.py` | Knowledge base CRUD tests |

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Host Machine (Windows)                     │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  Agent Zero   │    │     LMM      │    │   pgvector    │  │
│  │  (a0-v098)    │    │  (Flask)     │    │  (PG 17)      │  │
│  │              │    │              │    │               │  │
│  │ PostgresClient│───→│              │    │ agent_zero DB │  │
│  │ (asyncpg)    │    │              │    │  ├─workflows  │  │
│  │              │    │              │    │  ├─metrics    │  │
│  │ DatabaseTool │───→│              │    │  ├─embeddings │  │
│  │ (psycopg2)   │    │              │    │  ├─step_cache │  │
│  └──────┬───────┘    └──────────────┘    │  ├─routing    │  │
│         │                                 │  ├─knowledge  │  │
│         │         localhost:5433           │  └─activity   │  │
│         └────────────────────────────────→│               │  │
│                                           └───────────────┘  │
│                                           Port 5433:5432     │
│                                                              │
│  ┌──────────────┐                                            │
│  │   pgAdmin     │    http://localhost:5050                   │
│  │  (Web UI)     │                                           │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

### PostgresClient API

| Method | Purpose |
| ------ | ------- |
| `connect()` / `close()` | Manage asyncpg connection pool |
| `insert_workflow()` | Insert/upsert workflow definition |
| `get_workflow()` | Get workflow by ID |
| `find_workflows_by_pattern()` | Fuzzy pattern match via pg_trgm |
| `update_workflow_usage()` | Increment usage counter |
| `record_metric()` | Record execution metric |
| `get_workflow_metrics()` | Get aggregated metrics |
| `insert_embedding()` | Store vector embedding |
| `search_similar()` | Vector similarity search (cosine) |
| `cache_step_result()` | Cache step output with TTL |
| `get_cached_step()` | Retrieve cached step result |
| `record_routing_decision()` | Log routing decision |
| `get_routing_stats()` | Get routing statistics |
| `search_knowledge()` | RAG: search knowledge chunks by vector similarity |
| `get_knowledge_stats()` | Get knowledge base statistics |

### Knowledge Indexer Pipeline

```text
Markdown files → DocumentChunker → chunks (1000 chars, 200 overlap)
                                       │
                                       ↓
                              SentenceTransformer (all-MiniLM-L6-v2)
                                       │
                                       ↓
                              384-dim embeddings
                                       │
                                       ↓
                              INSERT INTO knowledge_chunks
                              (file_path, chunk_index, text, metadata, embedding)
```

## Deployment Status

| Step | Status | Command |
| ---- | ------ | ------- |
| Start pgvector container | 🔴 Not done | `docker compose -f projects/phase_7_postgresql/docker-compose.yml up -d` |
| Create DB + schema | 🔴 Not done | `powershell -ExecutionPolicy Bypass -File projects/phase_7_postgresql/scripts/init_db.ps1` |
| Install Python deps | 🔴 Not done | `pip install asyncpg psycopg2-binary sentence-transformers` |
| Run connection tests | 🔴 Not done | `pytest projects/phase_7_postgresql/tests/test_connection.py` |
| Register as A0 tool | 🔴 Not done | Create proper Agent Zero tool class |
| Index knowledge base | 🔴 Not done | `python -m projects.phase_7_postgresql.python.index_knowledge --source docs` |

## Migration Notes

### As v1.7 Plugin: `usr/plugins/a0_postgresql/`

```text
usr/plugins/a0_postgresql/
├── __init__.py              # Plugin manifest
├── config/
│   └── database.yaml        # Connection config
├── python/
│   ├── postgres_client.py   # Async client (from projects/phase_7_postgresql/)
│   └── index_knowledge.py   # Knowledge indexer
├── extensions/python/
│   ├── 01_init/
│   │   └── _20_postgres_connect.py    # Initialize pool on agent startup
│   └── message_loop_end/
│       └── _90_record_metrics.py      # Record routing/workflow metrics
├── tools/
│   └── database_query.py    # Agent-facing SQL/search tool
├── sql/
│   └── *.sql                # Migration scripts
└── api/
    └── knowledge_monitoring.py  # REST endpoints for monitoring
```

### Key Decisions for Migration

1. **Connection from container** — Agent runs in Docker; pgvector also in Docker. Use Docker networking or `host.docker.internal` for connectivity
2. **Tool registration** — Create a proper Agent Zero `Tool` subclass that wraps `PostgresClient` for the agent to use
3. **Startup hook** — Extension in `01_init/` to establish connection pool on agent boot
4. **Metrics collection** — Extension in `message_loop_end/` to record routing decisions and workflow metrics automatically
5. **Knowledge sync** — Decide when to re-index: on startup, on file change, or manually
6. **FAISS vs pgvector** — The official `_memory` plugin uses FAISS; our knowledge base uses pgvector. These serve different purposes (agent memory vs documentation RAG) and coexist without conflict

### Dependencies

- `asyncpg` — async PostgreSQL driver
- `psycopg2-binary` — sync PostgreSQL driver (for DatabaseTool)
- `sentence-transformers` — embedding model (all-MiniLM-L6-v2)
- `pyyaml` — config loading

## Related Documents

- [Development Plan](../migration/DEVELOPMENT_PLAN_A0_ROUTER.md) — Phase 7 PostgreSQL integration
- [COMP: Memory System](COMP_MEMORY_SYSTEM.md) — FAISS-based memory (complementary)
- [COMP: Smart Router](COMP_SMART_ROUTER.md) — Routing decisions recorded to PostgreSQL
- [COMP: QuotaRouter](COMP_QUOTA_ROUTER.md) — Cost metrics tracked in PostgreSQL
- [Phase 7 Project README](../../projects/phase_7_postgresql/README.md) — Original project documentation
