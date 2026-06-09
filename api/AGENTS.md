# DOX contract - a0_postgresql/api

## Purpose

HTTP/API wrappers for PostgreSQL plugin UI and configuration flows.

## Ownership

- API files should stay thin and delegate database behavior to helpers.

## Local Contracts

- Validate inputs before passing them to helpers.
- Do not log secrets or full DSNs.

## Work Guidance

- Keep API route names aligned with webui callers.

## Verification

- Run `python -m py_compile` on touched API files.
- Inspect matching webui calls.

## Child DOX Index

No child AGENTS.md files yet.
