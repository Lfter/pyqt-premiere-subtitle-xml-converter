from __future__ import annotations

from pathlib import Path
from typing import Callable

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QMouseEvent
from PyQt5.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout, QWidget


class FileDropZone(QFrame):
    file_selected = pyqtSignal(str)

    def __init__(
        self,
        title: str,
        extensions: tuple[str, ...],
        dialog_filter: str,
        directory_provider: Callable[[], str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.title = title
        self.extensions = tuple(extension.lower() for extension in extensions)
        self.dialog_filter = dialog_filter
        self.directory_provider = directory_provider
        self.file_path = ""
        self._build_ui()

    def _build_ui(self) -> None:
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(320, 220)
        self._apply_style(active=False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #324255;")

        self.hint_label = QLabel("拖拽到此处\n或点击选择文件")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet("font-size: 18px; color: #5e6f82; line-height: 1.5;")

        self.path_label = QLabel("尚未选择文件")
        self.path_label.setAlignment(Qt.AlignCenter)
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("font-size: 13px; color: #738398;")

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.hint_label)
        layout.addWidget(self.path_label)
        layout.addStretch()

    def set_file(self, path: str) -> bool:
        if not self._matches_extension(path):
            return False
        self.file_path = path
        self.path_label.setText(Path(path).name)
        self.hint_label.setText("文件已载入")
        self._apply_style(active=True)
        self.file_selected.emit(path)
        return True

    def clear(self) -> None:
        self.file_path = ""
        self.path_label.setText("尚未选择文件")
        self.hint_label.setText("拖拽到此处\n或点击选择文件")
        self._apply_style(active=False)

    def is_valid(self) -> bool:
        return bool(self.file_path and self._matches_extension(self.file_path))

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            self._open_file_dialog()
        super().mousePressEvent(a0)

    def dragEnterEvent(self, a0: QDragEnterEvent) -> None:
        urls = a0.mimeData().urls()
        if any(url.isLocalFile() and self._matches_extension(url.toLocalFile()) for url in urls):
            self._apply_style(active=True, drag_over=True)
            a0.acceptProposedAction()
            return
        a0.ignore()

    def dragLeaveEvent(self, a0: QDragLeaveEvent) -> None:
        self._apply_style(active=self.is_valid())
        super().dragLeaveEvent(a0)

    def dropEvent(self, a0: QDropEvent) -> None:
        for url in a0.mimeData().urls():
            if not url.isLocalFile():
                continue
            if self.set_file(url.toLocalFile()):
                a0.acceptProposedAction()
                return
        a0.ignore()

    def _open_file_dialog(self) -> None:
        initial_path = ""
        if callable(self.directory_provider):
            initial_path = self.directory_provider() or ""
        if not initial_path and self.file_path:
            initial_path = self.file_path
        path, _ = QFileDialog.getOpenFileName(self, f"选择{self.title}", initial_path, self.dialog_filter)
        if path:
            self.set_file(path)

    def _matches_extension(self, path: str) -> bool:
        suffix = Path(path).suffix.lower()
        return suffix in self.extensions

    def _apply_style(self, active: bool, drag_over: bool = False) -> None:
        border_color = "#2f80ed" if active else "#8ca0b5"
        background = "#eef6ff" if active else "#f8fbfd"
        if drag_over:
            background = "#e3f0ff"
        self.setStyleSheet(
            f"""
            QFrame {{
                border: 3px dashed {border_color};
                border-radius: 24px;
                background-color: {background};
            }}
            """
        )
