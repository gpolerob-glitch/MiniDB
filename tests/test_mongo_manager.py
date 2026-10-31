"""Pruebas con colección ficticia para operaciones básicas."""
from unittest.mock import MagicMock

from app.nosql_manager import MongoManager


def new_manager():
    manager = MongoManager()
    manager.client = MagicMock()
    manager.database = MagicMock()
    return manager


def test_insert_one_returns_id():
    manager = new_manager()
    manager.database.__getitem__.return_value.insert_one.return_value.inserted_id = "abc123"
    result = manager.execute('db.estudiantes.insertOne({nombre: "Ana"})')
    assert "abc123" in result.message


def test_find_returns_tabular_documents():
    manager = new_manager()
    col = manager.database.__getitem__.return_value
    cur = col.find.return_value
    cur.limit.return_value = iter([{"nombre": "Ana", "edad": 19}])
    result = manager.execute('db.estudiantes.find({})')
    assert result.columns == ["nombre", "edad"]
    assert result.rows == [("Ana", "19")]


def test_create_collection():
    manager = new_manager()
    result = manager.execute('db.createCollection("estudiantes")')
    manager.database.create_collection.assert_called_once_with("estudiantes")
    assert "creada" in result.message
