import sys
from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def _icon_candidates() -> list[Path]:
    repo_root = Path(__file__).resolve().parent
    bundle_root = Path(getattr(sys, "_MEIPASS", repo_root))
    return [
        bundle_root / "assets" / "macos" / "srt_to_xml.icns",
        bundle_root / "assets" / "macos" / "srt_to_xml.png",
        repo_root / "assets" / "macos" / "srt_to_xml.icns",
        repo_root / "assets" / "macos" / "srt_to_xml.png",
    ]


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("srt_to_xml")
    app.setOrganizationName("ltzz")
    for icon_path in _icon_candidates():
        if icon_path.is_file():
            app.setWindowIcon(QIcon(str(icon_path)))
            break
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
