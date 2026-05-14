"""
pg_query tool — lets the agent query PostgreSQL directly.

Usage in agent JSON:
  {
    "tool_name": "pg_query",
    "tool_args": {
      "query": "SELECT table_name FROM information_schema.tables WHERE table_schema='public'",
      "params": [],
      "max_rows": 50
    }
  }

Special queries:
  "list_tables"  — returns all tables in public schema
  "describe:<table>"  — returns column definitions for <table>
"""

import logging
from helpers.tool import Tool, Response

logger = logging.getLogger(__name__)


class PgQuery(Tool):
    """Query PostgreSQL database (pgvector-enabled)."""

    async def execute(self, **kwargs) -> Response:
        await self.agent.handle_intervention()

        query: str = (self.args.get("query") or "").strip()
        params: list = self.args.get("params") or []
        max_rows: int = min(int(self.args.get("max_rows", 100)), 500)

        if not query:
            return Response(message="'query' argument is required.", break_loop=False)

        try:
            from usr.plugins.a0_postgresql.helpers.postgres_client import get_client
            client = await get_client()

            # ── Special shortcuts ───────────────────────────────────────────
            if query.lower() == "list_tables":
                tables = await client.list_tables()
                return Response(
                    message=f"Tables in public schema ({len(tables)}):\n" + "\n".join(f"  • {t}" for t in tables),
                    break_loop=False,
                    additional={"tables": tables},
                )

            if query.lower().startswith("describe:"):
                table_name = query[len("describe:"):].strip()
                cols = await client.describe_table(table_name)
                if not cols:
                    return Response(
                        message=f"Table '{table_name}' not found or has no columns.",
                        break_loop=False,
                    )
                lines = [f"  {c['column_name']} ({c['data_type']}) {'NULL' if c['is_nullable']=='YES' else 'NOT NULL'}" for c in cols]
                return Response(
                    message=f"Columns in {table_name}:\n" + "\n".join(lines),
                    break_loop=False,
                    additional={"columns": cols},
                )

            # ── Regular query ───────────────────────────────────────────────
            lowq = query.lower().lstrip()
            if any(lowq.startswith(kw) for kw in ("select", "with", "show", "explain")):
                rows = await client.fetch(query, *params, limit=max_rows)
                count = len(rows)
                if count == 0:
                    return Response(message="Query returned no rows.", break_loop=False, additional={"rows": []})

                # Format as a simple table for the agent
                cols = list(rows[0].keys())
                header = " | ".join(cols)
                sep = "-+-".join("-" * len(c) for c in cols)
                data_lines = [" | ".join(str(r.get(c, "")) for c in cols) for r in rows]
                table_text = "\n".join([header, sep] + data_lines)
                truncated = count >= max_rows
                note = f"\n(showing first {max_rows} rows — increase max_rows to see more)" if truncated else ""
                return Response(
                    message=f"Query returned {count} row(s):{note}\n\n{table_text}",
                    break_loop=False,
                    additional={"rows": rows, "count": count},
                )
            else:
                # DML/DDL
                status = await client.execute(query, *params)
                return Response(
                    message=f"Executed: {status}",
                    break_loop=False,
                    additional={"status": status},
                )

        except ConnectionError as e:
            return Response(
                message=f"PostgreSQL connection error: {e}\n\nCheck plugin settings (host/port/credentials).",
                break_loop=False,
            )
        except Exception as e:
            logger.error(f"[pg_query] Error: {e}")
            return Response(
                message=f"PostgreSQL error: {e}",
                break_loop=False,
            )
