# a0_postgresql — Reference

**Version:** 0.2.0 | Agent Zero v1.15–v1.17

## Overview

PostgreSQL + pgvector integration. The agent can run SQL queries, inspect schemas, and execute DML/DDL via the `pg_query` tool.

## Requirements

- PostgreSQL with pgvector: `docker pull pgvector/pgvector:pg16`
- asyncpg (installed automatically by the plugin into the A0 venv)

## Installation

```bash
docker cp ./a0_postgresql <container>:/a0/usr/plugins/a0_postgresql
```

Configure the connection in **Settings → External → PostgreSQL**.

## Configuration

| Setting | Description |
|---|---|
| `host` | Database host (default: `localhost`) |
| `port` | Database port (default: `5432`) |
| `database` | Database name |
| `user` | Username |
| `password` | Password |
| `ssl` | SSL mode (`disable`, `require`, …) |

## Tool API

Tool name: `pg_query`

### SELECT query
```json
{
  "tool_name": "pg_query",
  "tool_args": {
    "query": "SELECT id, name FROM users WHERE active = true",
    "max_rows": 50
  }
}
```

### List tables
```json
{"tool_name":"pg_query","tool_args":{"query":"list_tables"}}
```

### Describe table
```json
{"tool_name":"pg_query","tool_args":{"query":"describe:users"}}
```

### DML / DDL
```json
{
  "tool_name": "pg_query",
  "tool_args": {
    "query": "INSERT INTO notes (content) VALUES ($1)",
    "params": ["Hello world"]
  }
}
```

## REST endpoint

`POST /plugins/a0_postgresql/execute` — body: `{"query": "...", "params": [...]}`, returns rows or status.

## pgvector example

```json
{
  "tool_name": "pg_query",
  "tool_args": {
    "query": "SELECT id, content FROM embeddings ORDER BY embedding <-> $1::vector LIMIT 5",
    "params": [[0.1, 0.2, 0.3]]
  }
}
```

## pgvector setup

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings (
  id      serial PRIMARY KEY,
  content text,
  embedding vector(1536)
);
```

## Error handling

- `ConnectionError` → check host/port/credentials in Settings → External.
- SQL errors are returned as the tool message (not raised) — the agent sees the error and can retry.
