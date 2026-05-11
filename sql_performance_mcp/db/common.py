from __future__ import annotations

from typing import Any


def first_value(row: Any) -> Any:
    if row is None:
        return None
    if isinstance(row, dict):
        return next(iter(row.values())) if row else None
    if isinstance(row, (list, tuple)):
        return row[0] if row else None
    try:
        return row[0]
    except (KeyError, IndexError, TypeError):
        pass
    return row


def fetch_rows_as_dicts(cursor: Any) -> list[dict[str, Any]]:
    description = cursor.description or []
    columns = [column[0] for column in description]
    rows: list[dict[str, Any]] = []
    for row in cursor.fetchall():
        if isinstance(row, dict):
            rows.append(dict(row))
            continue
        if hasattr(row, "keys"):
            rows.append({column: row[column] for column in columns})
            continue
        rows.append(dict(zip(columns, row)))
    return rows
