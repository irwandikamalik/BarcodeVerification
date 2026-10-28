
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


def test_get_recent_inspections_returns_newest_first(tmp_path):
    database = DatabaseManager(
        tmp_path / "recent_inspections.db"
    )

    database.add_inspection(
        operator_code="OP001",
        operator_name="Operator Satu",
        box_barcode="7036-0001",
        unit_barcode="7830H-0001",
        box_key="7036",
        unit_key="7830H",
        judgment="OK",
    )

    database.add_inspection(
        operator_code="OP001",
        operator_name="Operator Satu",
        box_barcode="9999-0002",
        unit_barcode="7830H-0002",
        box_key="9999",
        unit_key="7830H",
        judgment="NG",
        reason="Pasangan barcode tidak terdaftar.",
    )

    rows = database.get_recent_inspections()

    assert len(rows) == 2
    assert rows[0]["judgment"] == "NG"
    assert rows[0]["box_key"] == "9999"
    assert rows[1]["judgment"] == "OK"


def test_get_recent_inspections_respects_limit(tmp_path):
    database = DatabaseManager(
        tmp_path / "limited_inspections.db"
    )

    for index in range(3):
        database.add_inspection(
            operator_code="OP001",
            operator_name="Operator Satu",
            box_barcode="BOX-{}".format(index),
            unit_barcode="UNIT-{}".format(index),
            box_key="BOX",
            unit_key="UNIT",
            judgment="OK",
        )

    rows = database.get_recent_inspections(limit=2)

    assert len(rows) == 2
    assert rows[0]["box_barcode"] == "BOX-2"
    assert rows[1]["box_barcode"] == "BOX-1"


def test_get_all_operators_returns_active_and_inactive(db):
    db.add_operator("OP002", "Operator Dua")
    db.add_operator("OP001", "Operator Satu")

    with db.get_connection() as connection:
        connection.execute(
            """
            UPDATE operators
            SET is_active = 0
            WHERE operator_code = ?
            """,
            ("OP002",),
        )

    operators = db.get_all_operators()

    assert len(operators) == 2

    # Daftar harus diurutkan berdasarkan kode operator.
    assert operators[0]["operator_code"] == "OP001"
    assert operators[1]["operator_code"] == "OP002"

    # Operator aktif dan nonaktif sama-sama ditampilkan.
    assert operators[0]["is_active"] == 1
    assert operators[1]["is_active"] == 0

    # Data waktu pendaftaran juga tersedia.
    assert operators[0]["created_at"] is not None


def test_set_operator_active_updates_status(db):
    db.add_operator("OP001", "Operator Satu")

    db.set_operator_active("OP001", False)
    assert db.get_operator("OP001")["is_active"] == 0

    db.set_operator_active("OP001", True)
    assert db.get_operator("OP001")["is_active"] == 1


def test_set_operator_active_rejects_unknown_operator(db):
    with pytest.raises(ValueError, match="Operator tidak ditemukan"):
        db.set_operator_active("OP999", False)
