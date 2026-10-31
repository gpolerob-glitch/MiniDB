"""Conexión y operaciones MongoDB; admite comandos JSON y un subconjunto de mongosh.

No se usa eval/exec: los argumentos se convierten con JSON5 y solo se permiten
métodos enumerados explícitamente.
"""
from __future__ import annotations

import json
import re
from typing import Any

import json5
from bson import json_util
from pymongo import ASCENDING, MongoClient

from .result_manager import MAX_ROWS, QueryResult, display_value, documents_result, scalar_result

_METHODS = {
    "insertOne": "insert_one", "insertMany": "insert_many",
    "find": "find", "findOne": "find_one",
    "updateOne": "update_one", "updateMany": "update_many",
    "deleteOne": "delete_one", "deleteMany": "delete_many",
    "countDocuments": "count_documents",
    "createIndex": "create_index", "dropIndex": "drop_index",
    "drop": "drop_collection",
}
_DB_METHODS = {"createCollection": "create_collection", "listCollections": "list_collections"}
_SHELL = re.compile(r"^db\.([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z][A-Za-z0-9_]*)\s*\((.*)\)\s*;?$", re.S)
_DB_SHELL = re.compile(r"^db\.([A-Za-z][A-Za-z0-9_]*)\s*\((.*)\)\s*;?$", re.S)


def parse_mongo_command(source: str) -> dict[str, Any]:
    """Acepta un objeto JSON/JSON5 o una llamada mongosh permitida.

    Ejemplo: db.estudiantes.insertOne({nombre: 'Ana'})
    No admite funciones JavaScript, ObjectId(...) ni encadenamientos .limit().
    BSON Extended JSON sí: {"_id": {"$oid": "..."}}.
    """
    source = source.strip()
    if not source:
        raise ValueError("Escriba una operación MongoDB.")
    try:
        if source.startswith("{"):
            obj = json5.loads(source)
            if not isinstance(obj, dict):
                raise ValueError("La operación JSON debe ser un objeto.")
            return json_util.loads(json.dumps(obj))

        match = _SHELL.fullmatch(source)
        if match:
            collection, method, args_string = match.groups()
            operation = _METHODS.get(method)
            if operation is None:
                raise ValueError(f"Método mongosh no admitido: {method}.")
            args = json5.loads("[" + args_string + "]")
            args = json_util.loads(json.dumps(args))
            return _shell_to_command(operation, collection, args)

        match = _DB_SHELL.fullmatch(source)
        if match:
            method, args_string = match.groups()
            operation = _DB_METHODS.get(method)
            if operation is None:
                raise ValueError(f"Método de base de datos no admitido: {method}.")
            args = json5.loads("[" + args_string + "]")
            return {"operation": operation, "name": args[0] if args else None}
    except (ValueError, TypeError) as exc:
        if isinstance(exc, ValueError) and ("no admitido" in str(exc) or "La operación" in str(exc)):
            raise
        raise ValueError(f"Sintaxis MongoDB inválida: {exc}") from exc
    raise ValueError("Comando no admitido. Use JSON o db.coleccion.metodo(...).")


def _shell_to_command(operation: str, collection: str, args: list) -> dict[str, Any]:
    cmd: dict[str, Any] = {"operation": operation, "collection": collection}
    if operation == "drop_collection":
        return cmd
    if operation == "insert_one":
        cmd["document"] = args[0] if len(args) > 0 else None
    elif operation == "insert_many":
        cmd["documents"] = args[0] if len(args) > 0 else None
    elif operation in ("find", "find_one", "count_documents", "delete_one", "delete_many"):
        cmd["filter"] = args[0] if args else {}
        if operation in ("find", "find_one") and len(args) > 1:
            cmd["projection"] = args[1]
    elif operation in ("update_one", "update_many"):
        cmd["filter"] = args[0] if args else {}
        cmd["update"] = args[1] if len(args) > 1 else None
    elif operation == "create_index":
        cmd["keys"] = args[0] if args else None
        cmd["options"] = args[1] if len(args) > 1 else {}
    elif operation == "drop_index":
        cmd["name"] = args[0] if args else None
    return cmd


def _as_dict(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"El campo '{name}' debe ser un objeto.")
    return value


