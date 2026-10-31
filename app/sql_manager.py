"""Conexión PostgreSQL y ejecución de sentencias SQL por transacción."""
from __future__ import annotations

import psycopg
import sqlparse

from .result_manager import MAX_ROWS, QueryResult, display_value


class SQLManager:
    def __init__(self) -> None:
        self.connection = None

    @property
    def is_connected(self) -> bool:
        return self.connection is not None and not self.connection.closed

    def connect(self, *, host: str, port: int, dbname: str,
                user: str, password: str) -> str:
        self.disconnect()
        if not host.strip() or not dbname.strip() or not user.strip():
            raise ValueError("Servidor, nombre de base de datos y usuario son obligatorios.")
        conn = psycopg.connect(
            host=host.strip(), port=port, dbname=dbname.strip(),
            user=user.strip(), password=password, connect_timeout=5,
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SHOW server_version")
                version = cur.fetchone()[0]
            conn.commit()
        except Exception:
            conn.close()
            raise
        self.connection = conn
        return f"Conexión correcta a PostgreSQL {version} · Base: {dbname}"

    def disconnect(self) -> None:
        if self.connection is not None:
            try:
                self.connection.close()
            finally:
                self.connection = None

    def execute(self, script: str) -> QueryResult:
        if not self.is_connected:
            raise RuntimeError("Primero debe conectarse a PostgreSQL.")
        statements = [s.strip() for s in sqlparse.split(script) if s.strip()]
        if not statements:
            raise ValueError("Escriba una instrucción SQL para ejecutarla.")

        last = QueryResult()
        try:
            # Todas las sentencias del bloque se confirman juntas (o se revierten).
            for statement in statements:
                with self.connection.cursor() as cur:
                    cur.execute(statement)
                    if cur.description is not None:
                        cols = [col.name for col in cur.description]
                        records = cur.fetchmany(MAX_ROWS + 1)
                        truncated = len(records) > MAX_ROWS
                        records = records[:MAX_ROWS]
                        rows = [tuple(display_value(x) for x in rec) for rec in records]
                        last = QueryResult(
                            columns=cols, rows=rows, truncated=truncated,
                            message=f"Consulta correcta · {len(rows)} fila(s) mostrada(s)"
                                    + (f" · límite {MAX_ROWS}" if truncated else ""),
                        )
                    else:
                        affected = cur.rowcount
                        detail = (f"{affected} fila(s) afectada(s)" if affected >= 0
                                  else "operación realizada")
                        last = QueryResult(message=f"Comando correcto · {detail}.")
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        if len(statements) > 1:
            last.message = f"{len(statements)} sentencias completadas. {last.message}"
        return last
