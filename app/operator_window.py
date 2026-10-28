
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
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


class OperatorWindow(QMainWindow):
    def __init__(self, database):
        super().__init__()

        self.database = database

        self.setWindowTitle("Master Data Operator")
        self.resize(700, 500)

        # Form input operator
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Contoh: OP002")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nama operator")

        form_layout = QFormLayout()
        form_layout.addRow("Kode Operator:", self.code_input)
        form_layout.addRow("Nama Operator:", self.name_input)

        self.add_button = QPushButton("Tambah Operator")
        self.add_button.clicked.connect(self.add_operator)

        form_layout.addRow(self.add_button)

        # Tabel daftar operator
        self.operator_table = QTableWidget()
        self.operator_table.setColumnCount(4)
        self.operator_table.setHorizontalHeaderLabels(
            ["Kode", "Nama", "Status", "Terdaftar"]
        )
        self.operator_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.operator_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.operator_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.operator_table.verticalHeader().setVisible(False)
        self.operator_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.operator_table.horizontalHeader().setStretchLastSection(True)

        # Tombol perubahan status
        self.toggle_button = QPushButton(
            "Aktifkan / Nonaktifkan Operator"
        )
        self.toggle_button.clicked.connect(self.toggle_operator_status)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(QLabel("Daftar Operator"))
        layout.addWidget(self.operator_table, 1)
        layout.addWidget(self.toggle_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.refresh_operators()

    def refresh_operators(self):
        operators = self.database.get_all_operators()

        self.operator_table.setRowCount(len(operators))

        for row_index, operator in enumerate(operators):
            values = [
                operator["operator_code"],
                operator["operator_name"],
                "Aktif" if operator["is_active"] else "Nonaktif",
                operator["created_at"],
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column_index == 2:
                    if value == "Aktif":
                        item.setForeground(Qt.GlobalColor.darkGreen)
                    else:
                        item.setForeground(Qt.GlobalColor.red)

                self.operator_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def add_operator(self):
        operator_code = self.code_input.text().strip()
        operator_name = self.name_input.text().strip()

        if not operator_code or not operator_name:
            QMessageBox.warning(
                self,
                "Data Belum Lengkap",
                "Kode dan nama operator wajib diisi.",
            )
            return

        try:
            self.database.add_operator(
                operator_code,
                operator_name,
            )
        except ValueError as error:
            QMessageBox.warning(self, "Data Tidak Valid", str(error))
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Gagal Menambahkan Operator",
                "Terjadi kesalahan:\n{}".format(error),
            )
            return

        self.code_input.clear()
        self.name_input.clear()
        self.refresh_operators()

        QMessageBox.information(
            self,
            "Berhasil",
            "Operator berhasil ditambahkan.",
        )

    def toggle_operator_status(self):
        selected_row = self.operator_table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Belum Ada Pilihan",
                "Pilih operator pada tabel terlebih dahulu.",
            )
            return

        code_item = self.operator_table.item(selected_row, 0)
        status_item = self.operator_table.item(selected_row, 2)

        operator_code = code_item.text()
        currently_active = status_item.text() == "Aktif"
        new_status = not currently_active

        action_text = "mengaktifkan" if new_status else "menonaktifkan"

        confirmation = QMessageBox.question(
            self,
            "Konfirmasi Perubahan Status",
            "Apakah Anda yakin ingin {} operator {}?".format(
                action_text,
                operator_code,
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            self.database.set_operator_active(
                operator_code,
                new_status,
            )
        except (ValueError, Exception) as error:
            QMessageBox.critical(
                self,
                "Gagal Mengubah Status",
                str(error),
            )
            return

        self.refresh_operators()
