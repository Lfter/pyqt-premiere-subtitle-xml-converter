from pathlib import Path
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    icon_path = Path(__file__).resolve().parent / "resources" / "macos" / "app_icon_master_1024.png"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
