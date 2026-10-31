"""Pruebas unitarias del formato MongoDB (no requieren servidor activo)."""
import pytest
from bson.objectid import ObjectId

from app.nosql_manager import parse_mongo_command


def test_insert_shell():
    result = parse_mongo_command("db.estudiantes.insertOne({nombre: 'Ana', edad: 19})")
    assert result == {"operation": "insert_one", "collection": "estudiantes",
                      "document": {"nombre": "Ana", "edad": 19}}


def test_update_with_set_operator():
    result = parse_mongo_command('db.estudiantes.updateOne({nombre:"Ana"}, {$set:{edad:20}})')
    assert result["operation"] == "update_one"
    assert result["update"] == {"$set": {"edad": 20}}


def test_json_command():
    result = parse_mongo_command('{"operation":"find","collection":"estudiantes","filter":{}}')
    assert result["operation"] == "find"
    assert result["filter"] == {}


def test_extended_json_object_id():
    oid = "507f1f77bcf86cd799439011"
    result = parse_mongo_command('{"operation":"find","collection":"x","filter":{"_id":{"$oid":"' + oid + '"}}}')
    assert result["filter"]["_id"] == ObjectId(oid)


def test_create_collection():
    result = parse_mongo_command('db.createCollection("usuarios")')
    assert result == {"operation": "create_collection", "name": "usuarios"}


def test_unsupported_code_is_not_executed():
    with pytest.raises(ValueError):
        parse_mongo_command('db.estudiantes.find({}).limit(5)')


def test_empty_query():
    with pytest.raises(ValueError, match="Escriba"):
        parse_mongo_command('  ')
