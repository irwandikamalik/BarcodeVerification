
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.barcode_service import BarcodeService
from app.database import DatabaseManager
from PySide6.QtGui import QAction


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Barcode Verification System")
        self.resize(900, 600)

        # Inisialisasi database dan layanan barcode.
        self.database = DatabaseManager()
        self.barcode_service = BarcodeService(self.database)

        # Identitas operator yang sedang login.
        self.current_operator = None

        # Status operator.
        self.operator_status = QLabel("Operator belum login")
        self.operator_status.setStyleSheet(
            "font-size: 14px; color: #666666;"
        )

        # Input operator.
        self.operator_input = QLineEdit()
        self.operator_input.setPlaceholderText(
            "Masukkan kode operator"
        )
        self.operator_input.returnPressed.connect(
            self.validate_operator
        )

        # Input barcode Box.
        self.box_input = QLineEdit()
        self.box_input.setPlaceholderText("Scan Barcode Box")
        self.box_input.returnPressed.connect(
            self.focus_unit_input
        )
        self.box_input.setEnabled(False)

        # Input barcode Unit.
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("Scan Barcode Unit")
        self.unit_input.returnPressed.connect(
            self.focus_start_button
        )
        self.unit_input.setEnabled(False)

        # Form input.
        form_layout = QFormLayout()
        form_layout.addRow("Operator Code:", self.operator_input)
        form_layout.addRow("Barcode Box:", self.box_input)
        form_layout.addRow("Barcode Unit:", self.unit_input)

        input_group = QGroupBox("Inspection Input")
        input_group.setLayout(form_layout)

        # Status inspeksi.
        self.result_label = QLabel("Belum ada inspeksi")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setMinimumHeight(100)
        self.set_result_style("neutral")

        # Tombol START.
        self.start_button = QPushButton("START INSPECTION")
        self.start_button.setMinimumHeight(45)
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_inspection)

        # Layout utama.
        layout = QVBoxLayout()
        layout.addWidget(self.operator_status)
        layout.addWidget(input_group)
        layout.addWidget(self.result_label)
        layout.addStretch()
        layout.addWidget(self.start_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Menubar
        menu_bar = self.menuBar()

        operator_menu = menu_bar.addMenu("Operator")

        self.logout_action = QAction("Logout Operator", self)
        self.logout_action.setEnabled(False)
        self.logout_action.triggered.connect(self.logout_operator)

        operator_menu.addAction(self.logout_action)

    def set_result_style(self, status):
        styles = {
            "neutral": """
                font-size: 24px;
                font-weight: bold;
                color: #555555;
                border: 1px solid #999999;
                border-radius: 8px;
            """,
            "ok": """
                font-size: 28px;
                font-weight: bold;
                color: #176B35;
                border: 2px solid #176B35;
                border-radius: 8px;
            """,
            "ng": """
                font-size: 28px;
                font-weight: bold;
                color: #B42318;
                border: 2px solid #B42318;
                border-radius: 8px;
            """,
        }

        self.result_label.setStyleSheet(styles[status])

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

        operator = self.barcode_service.validate_operator(
            operator_code
        )

        if operator is None:
            self.operator_status.setText(
                "Operator tidak terdaftar atau tidak aktif."
            )
            self.operator_status.setStyleSheet(
                "font-size: 14px; color: #B42318;"
            )
            self.operator_input.clear()
            self.operator_input.setFocus()
            return

        self.current_operator = operator

        self.operator_status.setText(
            "Operator aktif: {} ({})".format(
                operator["operator_name"],
                operator["operator_code"],
            )
        )
        self.operator_status.setStyleSheet(
            "font-size: 14px; color: #176B35;"
        )

        self.operator_input.setEnabled(False)
        self.box_input.setEnabled(True)
        self.unit_input.setEnabled(True)
        self.start_button.setEnabled(False)
        self.logout_action.setEnabled(True)

        self.box_input.setFocus()

    def logout_operator(self):
        if self.current_operator is None:
            return

        self.current_operator = None

        self.operator_input.clear()
        self.operator_input.setEnabled(True)

        self.box_input.clear()
        self.box_input.setEnabled(False)

        self.unit_input.clear()
        self.unit_input.setEnabled(False)

        self.start_button.setEnabled(False)

        self.operator_status.setText("Operator belum login")
        self.operator_status.setStyleSheet(
            "font-size: 14px; color: #666666;"
        )

        self.result_label.setText("Belum ada inspeksi")
        self.set_result_style("neutral")

        self.logout_action.setEnabled(False)
        self.operator_input.setFocus()

    def focus_unit_input(self):
        box_barcode = self.box_input.text().strip()

        if not box_barcode:
            self.result_label.setText(
                "Barcode Box belum diisi!"
            )
            self.set_result_style("ng")
            self.box_input.setFocus()
            return

        self.result_label.setText(
            "Barcode Box diterima. Scan Barcode Unit."
        )
        self.set_result_style("neutral")

        self.start_button.setEnabled(False)
        QTimer.singleShot(0, self.unit_input.setFocus)

    def focus_start_button(self):
        unit_barcode = self.unit_input.text().strip()

        if not unit_barcode:
            self.result_label.setText(
                "Barcode Unit belum diisi!"
            )
            self.set_result_style("ng")
            QTimer.singleShot(0, self.unit_input.setFocus)
            return

        self.result_label.setText(
            "Barcode Unit diterima. Memulai inspeksi..."
        )

        # Scanner biasanya mengirim Enter di akhir barcode.
        # Jalankan inspeksi setelah event Enter selesai.
        QTimer.singleShot(0, self.start_inspection)

    def start_inspection(self):
        if self.current_operator is None:
            QMessageBox.warning(
                self,
                "Operator Required",
                "Validasi operator terlebih dahulu.",
            )
            self.operator_input.setEnabled(True)
            self.operator_input.setFocus()
            return

        box_barcode = self.box_input.text().strip()
        unit_barcode = self.unit_input.text().strip()

        if not box_barcode or not unit_barcode:
            QMessageBox.warning(
                self,
                "Barcode Required",
                "Barcode Box dan Barcode Unit wajib diisi.",
            )
            if not box_barcode:
                self.box_input.setFocus()
            else:
                self.unit_input.setFocus()
            return

        self.start_button.setEnabled(False)

        try:
            result = self.barcode_service.inspect(
                operator_code=self.current_operator["operator_code"],
                operator_name=self.current_operator["operator_name"],
                box_barcode=box_barcode,
                unit_barcode=unit_barcode,
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Inspection Error",
                "Pemeriksaan gagal diproses.\n\n{}".format(error),
            )
            self.start_button.setEnabled(True)
            return

        if result.judgment == "OK":
            self.result_label.setText(
                "OK\nBox: {} | Unit: {}".format(
                    result.box_key,
                    result.unit_key,
                )
            )
            self.set_result_style("ok")
        else:
            self.result_label.setText(
                "NG\n{}".format(result.reason or "Pemeriksaan gagal.")
            )
            self.set_result_style("ng")

        # Operator tetap login untuk inspeksi berikutnya.
        self.box_input.clear()
        self.unit_input.clear()
        self.start_button.setEnabled(False)

        # Fokus kembali ke Barcode Box untuk scan berikutnya.
        QTimer.singleShot(0, self.box_input.setFocus)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
