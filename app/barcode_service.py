
from dataclasses import dataclass
from typing import Optional

from app.database import DatabaseManager


@dataclass(frozen=True)
class BarcodeRule:
    box_start: int = 0
    box_length: int = 4
    unit_start: int = 0
    unit_length: int = 5
    version: int = 1


@dataclass(frozen=True)
class InspectionResult:
    judgment: str
    reason: Optional[str]
    box_key: Optional[str]
    unit_key: Optional[str]
    inspection_id: int


class BarcodeService:

    def __init__(
        self,
        database: DatabaseManager,
        rule: Optional[BarcodeRule] = None,
    ):
        self.database = database

        if rule is not None:
            # Pertahankan aturan khusus jika diberikan.
            self.rule = rule
        else:
            # Ambil konfigurasi ekstraksi dari SQLite.
            settings = self.database.get_barcode_rule_settings()

            self.rule = BarcodeRule(
                box_start=settings["box_start_position"] - 1,
                box_length=settings["box_length"],
                unit_start=settings["unit_start_position"] - 1,
                unit_length=settings["unit_length"],
            )

    def validate_operator(self, operator_code):
        operator = self.database.get_operator(operator_code)

        if operator is None:
            return None

        if operator["is_active"] != 1:
            return None

        return {
            "operator_code": operator["operator_code"],
            "operator_name": operator["operator_name"],
        }

    def extract_key(self, barcode, start, length):
        barcode = barcode.strip()

        if start < 0 or length <= 0:
            return None

        end = start + length

        if len(barcode) < end:
            return None

        key = barcode[start:end]

        return key or None

    def inspect(
        self,
        operator_code,
        operator_name,
        box_barcode,
        unit_barcode,
    ):
        box_barcode = box_barcode.strip()
        unit_barcode = unit_barcode.strip()

        box_key = self.extract_key(
            box_barcode,
            self.rule.box_start,
            self.rule.box_length,
        )

        unit_key = self.extract_key(
            unit_barcode,
            self.rule.unit_start,
            self.rule.unit_length,
        )

        reason = None

        if not box_barcode or not unit_barcode:
            judgment = "NG"
            reason = "Barcode Box dan Barcode Unit wajib diisi."

        elif box_key is None:
            judgment = "NG"
            reason = "Format Barcode Box tidak valid."

        elif unit_key is None:
            judgment = "NG"
            reason = "Format Barcode Unit tidak valid."

        elif not self.database.is_valid_barcode_pair(
            box_key,
            unit_key,
        ):
            judgment = "NG"
            reason = "Pasangan Box Key dan Unit Key tidak terdaftar."

        else:
            judgment = "OK"

        inspection_id = self.database.add_inspection(
            operator_code=operator_code,
            operator_name=operator_name,
            box_barcode=box_barcode,
            unit_barcode=unit_barcode,
            box_key=box_key,
            unit_key=unit_key,
            judgment=judgment,
            reason=reason,
            rule_version=self.rule.version,
        )

        return InspectionResult(
            judgment=judgment,
            reason=reason,
            box_key=box_key,
            unit_key=unit_key,
            inspection_id=inspection_id,
        )