class MongoManager:
    def __init__(self) -> None:
        self.client: MongoClient | None = None
        self.database = None

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self.database is not None

    def connect(self, uri: str, database: str) -> str:
        self.disconnect()
        if not uri.strip() or not database.strip():
            raise ValueError("La URI y el nombre de base de datos son obligatorios.")
        client = MongoClient(uri.strip(), serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        try:
            client.admin.command("ping")
            db = client[database.strip()]
        except Exception:
            client.close()
            raise
        self.client = client
        self.database = db
        return f"Conexión correcta a MongoDB · Base: {database.strip()}"

    def disconnect(self) -> None:
        if self.client is not None:
            self.client.close()
        self.client = None
        self.database = None

    def execute(self, source: str) -> QueryResult:
        if not self.is_connected:
            raise RuntimeError("Primero debe conectarse a MongoDB.")
        cmd = parse_mongo_command(source)
        operation = cmd.get("operation")
        if not isinstance(operation, str):
            raise ValueError("La operación debe incluir el campo 'operation'.")
        db = self.database

        if operation == "list_collections":
            names = db.list_collection_names()
            return QueryResult(columns=["colección"], rows=[(name,) for name in names],
                               message=f"{len(names)} colección(es) encontrada(s).")
        if operation == "create_collection":
            name = _required_name(cmd.get("name"), "name")
            db.create_collection(name)
            return QueryResult(message=f"Colección '{name}' creada correctamente.")

        collection_name = _required_name(cmd.get("collection"), "collection")
        col = db[collection_name]
        if operation == "drop_collection":
            col.drop()
            return QueryResult(message=f"Colección '{collection_name}' eliminada.")

        if operation == "insert_one":
            document = _as_dict(cmd.get("document"), "document")
            result = col.insert_one(document)
            return QueryResult(message=f"Documento insertado · _id: {display_value(result.inserted_id)}")
        if operation == "insert_many":
            documents = cmd.get("documents")
            if not isinstance(documents, list) or not documents or not all(isinstance(x, dict) for x in documents):
                raise ValueError("'documents' debe ser una lista no vacía de objetos.")
            result = col.insert_many(documents)
            return QueryResult(message=f"{len(result.inserted_ids)} documentos insertados.")

        if operation == "find":
            filter_ = _as_dict(cmd.get("filter", {}), "filter")
            projection = cmd.get("projection")
            if projection is not None:
                _as_dict(projection, "projection")
            limit = cmd.get("limit", MAX_ROWS)
            if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
                raise ValueError("'limit' debe ser un entero positivo.")
            limit = min(limit, MAX_ROWS)
            cursor = col.find(filter_, projection)
            sort = cmd.get("sort")
            if sort is not None:
                sort = _as_dict(sort, "sort")
                cursor = cursor.sort(list(sort.items()))
            docs = list(cursor.limit(limit + 1))
            truncated = len(docs) > limit
            docs = docs[:limit]
            return documents_result(docs, f"{len(docs)} documento(s) mostrado(s).", truncated)

        if operation == "find_one":
            filter_ = _as_dict(cmd.get("filter", {}), "filter")
            projection = cmd.get("projection")
            if projection is not None:
                _as_dict(projection, "projection")
            doc = col.find_one(filter_, projection)
            return documents_result([doc] if doc else [], "1 documento encontrado." if doc else "Sin coincidencias.")

        if operation in ("update_one", "update_many"):
            filter_ = _as_dict(cmd.get("filter", {}), "filter")
            update = _as_dict(cmd.get("update"), "update")
            if not update:
                raise ValueError("'update' no puede estar vacío.")
            method = col.update_one if operation == "update_one" else col.update_many
            result = method(filter_, update)
            return QueryResult(message=f"{result.matched_count} coincidencia(s) · {result.modified_count} modificado(s).")

        if operation in ("delete_one", "delete_many"):
            filter_ = _as_dict(cmd.get("filter", {}), "filter")
            method = col.delete_one if operation == "delete_one" else col.delete_many
            result = method(filter_)
            return QueryResult(message=f"{result.deleted_count} documento(s) eliminado(s).")

        if operation == "count_documents":
            filter_ = _as_dict(cmd.get("filter", {}), "filter")
            value = col.count_documents(filter_)
            return scalar_result(value, "cantidad")

        if operation == "create_index":
            keys = _as_dict(cmd.get("keys"), "keys")
            if not keys:
                raise ValueError("Indique los campos para el índice.")
            options = _as_dict(cmd.get("options", {}), "options")
            allowed = {"name", "unique", "sparse"}
            if any(k not in allowed for k in options):
                raise ValueError("Opciones de índice permitidas: name, unique, sparse.")
            name = col.create_index(list(keys.items()), **options)
            return QueryResult(message=f"Índice '{name}' creado.")

        if operation == "drop_index":
            name = _required_name(cmd.get("name"), "name")
            col.drop_index(name)
            return QueryResult(message=f"Índice '{name}' eliminado.")

        raise ValueError(f"Operación no admitida: {operation!r}.")


def _required_name(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"El campo '{field}' es obligatorio y debe ser texto.")
    return value.strip()
