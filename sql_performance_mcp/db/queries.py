from __future__ import annotations

import re

_IDENTIFIER = r"(?:`[^`]+`|[A-Za-z_][\w$]*)"
_QUALIFIED_IDENTIFIER = rf"{_IDENTIFIER}(?:\s*\.\s*{_IDENTIFIER})?"

_TABLE_PATTERN = re.compile(
    rf"\b(?:from|join|update|into)\s+({_QUALIFIED_IDENTIFIER})",
    re.IGNORECASE,
)


def strip_identifier_quotes(identifier: str) -> str:
    return identifier.strip().strip("`")


def split_table_name(table_name: str, default_schema: str | None = None) -> tuple[str | None, str]:
    parts = [strip_identifier_quotes(part) for part in re.split(r"\s*\.\s*", table_name, maxsplit=1)]
    if len(parts) == 2:
        return parts[0], parts[1]
    return default_schema, parts[0]


def extract_table_names(sql: str) -> list[str]:
    tables: list[str] = []
    for match in _TABLE_PATTERN.finditer(sql):
        table_name = re.sub(r"\s+", "", match.group(1))
        if table_name.lower().startswith(("select", "with")):
            continue
        if table_name not in tables:
            tables.append(table_name)
    return tables


def ensure_single_statement(sql: str) -> str:
    normalized = sql.strip()
    if not normalized:
        raise ValueError("SQL must not be empty.")

    statement = normalized[:-1].strip() if normalized.endswith(";") else normalized
    if ";" in statement:
        raise ValueError("Only a single SQL statement is supported.")
    return statement

