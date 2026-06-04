# AGENTS.md — a0_postgresql

**Version:** 0.2.0 | **Target:** Agent Zero v1.15–v1.17

## What this plugin does

PostgreSQL + pgvector integration for Agent Zero. Exposes a `pg_query` tool for SQL queries, a REST endpoint for UI-level queries, and a settings panel for connection config. Requires the `pgvector/pgvector` Docker image (or any PostgreSQL with pgvector).

## Key files

| Path | Role |
|---|---|
| `plugin.yaml` | Manifest — section: `external`, `title: "PostgreSQL"` |
| `tools/pg_query.py` | `PgQuery(Tool)` — SELECT, DML/DDL, `list_tables`, `describe:<table>` |
| `api/pg_execute.py` | REST endpoint for direct query execution |
| `helpers/postgres_client.py` | asyncpg pool singleton (`get_client()`) |
| `webui/` | Settings panel (host/port/credentials) |
| `prompts/` | Agent tool guidance |

## Tool: `pg_query`

Import: `from helpers.tool import Tool, Response`
Client: `from usr.plugins.a0_postgresql.helpers.postgres_client import get_client`

| Query form | Trigger | Returns |
|---|---|---|
| `SELECT …` / `WITH …` / `SHOW …` / `EXPLAIN …` | Starts with keyword | Rows as formatted table |
| `list_tables` | Exact string | Public schema table names |
| `describe:<table>` | Prefix | Column definitions |
| DML/DDL | All other SQL | Execution status string |

`max_rows` caps SELECT results (default 100, max 500).

## Client pool pattern

```python
from usr.plugins.a0_postgresql.helpers.postgres_client import get_client
client = await get_client()
rows = await client.fetch(query, *params, limit=max_rows)
```

Pool is created lazily on first call and reused across tool invocations.

## Error handling

| Exception | Meaning |
|---|---|
| `ConnectionError` | Pool could not connect — check settings |
| General `Exception` | SQL error — returned as message, not raised |

## How to add a query shortcut

Add an `elif query.lower().startswith("my_prefix"):` block inside `PgQuery.execute()` before the main `if any(lowq.startswith(kw) ...)` check.

## Constraints

- Connection config lives in the `external` settings section — never hardcode credentials.
- Pool singleton is per-process; reconnection is automatic via asyncpg.
- `max_rows` hard cap is 500 — do not raise this without pagination.
