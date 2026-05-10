from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROMPT_TEMPLATE = Path(__file__).resolve().parents[1] / "prompts" / "performance_analysis.txt"


def analyze_performance(
    sql: str,
    execution_plan: Any,
    schema: Any,
    indexes: Any,
    database_type: str = "MySQL",
) -> str:
    """组装给大模型使用的 SQL 性能分析 prompt。"""
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    return template.format(
        database_type=database_type,
        sql=sql,
        execution_plan=_format_context(execution_plan),
        schema=_format_context(schema),
        indexes=_format_context(indexes),
    )


def _format_context(value: Any) -> str:
    """把 tool 返回的结构化对象格式化为易读 JSON，字符串则原样保留。"""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)
