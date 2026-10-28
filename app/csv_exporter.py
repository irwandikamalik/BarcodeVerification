
import csv
from pathlib import Path

from app.database import DatabaseManager


class CSVExporter:
    """Mengekspor seluruh riwayat inspeksi ke file CSV."""

    HEADERS = [
        "ID",
        "Tanggal dan Waktu",
        "Kode Operator",
        "Nama Operator",
        "Barcode Box",
        "Barcode Unit",
        "Box Key",
        "Unit Key",
        "Hasil",
        "Alasan NG",
    ]

    def __init__(self, database: DatabaseManager):
        self.database = database

    def export_inspection_history(self, output_path):
        output_path = Path(output_path)

        # Ambil seluruh riwayat, dari yang terbaru sampai terlama.
        with self.database.get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    inspected_at,
                    operator_code,
                    operator_name,
                    box_barcode,
                    unit_barcode,
                    box_key,
                    unit_key,
                    judgment,
                    reason
                FROM inspection_history
                ORDER BY id DESC
                """
            ).fetchall()

        # Pastikan folder tujuan tersedia.
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # utf-8-sig membantu Excel mengenali encoding UTF-8.
        with output_path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerow(self.HEADERS)

            for row in rows:
                writer.writerow([
                    row["id"],
                    row["inspected_at"],
                    row["operator_code"],
                    row["operator_name"],
                    row["box_barcode"],
                    row["unit_barcode"],
                    row["box_key"] or "",
                    row["unit_key"] or "",
                    row["judgment"],
                    row["reason"] or "",
                ])

        return {
            "path": output_path,
            "count": len(rows),
        }
