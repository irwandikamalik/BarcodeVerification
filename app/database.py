
import sqlite3
from pathlib import Path


# Lokasi database: folder data di root proyek.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "barcode_verification.db"


class DatabaseManager:
    def __init__(self, database_path=DATABASE_PATH):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.initialize_database()

    def get_connection(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize_database(self):
        with self.get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS operators (
                    operator_code TEXT PRIMARY KEY,
                    operator_name TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                        CHECK (is_active IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
                    )
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS barcode_pairs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    box_key TEXT NOT NULL,
                    unit_key TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                        CHECK (is_active IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
                    ),
                    UNIQUE (box_key, unit_key)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS inspection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inspected_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
                    ),
                    operator_code TEXT NOT NULL,
                    operator_name TEXT NOT NULL,
                    box_barcode TEXT NOT NULL,
                    unit_barcode TEXT NOT NULL,
                    box_key TEXT,
                    unit_key TEXT,
                    judgment TEXT NOT NULL
                        CHECK (judgment IN ('OK', 'NG')),
                    reason TEXT,
                    rule_version INTEGER NOT NULL DEFAULT 1
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_inspection_history_inspected_at
                ON inspection_history (inspected_at)
                """
            )

    def add_operator(self, operator_code, operator_name):
        operator_code = operator_code.strip()
        operator_name = operator_name.strip()

        if not operator_code or not operator_name:
            raise ValueError(
                "Kode dan nama operator wajib diisi."
            )

        with self.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO operators (
                    operator_code,
                    operator_name
                )
                VALUES (?, ?)
                """,
                (operator_code, operator_name),
            )

    def get_operator(self, operator_code):
        with self.get_connection() as connection:
            return connection.execute(
                """
                SELECT operator_code, operator_name, is_active
                FROM operators
                WHERE operator_code = ?
                """,
                (operator_code.strip(),),
            ).fetchone()

    def add_barcode_pair(self, box_key, unit_key):
        box_key = box_key.strip()
        unit_key = unit_key.strip()

        if not box_key or not unit_key:
            raise ValueError(
                "Box Key dan Unit Key wajib diisi."
            )

        with self.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO barcode_pairs (box_key, unit_key)
                VALUES (?, ?)
                """,
                (box_key, unit_key),
            )

    def is_valid_barcode_pair(self, box_key, unit_key):
        with self.get_connection() as connection:
            result = connection.execute(
                """
                SELECT 1
                FROM barcode_pairs
                WHERE box_key = ?
                  AND unit_key = ?
                  AND is_active = 1
                """,
                (box_key, unit_key),
            ).fetchone()

        return result is not None

    def add_inspection(
        self,
        operator_code,
        operator_name,
        box_barcode,
        unit_barcode,
        box_key,
        unit_key,
        judgment,
        reason=None,
        rule_version=1,
    ):
        if judgment not in ("OK", "NG"):
            raise ValueError("Judgment harus OK atau NG.")

        with self.get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO inspection_history (
                    operator_code,
                    operator_name,
                    box_barcode,
                    unit_barcode,
                    box_key,
                    unit_key,
                    judgment,
                    reason,
                    rule_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    operator_code,
                    operator_name,
                    box_barcode,
                    unit_barcode,
                    box_key,
                    unit_key,
                    judgment,
                    reason,
                    rule_version,
                ),
            )

            return cursor.lastrowid
