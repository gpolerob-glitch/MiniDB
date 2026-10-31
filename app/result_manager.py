"""Representación neutral de respuestas SQL y MongoDB para la interfaz gráfica."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from bson import json_util

MAX_ROWS = 500


@dataclass
class QueryResult:
    columns: list[str] = field(default_factory=list)
    rows: list[tuple[str, ...]] = field(default_factory=list)
    message: str = ""
    truncated: bool = False


def display_value(value: Any) -> str:
    """Convierte tipos SQL/BSON y documentos anidados a texto legible."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple)):
        return json_util.dumps(value, ensure_ascii=False)
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if isinstance(value, (date, datetime)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def documents_result(documents: Iterable[dict[str, Any]], message: str,
                     truncated: bool = False) -> QueryResult:
    docs = list(documents)
    if not docs:
        return QueryResult(message=message, truncated=truncated)
    keys: list[str] = []
    for doc in docs:
        for key in doc:
            if key not in keys:
                keys.append(key)
    rows = [tuple(display_value(doc.get(key)) if key in doc else "" for key in keys)
            for doc in docs]
    return QueryResult(columns=keys, rows=rows, message=message, truncated=truncated)


def scalar_result(value: Any, label: str = "resultado") -> QueryResult:
    return QueryResult(columns=[label], rows=[(display_value(value),)], message="Consulta correcta.")
