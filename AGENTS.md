# DOX contract - a0_postgresql

## Purpose

PostgreSQL + pgvector integration plugin for Agent Zero. It provides the
`pg_query` tool, connection/pool helpers, API endpoints, and a settings panel
for database configuration.

## Ownership

- This folder is plugin source, not database storage.
- Connection credentials and runtime database data must stay outside source.
- The plugin may depend on a PostgreSQL/pgvector service, but must not silently
  create or destroy user databases.

## Local Contracts

- `plugin.yaml:name` must stay `a0_postgresql`.
- Tool code must use shared connection helpers rather than opening ad hoc
  connections in multiple places.
- SQL execution must keep the configured safety policy explicit in the tool
  response. Do not hide failed queries or connection failures.
- Web/API surfaces should stay thin wrappers over helper logic.

## Work Guidance

- Read `README.md` before changing install, Docker, or configuration behavior.
- Keep pgvector-specific behavior separate from generic SQL query behavior.
- Do not put secrets, DSNs, or local database dumps in this plugin directory.

## Verification

- Run `python -m py_compile` on touched Python files.
- For UI/API changes, inspect matching webui calls and API handler names.
- For manifest changes, verify `plugin.yaml` still declares the intended
  settings section.

## Child DOX Index

- `helpers/AGENTS.md` — connection pool, config, and database helper contracts.
- `tools/AGENTS.md` — agent-facing SQL/vector tool behavior.
- `api/AGENTS.md` — web/API endpoint wrappers.
- `webui/AGENTS.md` — settings panel UI.
- `prompts/AGENTS.md` — tool prompt guidance.
- `docs/AGENTS.md` — install and operator documentation.
