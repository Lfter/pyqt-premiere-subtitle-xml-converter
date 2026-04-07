import sys
from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def _icon_candidates() -> list[Path]:
    repo_root = Path(__file__).resolve().parent
    bundle_root = Path(getattr(sys, "_MEIPASS", repo_root))
    packaging_assets_dir = Path("packaging") / "macos" / "assets"
    legacy_assets_dir = Path("assets") / "macos"
    return [
        bundle_root / packaging_assets_dir / "srt_to_xml.icns",
        bundle_root / packaging_assets_dir / "srt_to_xml.png",
        repo_root / packaging_assets_dir / "srt_to_xml.icns",
        repo_root / packaging_assets_dir / "srt_to_xml.png",
        bundle_root / legacy_assets_dir / "srt_to_xml.icns",
        bundle_root / legacy_assets_dir / "srt_to_xml.png",
        repo_root / legacy_assets_dir / "srt_to_xml.icns",
        repo_root / legacy_assets_dir / "srt_to_xml.png",
    ]


def main() -> None:
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
