from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from converter import ConversionError, ConversionService

from .file_drop_zone import FileDropZone


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.conversion_service: ConversionService = ConversionService()
        self.settings: QSettings = QSettings("Codex", "PremiereSubtitleXmlConverter")
        self._build_ui()
        self._restore_recent_files()
        if not self.log_view.toPlainText().strip():
            self._append_log("等待载入 XML 模板和 SRT 字幕文件。")

    def _build_ui(self) -> None:
        self.setWindowTitle("Premiere 字幕 XML 转换器")
        self.setFixedSize(920, 680)
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #edf2f7;
            }
            QWidget {
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            }
            QPushButton {
                background-color: #1459c7;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 22px;
                font-weight: 700;
                padding: 16px 28px;
            }
            QPushButton:hover:enabled {
                background-color: #0f4bac;
            }
            QPushButton:disabled {
                background-color: #a7bbdb;
                color: #edf3fb;
            }
            """
        )

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(50, 40, 50, 40)
        outer_layout.setSpacing(24)

        top_row = QHBoxLayout()
        top_row.setSpacing(40)
        top_row.addStretch()

        self.xml_zone = FileDropZone(
            "XML 样式文件",
            (".xml",),
            "XML Files (*.xml)",
            directory_provider=lambda: self._recent_path_for("recent/template_path"),
        )
        self.srt_zone = FileDropZone(
            "SRT 字幕文件",
            (".srt",),
            "SRT Files (*.srt)",
            directory_provider=lambda: self._recent_path_for("recent/srt_path"),
        )
        self.xml_zone.file_selected.connect(self._on_xml_selected)
        self.srt_zone.file_selected.connect(self._on_srt_selected)

        top_row.addWidget(self.xml_zone)
        top_row.addWidget(self.srt_zone)
        top_row.addStretch()

        outer_layout.addLayout(top_row)

        self.log_title = QLabel("预览与日志")
        self.log_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.log_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #324255;")
        outer_layout.addWidget(self.log_title)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(200)
        self.log_view.setStyleSheet(
            """
            QPlainTextEdit {
                border: 2px solid #d5deea;
                border-radius: 20px;
                background-color: #fbfdff;
                color: #45576d;
                padding: 16px;
                font-size: 14px;
            }
            """
        )
        outer_layout.addWidget(self.log_view)
        outer_layout.addStretch()

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.convert_button = QPushButton("开始转换")
        self.convert_button.setFixedSize(240, 70)
        self.convert_button.setEnabled(False)
        self.convert_button.clicked.connect(self._select_output_and_convert)
        button_row.addWidget(self.convert_button)

        button_row.addStretch()
        outer_layout.addLayout(button_row)

    def _refresh_convert_button(self) -> None:
        self.convert_button.setEnabled(self.xml_zone.is_valid() and self.srt_zone.is_valid())

    def _on_xml_selected(self, path: str) -> None:
        self.settings.setValue("recent/template_path", path)
        self._append_log(f"已载入 XML 模板：{path}")
        self._refresh_convert_button()

    def _on_srt_selected(self, path: str) -> None:
        self.settings.setValue("recent/srt_path", path)
        self._append_log(f"已载入 SRT 字幕：{path}")
        self._refresh_convert_button()

    def _select_output_and_convert(self) -> None:
        if not (self.xml_zone.is_valid() and self.srt_zone.is_valid()):
            QMessageBox.warning(self, "提示", "请先载入 XML 模板文件和 SRT 字幕文件。")
            return

        srt_path = Path(self.srt_zone.file_path)
        output_directory = self._recent_output_dir() or str(srt_path.parent)
        default_output = Path(output_directory) / f"{srt_path.stem}_premiere.xml"
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择转换后的 XML 保存位置",
            str(default_output),
            "XML Files (*.xml)",
        )
        if not output_path:
            return
        if not output_path.lower().endswith(".xml"):
            output_path += ".xml"

        output_file = Path(output_path)
        if output_file.exists():
            reply = QMessageBox.question(
                self,
                "覆盖确认",
                f"文件已存在，是否覆盖？\n{output_file}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        self.convert_button.setEnabled(False)
        self._append_log(
            f"开始转换：\nXML 模板：{self.xml_zone.file_path}\nSRT 文件：{self.srt_zone.file_path}\n输出路径：{output_path}"
        )
        try:
            result = self.conversion_service.convert(
                self.xml_zone.file_path,
                self.srt_zone.file_path,
                output_path,
            )
        except ConversionError as exc:
            QMessageBox.critical(self, "转换失败", str(exc))
            self._append_log(f"转换失败：{exc}")
            self._refresh_convert_button()
            return
        except Exception as exc:  # pragma: no cover
            QMessageBox.critical(self, "转换失败", f"发生了未预期的错误：{exc}")
            self._append_log(f"转换失败：发生未预期错误：{exc}")
            self._refresh_convert_button()
            return

        self.settings.setValue("recent/output_dir", str(output_file.parent))
        self._refresh_convert_button()
        preview_block = "\n".join(
            f"{index}. {line.replace(chr(10), ' / ')}"
            for index, line in enumerate(result.preview_lines, start=1)
        )
        if preview_block:
            self._append_log(
                f"转换完成：已生成 {result.clip_count} 条字幕。\n输出文件：{result.output_path}\n预览：\n{preview_block}"
            )
        else:
            self._append_log(f"转换完成：已生成 {result.clip_count} 条字幕。\n输出文件：{result.output_path}")
        QMessageBox.information(
            self,
            "转换完成",
            f"已生成 {result.clip_count} 条字幕。\n输出文件：\n{result.output_path}",
        )

    def _restore_recent_files(self) -> None:
        restored_any = False
        template_path = self.settings.value("recent/template_path", "", type=str)
        srt_path = self.settings.value("recent/srt_path", "", type=str)

        if template_path and Path(template_path).is_file():
            if self.xml_zone.set_file(template_path):
                restored_any = True
        if srt_path and Path(srt_path).is_file():
            if self.srt_zone.set_file(srt_path):
                restored_any = True

        if restored_any:
            self._append_log("已恢复最近一次使用的文件路径。")
        self._refresh_convert_button()

    def _recent_output_dir(self) -> str:
        recent_dir = self.settings.value("recent/output_dir", "", type=str)
        if recent_dir and Path(recent_dir).is_dir():
            return recent_dir
        return ""

    def _recent_path_for(self, key: str) -> str:
        value = self.settings.value(key, "", type=str)
        if value and Path(value).exists():
            return value
        return self._recent_output_dir()

    def _append_log(self, message: str) -> None:
        current_text = self.log_view.toPlainText().strip()
        combined = f"{current_text}\n\n{message}".strip() if current_text else message
        self.log_view.setPlainText(combined)
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
