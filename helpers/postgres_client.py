"""
PostgreSQL + pgvector client for Agent Zero a0_postgresql plugin.

Manages an asyncpg connection pool. Connection parameters are read from
plugin config (set in the a0_postgresql settings panel) or from environment
variables (PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE).

Usage:
    from usr.plugins.a0_postgresql.helpers.postgres_client import get_client
    client = await get_client()
    rows = await client.fetch("SELECT * FROM my_table LIMIT 10")
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class PgConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "agent_zero"
    database: str = "agent_zero"
    min_pool_size: int = 1
    max_pool_size: int = 5
    command_timeout: float = 60.0

    @classmethod
    def from_env(cls) -> "PgConfig":
        """Load config from environment variables (set in secrets.env)."""
        return cls(
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            user=os.getenv("PG_USER", "postgres"),
            password=os.getenv("PG_PASSWORD", "agent_zero"),
            database=os.getenv("PG_DATABASE", "agent_zero"),
            min_pool_size=int(os.getenv("PG_MIN_POOL", "1")),
            max_pool_size=int(os.getenv("PG_MAX_POOL", "5")),
        )

    @classmethod
    def from_settings(cls, settings: dict) -> "PgConfig":
        """Load config from plugin settings dict."""
        return cls(
            host=settings.get("pg_host", os.getenv("PG_HOST", "localhost")),
            port=int(settings.get("pg_port", os.getenv("PG_PORT", "5432"))),
            user=settings.get("pg_user", os.getenv("PG_USER", "postgres")),
            password=settings.get("pg_password", os.getenv("PG_PASSWORD", "agent_zero")),
            database=settings.get("pg_database", os.getenv("PG_DATABASE", "agent_zero")),
        )


# ── Client ────────────────────────────────────────────────────────────────────

class PostgresClient:
    """
    Async PostgreSQL client with connection pooling and pgvector support.
    Safe to call from multiple coroutines — pool is created once.
    """

    def __init__(self, config: Optional[PgConfig] = None):
        self.config = config or PgConfig.from_env()
        self._pool = None
        self._lock = asyncio.Lock()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Create the connection pool (idempotent)."""
        async with self._lock:
            if self._pool is not None:
                return
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.user,
                    password=self.config.password,
                    database=self.config.database,
                    min_size=self.config.min_pool_size,
                    max_size=self.config.max_pool_size,
                    command_timeout=self.config.command_timeout,
                )
                logger.info(
                    f"[a0_postgresql] Pool connected to "
                    f"{self.config.host}:{self.config.port}/{self.config.database}"
                )
            except Exception as e:
                self._pool = None
                raise ConnectionError(f"PostgreSQL connection failed: {e}") from e

    async def close(self) -> None:
        """Close the connection pool."""
        async with self._lock:
            if self._pool:
                await self._pool.close()
                self._pool = None
                logger.info("[a0_postgresql] Pool closed")

    async def ping(self) -> bool:
        """Return True if the database is reachable."""
        try:
            await self.connect()
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    # ── Query helpers ─────────────────────────────────────────────────────────

    async def _pool_or_connect(self):
        if self._pool is None:
            await self.connect()
        return self._pool

    async def execute(self, query: str, *args) -> str:
        """Execute a DML/DDL query and return the status string."""
        pool = await self._pool_or_connect()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single scalar value."""
        pool = await self._pool_or_connect()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[dict]:
        """Fetch a single row as a dict, or None."""
        pool = await self._pool_or_connect()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch(self, query: str, *args, limit: int = 500) -> list[dict]:
        """
        Fetch multiple rows as a list of dicts.
        Safety cap: at most `limit` rows returned.
        """
        pool = await self._pool_or_connect()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
        result = [dict(r) for r in rows]
        if len(result) > limit:
            result = result[:limit]
        return result

    # ── Vector search ─────────────────────────────────────────────────────────

    async def vector_search(
        self,
        table: str,
        embedding_col: str,
        query_vector: list[float],
        select_cols: str = "*",
        where: str = "",
        limit: int = 5,
        min_similarity: float = 0.0,
    ) -> list[dict]:
        """
        pgvector cosine similarity search.

        Args:
            table:           qualified table name, e.g. 'public.documents'
            embedding_col:   column holding the vector, e.g. 'embedding'
            query_vector:    list of floats
            select_cols:     columns to return (default '*')
            where:           extra WHERE clause (without 'WHERE')
            limit:           max rows
            min_similarity:  minimum 1 - cosine_distance threshold
        """
        vec_str = f"[{','.join(map(str, query_vector))}]"
        extra_where = f"AND ({where})" if where else ""
        query = f"""
            SELECT {select_cols},
                   1 - ({embedding_col} <=> $1::vector) AS similarity
            FROM {table}
            WHERE 1 - ({embedding_col} <=> $1::vector) >= $2
            {extra_where}
            ORDER BY {embedding_col} <=> $1::vector
            LIMIT $3
        """
        pool = await self._pool_or_connect()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, vec_str, min_similarity, limit)
        return [dict(r) for r in rows]

    # ── Schema inspection ─────────────────────────────────────────────────────

    async def list_tables(self, schema: str = "public") -> list[str]:
        """Return list of table names in the given schema."""
        rows = await self.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = $1
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            schema,
        )
        return [r["table_name"] for r in rows]

    async def describe_table(self, table: str, schema: str = "public") -> list[dict]:
        """Return column definitions for a table."""
        return await self.fetch(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
            """,
            schema,
            table,
        )


# ── Singleton ─────────────────────────────────────────────────────────────────

_client: Optional[PostgresClient] = None
_client_lock = asyncio.Lock()


async def get_client(config: Optional[PgConfig] = None) -> PostgresClient:
    """Return the shared PostgresClient, connecting on first call."""
    global _client
    async with _client_lock:
        if _client is None:
            _client = PostgresClient(config)
        elif config is not None:
            # config override — replace pool
            await _client.close()
            _client = PostgresClient(config)
    return _client


async def reset_client() -> None:
    """Close and discard the singleton (e.g. after config change)."""
    global _client
    async with _client_lock:
        if _client is not None:
            await _client.close()
            _client = None
