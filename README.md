# sql-performance-mcp

[中文说明](README.zh-CN.md)

MySQL SQL performance analysis MCP server.

The workflow is:

1. User provides a SQL statement.
2. The model calls `get_execution_plan` to fetch the MySQL execution plan.
3. The model calls `get_table_schema` to fetch table columns.
4. The model calls `get_indexes` to fetch table indexes.
5. The model uses the `analyze_performance` prompt to assemble the final analysis prompt.

## Tools

### `get_execution_plan`

Runs `EXPLAIN FORMAT=JSON` for a single SQL statement, with a fallback to plain `EXPLAIN`.

Arguments:

- `sql`: SQL statement to inspect.
- `database`: optional MySQL database name. If omitted, `MYSQL_DATABASE` is used.

### `get_table_schema`

Reads column metadata from `information_schema.COLUMNS`.

Arguments:

- `sql`: SQL statement to inspect.
- `database`: optional MySQL database name.
- `tables`: optional explicit table list, useful for complex SQL where table extraction is ambiguous.

### `get_indexes`

Reads index metadata from `information_schema.STATISTICS`.

Arguments:

- `sql`: SQL statement to inspect.
- `database`: optional MySQL database name.
- `tables`: optional explicit table list.

### `analyze_performance`

Builds a MySQL performance analysis prompt from:

- `sql`
- `execution_plan`
- `schema`
- `indexes`

## Configuration

Set MySQL connection settings with environment variables:

```powershell
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "password"
$env:MYSQL_DATABASE = "app_db"
```

Optional:

```powershell
$env:MYSQL_CHARSET = "utf8mb4"
$env:MYSQL_CONNECT_TIMEOUT = "10"
```

## Run

Install dependencies:

```powershell
uv sync
```

Run the MCP server:

```powershell
uv run sql-performance-mcp
```

If you are not using `uv`, install from `requirements.txt` and run:

```powershell
python -m sql_performance_mcp.server
```

## Notes

- Only MySQL is implemented now.
- `get_execution_plan` accepts one SQL statement only.
- SQL table extraction covers common `FROM`, `JOIN`, `UPDATE`, and `INSERT INTO` patterns. For CTEs, nested SQL, or generated SQL, pass `tables` explicitly to schema and index tools.

