
import sys

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Barcode Verification System")
        self.resize(900, 600)

        # Judul aplikasi
        self.title_label = QLabel("BARCODE VERIFICATION SYSTEM")
        self.title_label.setStyleSheet(
            """
            font-size: 24px;
            font-weight: bold;
            """
        )

        # Informasi status
        self.status_label = QLabel(
            "Status: Menunggu operator"
        )
        self.status_label.setStyleSheet(
            "font-size: 16px; color: #555555;"
        )

        # Tombol awal
        self.start_button = QPushButton("START INSPECTION")
        self.start_button.setMinimumHeight(45)
        self.start_button.clicked.connect(
            self.start_inspection
        )

        # Layout utama
        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.start_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

    def start_inspection(self):
        self.status_label.setText(
            "Status: Tombol START berhasil ditekan"
        )


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
