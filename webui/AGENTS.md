# DOX contract - a0_postgresql/webui

## Purpose

Settings panel and UI assets for PostgreSQL configuration.

## Ownership

- UI collects configuration and displays status; helpers/API own behavior.
- Do not embed secrets in static files.

## Local Contracts

- Keep field names aligned with API/config expectations.

## Work Guidance

- Preserve graceful error display for missing database services.

## Verification

- Inspect HTML/JS wiring after UI changes.

## Child DOX Index

No child AGENTS.md files yet.
