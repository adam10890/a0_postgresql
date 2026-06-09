# DOX contract - a0_postgresql/helpers

## Purpose

Connection, pool, configuration, and database helper logic.

## Ownership

- Helpers own shared connection behavior.
- Credentials, DSNs, database dumps, and runtime state must not be committed.

## Local Contracts

- Centralize connection/pool handling here; tools and APIs should not open
  unrelated ad hoc connections.
- Failures must surface clear messages without leaking secrets.

## Work Guidance

- Keep pgvector-specific helpers separate from generic SQL helpers.

## Verification

- Run `python -m py_compile` on touched helper files.

## Child DOX Index

No child AGENTS.md files yet.
