
import pytest

from app.database import DatabaseManager


@pytest.fixture
def db(tmp_path):
    database_path = tmp_path / "test_database.db"
    return DatabaseManager(database_path)


def test_add_and_get_operator(db):
    db.add_operator("OP001", "Operator Satu")

    operator = db.get_operator("OP001")

    assert operator is not None
    assert operator["operator_code"] == "OP001"
    assert operator["operator_name"] == "Operator Satu"
    assert operator["is_active"] == 1


def test_unknown_operator_returns_none(db):
    assert db.get_operator("OP999") is None


def test_add_and_check_barcode_pair(db):
    db.add_barcode_pair("7036", "7830H")

    assert db.is_valid_barcode_pair("7036", "7830H")
    assert not db.is_valid_barcode_pair("7036", "9999")


def test_inactive_barcode_pair_is_invalid(db):
    db.add_barcode_pair("7036", "7830H")

    with db.get_connection() as connection:
        connection.execute(
            """
            UPDATE barcode_pairs
            SET is_active = 0
            WHERE box_key = ? AND unit_key = ?
            """,
            ("7036", "7830H"),
        )

    assert not db.is_valid_barcode_pair("7036", "7830H")


def test_add_inspection_history(db):
    inspection_id = db.add_inspection(
        operator_code="OP001",
        operator_name="Operator Satu",
        box_barcode="7036-1234567",
        unit_barcode="7830HP707636",
        box_key="7036",
        unit_key="7830H",
        judgment="OK",
    )

    assert inspection_id > 0

    with db.get_connection() as connection:
        result = connection.execute(
            """
            SELECT *
            FROM inspection_history
            WHERE id = ?
            """,
            (inspection_id,),
        ).fetchone()

    assert result is not None
    assert result["judgment"] == "OK"
    assert result["box_barcode"] == "7036-1234567"
    assert result["unit_barcode"] == "7830HP707636"


def test_invalid_operator_data_is_rejected(db):
    with pytest.raises(ValueError):
        db.add_operator("", "Operator Satu")


def test_invalid_judgment_is_rejected(db):
    with pytest.raises(ValueError):
        db.add_inspection(
            operator_code="OP001",
            operator_name="Operator Satu",
            box_barcode="BOX001",
            unit_barcode="UNIT001",
            box_key="BOX",
            unit_key="UNIT",
            judgment="MAYBE",
        )
