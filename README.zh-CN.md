# sql-performance-mcp

[English README](README.md)

[GitHub](https://github.com/shiro-4q/sql-performance-mcp)

这是一个面向 MySQL、PostgreSQL 和 SQL Server 的 SQL 性能分析 MCP Server。

工作流程：

1. 用户提供一段 SQL。
2. 模型调用 `get_execution_plan` 获取执行计划。
3. 模型调用 `get_table_schema` 获取表结构。
4. 模型调用 `get_indexes` 获取索引信息。
5. 模型调用 `analyze_performance` 组装最终分析提示词。

## 工具

### `get_execution_plan`

获取单条 SQL 的执行计划。

- `sql`：要分析的 SQL。
- `database`：可选数据库名。
- `database_type`：可选数据库类型，支持 `mysql`、`postgresql`、`sqlserver`。

### `get_table_schema`

读取表字段元数据。

- `sql`：要分析的 SQL。
- `database`：可选数据库名。
- `tables`：可选显式表名列表，适合复杂 SQL。
- `database_type`：可选数据库类型。

### `get_indexes`

读取索引元数据。

- `sql`：要分析的 SQL。
- `database`：可选数据库名。
- `tables`：可选显式表名列表。
- `database_type`：可选数据库类型。

### `analyze_performance`

根据以下内容生成数据库性能分析提示词：

- `sql`
- `execution_plan`
- `schema`
- `indexes`
- `database_type`

## 配置

MySQL：

```powershell
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "password"
$env:MYSQL_DATABASE = "app_db"
```

PostgreSQL：

```powershell
$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "password"
$env:POSTGRES_DATABASE = "app_db"
```

SQL Server：

```powershell
$env:SQLSERVER_HOST = "127.0.0.1"
$env:SQLSERVER_PORT = "1433"
$env:SQLSERVER_USER = "sa"
$env:SQLSERVER_PASSWORD = "password"
$env:SQLSERVER_DATABASE = "app_db"
```

可选：

```powershell
$env:SQL_PERFORMANCE_DB_TYPE = "mysql"
$env:MYSQL_CHARSET = "utf8mb4"
$env:MYSQL_CONNECT_TIMEOUT = "10"
$env:POSTGRES_CONNECT_TIMEOUT = "10"
$env:SQLSERVER_DRIVER = "ODBC Driver 18 for SQL Server"
```

## 运行

```powershell
uv sync
uv run sql-performance-mcp
```

## 说明

- `get_execution_plan` 只接受一条 SQL。
- SQL 表名提取覆盖常见的 `FROM`、`JOIN`、`UPDATE` 和 `INSERT INTO` 场景。
- 对于 CTE、嵌套 SQL 或动态生成 SQL，建议显式传入 `tables`。
