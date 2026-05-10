# sql-performance-mcp

[English README](README.md)

MySQL SQL 性能分析 MCP Server。

工作流程：

1. 用户提供 SQL。
2. 模型调用 `get_execution_plan` 获取执行计划。
3. 模型调用 `get_table_schema` 获取表结构。
4. 模型调用 `get_indexes` 获取索引信息。
5. 模型使用 `analyze_performance` 组装最终分析提示词。

## 工具

### `get_execution_plan`

对单条 SQL 执行 `EXPLAIN FORMAT=JSON`，失败后回退到普通 `EXPLAIN`。

参数：

- `sql`：要分析的 SQL。
- `database`：可选的 MySQL 数据库名。不传则使用 `MYSQL_DATABASE`。

### `get_table_schema`

从 `information_schema.COLUMNS` 读取字段元数据。

参数：

- `sql`：要分析的 SQL。
- `database`：可选的 MySQL 数据库名。
- `tables`：可选的显式表名列表，适合复杂 SQL。

### `get_indexes`

从 `information_schema.STATISTICS` 读取索引元数据。

参数：

- `sql`：要分析的 SQL。
- `database`：可选的 MySQL 数据库名。
- `tables`：可选的显式表名列表。

### `analyze_performance`

根据以下内容组装 MySQL 性能分析提示词：

- `sql`
- `execution_plan`
- `schema`
- `indexes`

## 配置

通过环境变量配置 MySQL 连接：

```powershell
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "password"
$env:MYSQL_DATABASE = "app_db"
```

可选：

```powershell
$env:MYSQL_CHARSET = "utf8mb4"
$env:MYSQL_CONNECT_TIMEOUT = "10"
```

## 运行

安装依赖：

```powershell
uv sync
```

运行 MCP Server：

```powershell
uv run sql-performance-mcp
```

如果不用 `uv`，可以安装 `requirements.txt` 后执行：

```powershell
python -m sql_performance_mcp.server
```

## 说明

- 当前只实现了 MySQL。
- `get_execution_plan` 只接受单条 SQL。
- 表名提取覆盖常见的 `FROM`、`JOIN`、`UPDATE`、`INSERT INTO` 场景。对于 CTE、嵌套 SQL 或动态生成 SQL，建议显式传入 `tables`。

