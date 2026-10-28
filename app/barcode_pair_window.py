
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class BarcodePairWindow(QMainWindow):
    def __init__(self, database):
        super().__init__()

        self.database = database
        self.editing_pair_id = None

        self.setWindowTitle("Master Data Pasangan Barcode")
        self.resize(1100, 650)

        # Input key barcode
        self.box_key_input = QLineEdit()
        self.box_key_input.setPlaceholderText("Contoh: 7036")

        self.unit_key_input = QLineEdit()
        self.unit_key_input.setPlaceholderText("Contoh: 7830H")

        # Input konfigurasi ekstraksi
        self.box_start_input = QSpinBox()
        self.box_start_input.setRange(1, 10000)
        self.box_start_input.setValue(1)

        self.box_length_input = QSpinBox()
        self.box_length_input.setRange(1, 10000)
        self.box_length_input.setValue(4)

        self.unit_start_input = QSpinBox()
        self.unit_start_input.setRange(1, 10000)
        self.unit_start_input.setValue(1)

        self.unit_length_input = QSpinBox()
        self.unit_length_input.setRange(1, 10000)
        self.unit_length_input.setValue(5)

        form_layout = QFormLayout()
        form_layout.addRow("Box Key:", self.box_key_input)
        form_layout.addRow("Unit Key:", self.unit_key_input)
        form_layout.addRow(
            "Box posisi mulai:",
            self.box_start_input,
        )
        form_layout.addRow("Box length:", self.box_length_input)
        form_layout.addRow(
            "Unit posisi mulai:",
            self.unit_start_input,
        )
        form_layout.addRow(
            "Unit length:",
            self.unit_length_input,
        )

        self.add_button = QPushButton("Tambah Pasangan Barcode")
        self.add_button.clicked.connect(self.add_barcode_pair)
        form_layout.addRow(self.add_button)

        self.edit_button = QPushButton("Muat Pasangan untuk Edit")
        self.edit_button.clicked.connect(self.load_pair_for_edit)
        form_layout.addRow(self.edit_button)

        self.cancel_edit_button = QPushButton("Batal Edit")
        self.cancel_edit_button.clicked.connect(self.reset_form)
        self.cancel_edit_button.setEnabled(False)
        form_layout.addRow(self.cancel_edit_button)

        # Tabel pasangan barcode
        self.pair_table = QTableWidget()
        self.pair_table.setColumnCount(9)
        self.pair_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Box Key",
                "Unit Key",
                "Box Posisi",
                "Box Length",
                "Unit Posisi",
                "Unit Length",
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
        self.pair_table.horizontalHeader().setStretchLastSection(True)

        self.toggle_button = QPushButton(
            "Aktifkan / Nonaktifkan Pasangan"
        )
        self.toggle_button.clicked.connect(
            self.toggle_barcode_pair_status
        )

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(QLabel("Daftar Pasangan Barcode"))
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
                pair["box_start_position"],
                pair["box_length"],
                pair["unit_start_position"],
                pair["unit_length"],
                "Aktif" if pair["is_active"] else "Nonaktif",
                pair["created_at"],
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column_index == 7:
                    color = (
                        Qt.GlobalColor.darkGreen
                        if value == "Aktif"
                        else Qt.GlobalColor.red
                    )
                    item.setForeground(color)

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
            if self.editing_pair_id is None:
                self.database.add_barcode_pair(
                    box_key=box_key,
                    unit_key=unit_key,
                    box_start_position=self.box_start_input.value(),
                    box_length=self.box_length_input.value(),
                    unit_start_position=self.unit_start_input.value(),
                    unit_length=self.unit_length_input.value(),
                )
            else:
                self.database.update_barcode_pair(
                    pair_id=self.editing_pair_id,
                    box_key=box_key,
                    unit_key=unit_key,
                    box_start_position=self.box_start_input.value(),
                    box_length=self.box_length_input.value(),
                    unit_start_position=self.unit_start_input.value(),
                    unit_length=self.unit_length_input.value(),
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

        self.reset_form()
        self.refresh_barcode_pairs()

        QMessageBox.information(
            self,
            "Berhasil",
            "Pasangan barcode berhasil ditambahkan.",
        )

    def load_pair_for_edit(self):
        selected_row = self.pair_table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Belum Ada Pilihan",
                "Pilih pasangan barcode pada tabel terlebih dahulu.",
            )
            return

        pair_id = int(self.pair_table.item(selected_row, 0).text())

        pair = next(
            (
                item
                for item in self.database.get_all_barcode_pairs()
                if item["id"] == pair_id
            ),
            None,
        )

        if pair is None:
            QMessageBox.warning(
                self,
                "Data Tidak Ditemukan",
                "Pasangan barcode tidak ditemukan.",
            )
            self.refresh_barcode_pairs()
            return

        self.editing_pair_id = pair_id

        self.box_key_input.setText(pair["box_key"])
        self.unit_key_input.setText(pair["unit_key"])
        self.box_start_input.setValue(pair["box_start_position"])
        self.box_length_input.setValue(pair["box_length"])
        self.unit_start_input.setValue(pair["unit_start_position"])
        self.unit_length_input.setValue(pair["unit_length"])

        self.add_button.setText("Simpan Perubahan Pasangan")
        self.cancel_edit_button.setEnabled(True)

    def reset_form(self):
        self.editing_pair_id = None

        self.box_key_input.clear()
        self.unit_key_input.clear()
        self.box_start_input.setValue(1)
        self.box_length_input.setValue(4)
        self.unit_start_input.setValue(1)
        self.unit_length_input.setValue(5)

        self.add_button.setText("Tambah Pasangan Barcode")
        self.cancel_edit_button.setEnabled(False)

    def toggle_barcode_pair_status(self):
        selected_row = self.pair_table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Belum Ada Pilihan",
                "Pilih pasangan barcode pada tabel terlebih dahulu.",
            )
            return

        pair_id = int(self.pair_table.item(selected_row, 0).text())
        box_key = self.pair_table.item(selected_row, 1).text()
        unit_key = self.pair_table.item(selected_row, 2).text()
        status_item = self.pair_table.item(selected_row, 7)

        currently_active = status_item.text() == "Aktif"
        new_status = not currently_active

        action_text = (
            "mengaktifkan" if new_status else "menonaktifkan"
        )

        confirmation = QMessageBox.question(
            self,
            "Konfirmasi Perubahan Status",
            "Apakah Anda yakin ingin {} pasangan Box {} dan Unit {}?"
            .format(action_text, box_key, unit_key),
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
