# a0_postgresql

> PostgreSQL + pgvector integration. Provides pg_query tool for agents, asyncpg pool helper, and a settings panel for connection config. Requires pgvector/pgvector Docker image.

**Version:** 0.2.0

## Installation

### Option A: Upload ZIP (easiest)
1. Open Agent Zero GUI
2. Go to **Settings → Plugins**
3. Click **Upload ZIP**
4. Select `a0_postgresql.zip`

### Option B: Git (private repo)
1. Open Agent Zero GUI
2. Go to **Settings → Plugins → Install from Git**
3. Enter the repo URL and your Personal Access Token

### Option C: Manual copy
```bash
# Copy plugin folder to any Agent Zero container
docker cp ./a0_postgresql <container>:/a0/usr/plugins/a0_postgresql
```

## Documentation

- [`docs/COMP_POSTGRESQL.md`](docs/COMP_POSTGRESQL.md)
