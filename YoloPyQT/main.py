# main.py
import sys
from PySide6.QtWidgets import QApplication
from mainwindow import MainWindow  # mainwindow.py에 MainWindow 클래스 있어야 함

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
