
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

        # Tetap mendukung aturan khusus untuk kompatibilitas
        # dengan kode atau pengujian yang sudah ada.
        self.rule = rule or BarcodeRule()

    def validate_operator(self, operator_code):
        operator = self.database.get_operator(operator_code)

        if operator is None or operator["is_active"] != 1:
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

        return barcode[start:end] or None

    def inspect(
        self,
        operator_code,
        operator_name,
        box_barcode,
        unit_barcode,
    ):
        box_barcode = box_barcode.strip()
        unit_barcode = unit_barcode.strip()

        box_key = None
        unit_key = None
        matched_pair = None
        reason = None

        if not box_barcode or not unit_barcode:
            judgment = "NG"
            reason = "Barcode Box dan Barcode Unit wajib diisi."


        else:
            pairs = self.database.get_all_barcode_pairs()
            active_pairs = [
                pair
                for pair in pairs
                if pair["is_active"] == 1
            ]

            # Jika tidak ada pasangan aktif, jangan anggap
            # barcode pendek sebagai pasangan yang valid.
            if not active_pairs:
                judgment = "NG"
                reason = "Pasangan Box Key dan Unit Key tidak terdaftar."

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

            else:
                # Cek apakah barcode cukup panjang untuk setidaknya
                # satu aturan ekstraksi pasangan yang aktif.
                box_can_be_extracted = any(
                    self.extract_key(
                        box_barcode,
                        pair["box_start_position"] - 1,
                        pair["box_length"],
                    ) is not None
                    for pair in active_pairs
                )

                unit_can_be_extracted = any(
                    self.extract_key(
                        unit_barcode,
                        pair["unit_start_position"] - 1,
                        pair["unit_length"],
                    ) is not None
                    for pair in active_pairs
                )

                if not box_can_be_extracted:
                    judgment = "NG"
                    reason = "Format Barcode Box tidak valid."

                elif not unit_can_be_extracted:
                    judgment = "NG"
                    reason = "Format Barcode Unit tidak valid."

                else:
                    matched_pair = None

                    for pair in active_pairs:
                        candidate_box_key = self.extract_key(
                            box_barcode,
                            pair["box_start_position"] - 1,
                            pair["box_length"],
                        )

                        candidate_unit_key = self.extract_key(
                            unit_barcode,
                            pair["unit_start_position"] - 1,
                            pair["unit_length"],
                        )

                        if (
                            candidate_box_key == pair["box_key"]
                            and candidate_unit_key == pair["unit_key"]
                        ):
                            matched_pair = pair
                            box_key = candidate_box_key
                            unit_key = candidate_unit_key
                            break

                    if matched_pair is not None:
                        judgment = "OK"
                        reason = None
                    else:
                        judgment = "NG"
                        reason = (
                            "Tidak ditemukan pasangan barcode aktif "
                            "yang cocok dengan aturan ekstraksinya."
                        )

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
