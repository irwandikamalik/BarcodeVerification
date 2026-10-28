
import pytest

from app.barcode_service import BarcodeService, BarcodeRule
from app.database import DatabaseManager


@pytest.fixture
def service(tmp_path):
    database = DatabaseManager(
        tmp_path / "barcode_service_test.db"
    )

    database.add_operator("OP001", "Operator Satu")
    database.add_barcode_pair("7036", "7830H")

    return BarcodeService(database)


def test_validate_active_operator(service):
    operator = service.validate_operator("OP001")

    assert operator is not None
    assert operator["operator_name"] == "Operator Satu"


def test_unknown_operator_is_rejected(service):
    assert service.validate_operator("OP999") is None


def test_extract_barcode_keys(service):
    assert service.extract_key("7036-1234567", 0, 4) == "7036"
    assert service.extract_key("7830HP707636", 0, 5) == "7830H"


def test_valid_pair_returns_ok_and_saves_history(service):
    result = service.inspect(
        "OP001",
        "Operator Satu",
        "7036-1234567",
        "7830HP707636",
    )

    assert result.judgment == "OK"
    assert result.box_key == "7036"
    assert result.unit_key == "7830H"
    assert result.inspection_id > 0


def test_unknown_pair_returns_ng_and_saves_history(service):
    result = service.inspect(
        "OP001",
        "Operator Satu",
        "9999-1234567",
        "7830HP707636",
    )

    assert result.judgment == "NG"
    assert result.reason is not None
    assert result.inspection_id > 0


def test_short_barcode_returns_ng(service):
    result = service.inspect(
        "OP001",
        "Operator Satu",
        "70",
        "7830HP707636",
    )

    assert result.judgment == "NG"
    assert result.reason == "Format Barcode Box tidak valid."



def test_custom_extraction_rule(tmp_path):
    rule = BarcodeRule(
        box_start=0,
        box_length=4,
        unit_start=2,
        unit_length=5,
        version=2,
    )

    database = DatabaseManager(
        tmp_path / "custom_rule_test.db"
    )
    service = BarcodeService(database, rule)

    assert service.extract_key("AB7830HP707636", 2, 5) == "7830H"


def test_inactive_pair_returns_ng_and_saves_history(service):
    # Pasangan yang terdaftar awalnya valid.
    first_result = service.inspect(
        "OP001",
        "Operator Satu",
        "7036-1234567",
        "7830HP707636",
    )

    assert first_result.judgment == "OK"

    # Nonaktifkan pasangan yang sama.
    database = service.database
    pairs = database.get_all_barcode_pairs()
    pair_id = pairs[0]["id"]

    database.set_barcode_pair_active(pair_id, False)

    # Pasangan yang nonaktif seharusnya menghasilkan NG.
    second_result = service.inspect(
        "OP001",
        "Operator Satu",
        "7036-1234567",
        "7830HP707636",
    )

    assert second_result.judgment == "NG"
    assert second_result.reason is not None
    assert second_result.inspection_id > first_result.inspection_id


def test_deactivating_pair_preserves_inspection_history(service):
    # Simpan hasil inspeksi pertama.
    result = service.inspect(
        "OP001",
        "Operator Satu",
        "7036-1234567",
        "7830HP707636",
    )

    assert result.judgment == "OK"

    # Nonaktifkan pasangan barcode.
    database = service.database
    pairs = database.get_all_barcode_pairs()
    pair_id = pairs[0]["id"]

    database.set_barcode_pair_active(pair_id, False)

    # Riwayat inspeksi pertama tetap tersimpan.
    history = database.get_recent_inspections(limit=10)

    assert len(history) == 1
    assert history[0]["judgment"] == "OK"
    assert history[0]["box_key"] == "7036"
    assert history[0]["unit_key"] == "7830H"
