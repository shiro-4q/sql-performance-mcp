from __future__ import annotations

import json
from typing import Any

PROMPT_TEMPLATE = """You are a MySQL performance optimization expert.

SQL:
{sql}

Execution plan:
{execution_plan}

Table schema:
{schema}

Indexes:
{indexes}

Please analyze:
1. Performance bottlenecks
2. Why the optimizer chose this plan
3. Whether indexes are needed
4. How to optimize
5. Provide actionable SQL or rewrite suggestions
"""


def analyze_performance(
    sql: str,
    execution_plan: Any,
    schema: Any,
    indexes: Any,
    database_type: str = "MySQL",
) -> str:
    return PROMPT_TEMPLATE.format(
        database_type=database_type,
        sql=sql,
        execution_plan=_format_context(execution_plan),
        schema=_format_context(schema),
        indexes=_format_context(indexes),
    )


def _format_context(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)
