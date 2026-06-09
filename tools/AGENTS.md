# DOX contract - a0_postgresql/tools

## Purpose

Agent-facing PostgreSQL/pgvector tools.

## Ownership

- Tools own request parsing and agent response shape.
- Database access must route through helpers.

## Local Contracts

- Keep SQL safety policy explicit in tool results.
- Do not hide failed queries or connection failures.

## Work Guidance

- Update prompt guidance when tool arguments or result fields change.

## Verification

- Run `python -m py_compile` on touched tool files.

## Child DOX Index

No child AGENTS.md files yet.
