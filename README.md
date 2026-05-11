# sql-performance-mcp

[中文说明](README.zh-CN.md)

[GitHub](https://github.com/shiro-4q/sql-performance-mcp)

SQL performance analysis MCP server for MySQL, PostgreSQL, and SQL Server.

The workflow is:

1. User provides a SQL statement.
2. The model calls `get_execution_plan` to fetch the execution plan.
3. The model calls `get_table_schema` to fetch table columns.
4. The model calls `get_indexes` to fetch table indexes.
5. The model uses the `analyze_performance` prompt to assemble the final analysis prompt.

## Tools

### `get_execution_plan`

Runs the database-appropriate execution plan command for a single SQL statement.

Arguments:

- `sql`: SQL statement to inspect.
- `database`: optional database name. If omitted, the matching environment variable is used.
- `database_type`: optional database type. Supported values are `mysql`, `postgresql`, and `sqlserver`.

### `get_table_schema`

Reads column metadata from the database's catalog views.

Arguments:

- `sql`: SQL statement to inspect.
- `database`: optional database name.
- `tables`: optional explicit table list, useful for complex SQL where table extraction is ambiguous.
- `database_type`: optional database type.

### `get_indexes`

Reads index metadata from the database's catalog views.

Arguments:

- `sql`: SQL statement to inspect.
- `database`: optional database name.
- `tables`: optional explicit table list.
- `database_type`: optional database type.

### `analyze_performance`

Builds a database-specific performance analysis prompt from:

- `sql`
- `execution_plan`
- `schema`
- `indexes`

## Configuration

Set database connection settings with environment variables:

MySQL:

```powershell
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "password"
$env:MYSQL_DATABASE = "app_db"
```

PostgreSQL:

```powershell
$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "password"
$env:POSTGRES_DATABASE = "app_db"
```

SQL Server:

```powershell
$env:SQLSERVER_HOST = "127.0.0.1"
$env:SQLSERVER_PORT = "1433"
$env:SQLSERVER_USER = "sa"
$env:SQLSERVER_PASSWORD = "password"
$env:SQLSERVER_DATABASE = "app_db"
```

Optional:

```powershell
$env:SQL_PERFORMANCE_DB_TYPE = "mysql"
$env:MYSQL_CHARSET = "utf8mb4"
$env:MYSQL_CONNECT_TIMEOUT = "10"
$env:POSTGRES_CONNECT_TIMEOUT = "10"
$env:SQLSERVER_DRIVER = "ODBC Driver 18 for SQL Server"
```

## MCP Client Configuration

Use the published package from PyPI in your MCP client config:

```json
{
  "mcpServers": {
    "sql-performance-mcp": {
      "command": "uvx",
      "args": ["sql-performance-mcp"],
      "env": {
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "password",
        "MYSQL_DATABASE": "app_db"
      }
    }
  }
}
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

- `get_execution_plan` accepts one SQL statement only.
- SQL table extraction covers common `FROM`, `JOIN`, `UPDATE`, and `INSERT INTO` patterns. For CTEs, nested SQL, or generated SQL, pass `tables` explicitly to schema and index tools.
- For SQL Server and PostgreSQL, use `database_type` when the default environment setting is not enough.
