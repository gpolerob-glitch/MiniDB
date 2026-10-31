from bson.objectid import ObjectId

from app.result_manager import display_value, documents_result


def test_null_and_bools():
    assert display_value(None) == "NULL"
    assert display_value(True) == "true"
    assert display_value(False) == "false"


def test_documents_with_different_fields():
    result = documents_result([{"nombre": "Ana"}, {"edad": 19}], "ok")
    assert result.columns == ["nombre", "edad"]
    assert result.rows == [("Ana", ""), ("", "19")]


def test_objectid_visible_as_text():
    oid = ObjectId("507f1f77bcf86cd799439011")
    assert "507f1f77bcf86cd799439011" in display_value(oid)
