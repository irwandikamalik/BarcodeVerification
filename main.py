
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Barcode Verification System")
        self.resize(900, 600)

        # Status operator
        self.operator_status = QLabel("Operator belum login")
        self.operator_status.setStyleSheet(
            "font-size: 14px; color: #666666;"
        )

        # Input operator
        self.operator_input = QLineEdit()
        self.operator_input.setPlaceholderText(
            "Masukkan kode operator"
        )
        self.operator_input.returnPressed.connect(
            self.validate_operator
        )

        # Input barcode box
        self.box_input = QLineEdit()
        self.box_input.setPlaceholderText(
            "Scan Barcode Box"
        )
        self.box_input.returnPressed.connect(
            self.focus_unit_input
        )
        self.box_input.setEnabled(False)

        # Input barcode unit
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText(
            "Scan Barcode Unit"
        )
        self.unit_input.returnPressed.connect(
            self.focus_start_button
        )
        self.unit_input.setEnabled(False)

        # Form input
        form_layout = QFormLayout()
        form_layout.addRow("Operator Code:", self.operator_input)
        form_layout.addRow("Barcode Box:", self.box_input)
        form_layout.addRow("Barcode Unit:", self.unit_input)

        input_group = QGroupBox("Inspection Input")
        input_group.setLayout(form_layout)

        # Status inspeksi
        self.result_label = QLabel("Belum ada inspeksi")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setMinimumHeight(100)
        self.result_label.setStyleSheet(
            """
            font-size: 24px;
            font-weight: bold;
            border: 1px solid #999999;
            border-radius: 8px;
            """
        )

        # Tombol START
        self.start_button = QPushButton("START INSPECTION")
        self.start_button.setMinimumHeight(45)
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(
            self.start_inspection
        )

        # Layout utama
        layout = QVBoxLayout()
        layout.addWidget(self.operator_status)
        layout.addWidget(input_group)
        layout.addWidget(self.result_label)
        layout.addStretch()
        layout.addWidget(self.start_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def validate_operator(self):
        operator_code = self.operator_input.text().strip()

        if not operator_code:
            QMessageBox.warning(
                self,
                "Operator Required",
                "Masukkan kode operator terlebih dahulu.",
            )
            self.operator_input.setFocus()
            return

        # Validasi sementara, belum menggunakan database.
        self.operator_status.setText(
            f"Operator aktif: {operator_code}"
        )
        self.operator_status.setStyleSheet(
            "font-size: 14px; color: green;"
        )

        self.operator_input.setEnabled(False)
        self.box_input.setEnabled(True)
        self.unit_input.setEnabled(True)
        self.box_input.setFocus()



    def focus_unit_input(self):
        box_barcode = self.box_input.text().strip()

        if not box_barcode:
            self.result_label.setText(
                "Barcode Box belum diisi!"
            )
            self.box_input.setFocus()
            return

        self.result_label.setText(
            "Barcode Box diterima. Scan Barcode Unit."
        )

        # Pindahkan fokus setelah event Enter selesai diproses.
        QTimer.singleShot(0, self.unit_input.setFocus)


    def focus_start_button(self):
        unit_barcode = self.unit_input.text().strip()

        if not unit_barcode:
            self.result_label.setText(
                "Barcode Unit belum diisi!"
            )
            QTimer.singleShot(0, self.unit_input.setFocus)
            return

        self.result_label.setText(
            "Barcode Unit diterima. Memulai inspeksi..."
        )

        self.start_button.setEnabled(True)

        # Tunggu event Enter selesai, lalu jalankan inspeksi.
        QTimer.singleShot(0, self.start_inspection)


    def start_inspection(self):
        box_barcode = self.box_input.text().strip()
        unit_barcode = self.unit_input.text().strip()

        if not box_barcode or not unit_barcode:
            QMessageBox.warning(
                self,
                "Barcode Required",
                "Barcode Box dan Barcode Unit wajib diisi.",
            )
            return

        # Hasil sementara. Pemeriksaan pasangan barcode
        # yang sebenarnya akan dibuat pada tahap berikutnya.
        self.result_label.setText("INSPECTION RECORDED")
        self.result_label.setStyleSheet(
            """
            font-size: 24px;
            font-weight: bold;
            color: #176B35;
            border: 2px solid #176B35;
            border-radius: 8px;
            """
        )

        self.box_input.clear()
        self.unit_input.clear()
        self.box_input.setFocus()


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
