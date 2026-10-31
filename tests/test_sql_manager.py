"""Pruebas de transacción con cursor ficticio: no requieren PostgreSQL levantado."""
from unittest.mock import MagicMock
import pytest

from app.sql_manager import SQLManager


def build_manager(cursor):
    manager = SQLManager()
    connection = MagicMock()
    connection.closed = False
    connection.cursor.return_value.__enter__.return_value = cursor
    manager.connection = connection
    return manager, connection


def test_select_displays_rows_and_commits():
    cur = MagicMock()
    cur.description = [MagicMock(name="ignored")]
    cur.description[0].name = "nombre"
    cur.fetchmany.return_value = [("Ana",), ("Carlos",)]
    manager, connection = build_manager(cur)
    result = manager.execute("SELECT nombre FROM estudiantes;")
    assert result.columns == ["nombre"]
    assert result.rows == [("Ana",), ("Carlos",)]
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()


def test_update_reports_count():
    cur = MagicMock()
    cur.description = None
    cur.rowcount = 2
    manager, connection = build_manager(cur)
    result = manager.execute("UPDATE estudiantes SET edad = 20;")
    assert "2 fila(s)" in result.message
    connection.commit.assert_called_once()


def test_error_rolls_back():
    cur = MagicMock()
    cur.execute.side_effect = RuntimeError("fallo simulado")
    manager, connection = build_manager(cur)
    with pytest.raises(RuntimeError, match="fallo simulado"):
        manager.execute("SELECT * FROM mal;")
    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
