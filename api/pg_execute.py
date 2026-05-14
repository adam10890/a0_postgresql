"""
API handler for a0_postgresql plugin.

POST /api/plugins/a0_postgresql/pg_execute
Body: { "action": "ping"|"list_tables"|"describe"|"query", ... }
"""

from __future__ import annotations
import logging
from helpers.api import ApiHandler
from flask import Request, Response

logger = logging.getLogger(__name__)


class PgExecute(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "query")

        try:
            from usr.plugins.a0_postgresql.helpers.postgres_client import get_client, reset_client, PgConfig

            # ── Connection config override from request ──────────────────────
            if "pg_host" in input:
                cfg = PgConfig.from_settings(input)
                await reset_client()
                client = await get_client(cfg)
            else:
                client = await get_client()

            # ── Actions ──────────────────────────────────────────────────────
            if action == "ping":
                ok = await client.ping()
                return {"ok": ok, "message": "Connected" if ok else "Unreachable"}

            elif action == "list_tables":
                schema = input.get("schema", "public")
                tables = await client.list_tables(schema)
                return {"tables": tables, "count": len(tables)}

            elif action == "describe":
                table = input.get("table", "")
                if not table:
                    return {"error": "table is required"}
                schema = input.get("schema", "public")
                cols = await client.describe_table(table, schema)
                return {"columns": cols, "table": table}

            elif action == "query":
                query = (input.get("query") or "").strip()
                if not query:
                    return {"error": "query is required"}
                params = input.get("params") or []
                max_rows = min(int(input.get("max_rows", 200)), 1000)

                lowq = query.lower().lstrip()
                if any(lowq.startswith(kw) for kw in ("select", "with", "show", "explain")):
                    rows = await client.fetch(query, *params, limit=max_rows)
                    return {"rows": rows, "count": len(rows), "truncated": len(rows) >= max_rows}
                else:
                    status = await client.execute(query, *params)
                    return {"status": status, "ok": True}

            elif action == "vector_search":
                table = input.get("table", "")
                embedding_col = input.get("embedding_col", "embedding")
                query_vector = input.get("query_vector", [])
                if not table or not query_vector:
                    return {"error": "table and query_vector are required"}
                rows = await client.vector_search(
                    table=table,
                    embedding_col=embedding_col,
                    query_vector=query_vector,
                    select_cols=input.get("select_cols", "*"),
                    where=input.get("where", ""),
                    limit=int(input.get("limit", 5)),
                    min_similarity=float(input.get("min_similarity", 0.0)),
                )
                return {"rows": rows, "count": len(rows)}

            else:
                return {"error": f"Unknown action '{action}'. Use: ping, list_tables, describe, query, vector_search"}

        except ConnectionError as e:
            return {"error": str(e), "ok": False}
        except Exception as e:
            logger.error(f"[pg_execute] {e}")
            return {"error": str(e), "ok": False}
