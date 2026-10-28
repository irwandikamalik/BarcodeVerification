
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

            # Konfigurasi ekstraksi key barcode.
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS barcode_rule_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    box_start_position INTEGER NOT NULL
                        CHECK (box_start_position >= 1),
                    box_length INTEGER NOT NULL
                        CHECK (box_length >= 1),
                    unit_start_position INTEGER NOT NULL
                        CHECK (unit_start_position >= 1),
                    unit_length INTEGER NOT NULL
                        CHECK (unit_length >= 1)
                )
                """
            )

            # Buat konfigurasi default hanya jika belum tersedia.
            connection.execute(
                """
                INSERT OR IGNORE INTO barcode_rule_settings (
                    id,
                    box_start_position,
                    box_length,
                    unit_start_position,
                    unit_length
                )
                VALUES (1, 1, 4, 1, 5)
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

            
            # Migrasi: tambahkan konfigurasi ekstraksi ke setiap pasangan.
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(barcode_pairs)"
                ).fetchall()
            }

            new_columns = {
                "box_start_position": (
                    "INTEGER NOT NULL DEFAULT 1 "
                    "CHECK (box_start_position >= 1)"
                ),
                "box_length": (
                    "INTEGER NOT NULL DEFAULT 4 "
                    "CHECK (box_length >= 1)"
                ),
                "unit_start_position": (
                    "INTEGER NOT NULL DEFAULT 1 "
                    "CHECK (unit_start_position >= 1)"
                ),
                "unit_length": (
                    "INTEGER NOT NULL DEFAULT 5 "
                    "CHECK (unit_length >= 1)"
                ),
            }

            for column_name, column_definition in new_columns.items():
                if column_name not in columns:
                    connection.execute(
                        "ALTER TABLE barcode_pairs ADD COLUMN "
                        "{} {}".format(
                            column_name,
                            column_definition,
                        )
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

    
    def get_all_operators(self):
        with self.get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    operator_code,
                    operator_name,
                    is_active,
                    created_at
                FROM operators
                ORDER BY operator_code ASC
                """
            ).fetchall()

        return rows

    
    def set_operator_active(self, operator_code, is_active):
        operator_code = operator_code.strip()

        if not operator_code:
            raise ValueError("Kode operator wajib diisi.")

        if not isinstance(is_active, bool):
            raise ValueError("Status operator harus berupa True atau False.")

        with self.get_connection() as connection:
            cursor = connection.execute(
                """
                UPDATE operators
                SET is_active = ?
                WHERE operator_code = ?
                """,
                (int(is_active), operator_code),
            )

            if cursor.rowcount == 0:
                raise ValueError("Operator tidak ditemukan.")



    def add_barcode_pair(
        self,
        box_key,
        unit_key,
        box_start_position=1,
        box_length=4,
        unit_start_position=1,
        unit_length=5,
    ):
        box_key = box_key.strip()
        unit_key = unit_key.strip()

        if not box_key or not unit_key:
            raise ValueError(
                "Box Key dan Unit Key wajib diisi."
            )

        settings = {
            "Box posisi mulai": box_start_position,
            "Box length": box_length,
            "Unit posisi mulai": unit_start_position,
            "Unit length": unit_length,
        }

        for name, value in settings.items():
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 1
            ):
                raise ValueError(
                    "{} harus berupa bilangan bulat positif.".format(
                        name
                    )
                )

        with self.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO barcode_pairs (
                    box_key,
                    unit_key,
                    box_start_position,
                    box_length,
                    unit_start_position,
                    unit_length
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    box_key,
                    unit_key,
                    box_start_position,
                    box_length,
                    unit_start_position,
                    unit_length,
                ),
            )

    
    def update_barcode_pair(
        self,
        pair_id,
        box_key,
        unit_key,
        box_start_position,
        box_length,
        unit_start_position,
        unit_length,
    ):
        if (
            not isinstance(pair_id, int)
            or isinstance(pair_id, bool)
            or pair_id <= 0
        ):
            raise ValueError(
                "ID pasangan harus berupa bilangan bulat positif."
            )

        box_key = box_key.strip()
        unit_key = unit_key.strip()

        if not box_key or not unit_key:
            raise ValueError(
                "Box Key dan Unit Key wajib diisi."
            )

        settings = {
            "Box posisi mulai": box_start_position,
            "Box length": box_length,
            "Unit posisi mulai": unit_start_position,
            "Unit length": unit_length,
        }

        for name, value in settings.items():
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 1
            ):
                raise ValueError(
                    "{} harus berupa bilangan bulat positif.".format(
                        name
                    )
                )

        with self.get_connection() as connection:
            cursor = connection.execute(
                """
                UPDATE barcode_pairs
                SET
                    box_key = ?,
                    unit_key = ?,
                    box_start_position = ?,
                    box_length = ?,
                    unit_start_position = ?,
                    unit_length = ?
                WHERE id = ?
                """,
                (
                    box_key,
                    unit_key,
                    box_start_position,
                    box_length,
                    unit_start_position,
                    unit_length,
                    pair_id,
                ),
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    "Pasangan barcode tidak ditemukan."
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

    
    def get_all_barcode_pairs(self):
        with self.get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    box_key,
                    unit_key,
                    box_start_position,
                    box_length,
                    unit_start_position,
                    unit_length,
                    is_active,
                    created_at
                FROM barcode_pairs
                ORDER BY box_key ASC, unit_key ASC
                """
            ).fetchall()

        return rows

    
    def get_barcode_rule_settings(self):
        with self.get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    box_start_position,
                    box_length,
                    unit_start_position,
                    unit_length
                FROM barcode_rule_settings
                WHERE id = 1
                """
            ).fetchone()

        if row is None:
            raise RuntimeError(
                "Konfigurasi ekstraksi barcode tidak ditemukan."
            )

        return dict(row)

    def update_barcode_rule_settings(
        self,
        box_start_position,
        box_length,
        unit_start_position,
        unit_length,
    ):
        values = {
            "Box posisi mulai": box_start_position,
            "Box length": box_length,
            "Unit posisi mulai": unit_start_position,
            "Unit length": unit_length,
        }

        for name, value in values.items():
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 1
            ):
                raise ValueError(
                    "{} harus berupa bilangan bulat positif.".format(
                        name
                    )
                )

        with self.get_connection() as connection:
            connection.execute(
                """
                UPDATE barcode_rule_settings
                SET
                    box_start_position = ?,
                    box_length = ?,
                    unit_start_position = ?,
                    unit_length = ?
                WHERE id = 1
                """,
                (
                    box_start_position,
                    box_length,
                    unit_start_position,
                    unit_length,
                ),
            )
    
    def set_barcode_pair_active(self, pair_id, is_active):
        if (
            not isinstance(pair_id, int)
            or isinstance(pair_id, bool)
            or pair_id <= 0
        ):
            raise ValueError("ID pasangan harus berupa bilangan bulat positif.")

        if not isinstance(is_active, bool):
            raise ValueError("Status pasangan harus berupa True atau False.")

        with self.get_connection() as connection:
            cursor = connection.execute(
                """
                UPDATE barcode_pairs
                SET is_active = ?
                WHERE id = ?
                """,
                (int(is_active), pair_id),
            )

            if cursor.rowcount == 0:
                raise ValueError("Pasangan barcode tidak ditemukan.")


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

    
    def get_recent_inspections(self, limit=10):
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError("Limit harus berupa bilangan bulat positif.")

        with self.get_connection() as connection:
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
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return rows

