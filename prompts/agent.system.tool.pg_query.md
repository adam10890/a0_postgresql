# pg_query

Query or modify a PostgreSQL database (with optional pgvector extension).

## When to use
- Read data from PostgreSQL tables
- Run analytics queries
- Insert, update, or delete rows
- Perform vector similarity search via pgvector
- Inspect the database schema

## Operations

### Regular SQL query
```json
{
  "tool_name": "pg_query",
  "tool_args": {
    "query": "SELECT * FROM public.documents WHERE created_at > NOW() - INTERVAL '7 days' LIMIT 20",
    "params": [],
    "max_rows": 100
  }
}
```

### List all tables
```json
{
  "tool_name": "pg_query",
  "tool_args": { "query": "list_tables" }
}
```

### Describe a table's columns
```json
{
  "tool_name": "pg_query",
  "tool_args": { "query": "describe:public.documents" }
}
```

### DML (INSERT / UPDATE / DELETE)
```json
{
  "tool_name": "pg_query",
  "tool_args": {
    "query": "INSERT INTO events (name, payload) VALUES ($1, $2)",
    "params": ["agent_action", "{\"task\": \"summarize\"}"]
  }
}
```

## Parameters

| Parameter | Type    | Default | Description                              |
|-----------|---------|---------|------------------------------------------|
| `query`   | str     | required| SQL string, or `list_tables`, `describe:<table>` |
| `params`  | list    | `[]`    | Positional parameters ($1, $2, …)        |
| `max_rows`| int     | `100`   | Cap on SELECT results (max 500)          |

## Notes
- Connection config is set in the a0_postgresql plugin settings panel.
- SELECT queries return results as a formatted table.
- Use `describe:<tablename>` to inspect columns before writing queries.
- pgvector similarity search is available via the API (not this tool) or by writing raw `<=> ` operator SQL.
