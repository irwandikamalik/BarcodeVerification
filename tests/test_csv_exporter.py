
import csv

from app.csv_exporter import CSVExporter
from app.database import DatabaseManager


def test_export_inspection_history(tmp_path):
    database = DatabaseManager(
        tmp_path / "csv_export_test.db"
    )

    database.add_operator("OP001", "Operator Satu")
    database.add_barcode_pair("7036", "7830H")

    database.add_inspection(
        operator_code="OP001",
        operator_name="Operator Satu",
        box_barcode="7036-1234567",
        unit_barcode="7830HP707636",
        box_key="7036",
        unit_key="7830H",
        judgment="OK",
    )

    output_path = tmp_path / "exports" / "history.csv"
    exporter = CSVExporter(database)

    result = exporter.export_inspection_history(output_path)

    assert result["path"] == output_path
    assert result["count"] == 1
    assert output_path.exists()

    with output_path.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:
        rows = list(csv.reader(csv_file, delimiter=";"))

    assert rows[0] == CSVExporter.HEADERS
    assert len(rows) == 2
    assert rows[1][2] == "OP001"
    assert rows[1][4] == "7036-1234567"
    assert rows[1][8] == "OK"


def test_export_empty_history(tmp_path):
    database = DatabaseManager(
        tmp_path / "empty_csv_export_test.db"
    )
    output_path = tmp_path / "exports" / "empty.csv"

    exporter = CSVExporter(database)
    result = exporter.export_inspection_history(output_path)

    assert result["count"] == 0
    assert output_path.exists()

    with output_path.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:
        rows = list(csv.reader(csv_file, delimiter=";"))

    assert rows == [CSVExporter.HEADERS]
