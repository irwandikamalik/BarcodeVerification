
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class BarcodePairWindow(QMainWindow):
    def __init__(self, database):
        super().__init__()

        self.database = database

        self.setWindowTitle("Master Data Pasangan Barcode")
        self.resize(800, 550)

        # Form input pasangan barcode
        self.box_key_input = QLineEdit()
        self.box_key_input.setPlaceholderText(
            "Contoh: 7036"
        )

        self.unit_key_input = QLineEdit()
        self.unit_key_input.setPlaceholderText(
            "Contoh: 7830H"
        )

        form_layout = QFormLayout()
        form_layout.addRow(
            "Box Barcode Key:",
            self.box_key_input,
        )
        form_layout.addRow(
            "Unit Barcode Key:",
            self.unit_key_input,
        )

        self.add_button = QPushButton(
            "Tambah Pasangan Barcode"
        )
        self.add_button.clicked.connect(
            self.add_barcode_pair
        )

        form_layout.addRow(self.add_button)

        # Tabel pasangan barcode
        self.pair_table = QTableWidget()
        self.pair_table.setColumnCount(5)
        self.pair_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Box Key",
                "Unit Key",
                "Status",
                "Terdaftar",
            ]
        )

        self.pair_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.pair_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.pair_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.pair_table.verticalHeader().setVisible(False)

        self.pair_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.pair_table.horizontalHeader().setStretchLastSection(
            True
        )

        # Tombol perubahan status pasangan
        self.toggle_button = QPushButton(
            "Aktifkan / Nonaktifkan Pasangan"
        )
        self.toggle_button.clicked.connect(
            self.toggle_barcode_pair_status
        )

        # Layout utama
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(
            QLabel("Daftar Pasangan Barcode")
        )
        layout.addWidget(self.pair_table, 1)
        layout.addWidget(self.toggle_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.refresh_barcode_pairs()

    def refresh_barcode_pairs(self):
        pairs = self.database.get_all_barcode_pairs()

        self.pair_table.setRowCount(len(pairs))

        for row_index, pair in enumerate(pairs):
            values = [
                pair["id"],
                pair["box_key"],
                pair["unit_key"],
                "Aktif" if pair["is_active"] else "Nonaktif",
                pair["created_at"],
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column_index == 3:
                    if value == "Aktif":
                        item.setForeground(
                            Qt.GlobalColor.darkGreen
                        )
                    else:
                        item.setForeground(
                            Qt.GlobalColor.red
                        )

                self.pair_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def add_barcode_pair(self):
        box_key = self.box_key_input.text().strip()
        unit_key = self.unit_key_input.text().strip()

        if not box_key or not unit_key:
            QMessageBox.warning(
                self,
                "Data Belum Lengkap",
                "Box Key dan Unit Key wajib diisi.",
            )
            return

        try:
            self.database.add_barcode_pair(
                box_key,
                unit_key,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Data Tidak Valid",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Gagal Menambahkan Pasangan",
                "Terjadi kesalahan:\n{}".format(error),
            )
            return

        self.box_key_input.clear()
        self.unit_key_input.clear()
        self.refresh_barcode_pairs()

        QMessageBox.information(
            self,
            "Berhasil",
            "Pasangan barcode berhasil ditambahkan.",
        )

    def toggle_barcode_pair_status(self):
        selected_row = self.pair_table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Belum Ada Pilihan",
                "Pilih pasangan barcode pada tabel terlebih dahulu.",
            )
            return

        id_item = self.pair_table.item(selected_row, 0)
        box_item = self.pair_table.item(selected_row, 1)
        unit_item = self.pair_table.item(selected_row, 2)
        status_item = self.pair_table.item(selected_row, 3)

        pair_id = int(id_item.text())
        box_key = box_item.text()
        unit_key = unit_item.text()

        currently_active = status_item.text() == "Aktif"
        new_status = not currently_active

        action_text = (
            "mengaktifkan" if new_status else "menonaktifkan"
        )

        confirmation = QMessageBox.question(
            self,
            "Konfirmasi Perubahan Status",
            (
                "Apakah Anda yakin ingin {} pasangan "
                "Box {} dan Unit {}?"
            ).format(action_text, box_key, unit_key),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            self.database.set_barcode_pair_active(
                pair_id,
                new_status,
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Gagal Mengubah Status",
                str(error),
            )
            return

        self.refresh_barcode_pairs()
