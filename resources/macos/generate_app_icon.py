from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)


BASE_DIR = Path(__file__).resolve().parent
ICONSET_DIR = BASE_DIR / "AppIcon.iconset"
MASTER_PATH = BASE_DIR / "app_icon_master_1024.png"
OUTPUT_SPECS = (
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
)


def scaled(value: float, size: int) -> float:
    return value * size / 1024.0


def rounded_bar(
    painter: QPainter,
    size: int,
    x: float,
    y: float,
    width: float,
    height: float,
    color: str,
) -> None:
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))
    painter.drawRoundedRect(
        QRectF(
            scaled(x, size),
            scaled(y, size),
            scaled(width, size),
            scaled(height, size),
        ),
        scaled(height / 2, size),
        scaled(height / 2, size),
    )


def draw_chevron(
    painter: QPainter,
    size: int,
    points: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    color: str,
) -> None:
    pen = QPen(QColor(color), scaled(44, size), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    path = QPainterPath()
    start_x, start_y = points[0]
    path.moveTo(scaled(start_x, size), scaled(start_y, size))
    for point_x, point_y in points[1:]:
        path.lineTo(scaled(point_x, size), scaled(point_y, size))
    painter.drawPath(path)


def draw_icon(size: int, output_path: Path) -> None:
    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    background_rect = QRectF(scaled(52, size), scaled(52, size), scaled(920, size), scaled(920, size))
    background_radius = scaled(220, size)

    shadow_path = QPainterPath()
    shadow_rect = QRectF(
        scaled(72, size),
        scaled(94, size),
        scaled(880, size),
        scaled(860, size),
    )
    shadow_path.addRoundedRect(shadow_rect, scaled(204, size), scaled(204, size))
    painter.fillPath(shadow_path, QColor(15, 24, 35, 40))

    gradient = QLinearGradient(background_rect.topLeft(), background_rect.bottomRight())
    gradient.setColorAt(0.0, QColor("#2d455b"))
    gradient.setColorAt(1.0, QColor("#1d2e40"))
    background_path = QPainterPath()
    background_path.addRoundedRect(background_rect, background_radius, background_radius)
    painter.fillPath(background_path, QBrush(gradient))

    panel_rect = QRectF(scaled(148, size), scaled(196, size), scaled(510, size), scaled(420, size))
    panel_path = QPainterPath()
    panel_path.addRoundedRect(panel_rect, scaled(88, size), scaled(88, size))
    painter.fillPath(panel_path, QColor("#f6fbff"))

    tail = QPainterPath()
    tail.moveTo(scaled(238, size), scaled(594, size))
    tail.lineTo(scaled(198, size), scaled(710, size))
    tail.lineTo(scaled(328, size), scaled(618, size))
    tail.closeSubpath()
    painter.fillPath(tail, QColor("#f6fbff"))

    rounded_bar(painter, size, 230, 286, 350, 54, "#54708b")
    rounded_bar(painter, size, 230, 370, 250, 48, "#70889f")
    rounded_bar(painter, size, 230, 444, 304, 48, "#70889f")

    rounded_bar(painter, size, 226, 534, 330, 26, "#d6dee6")
    rounded_bar(painter, size, 226, 534, 148, 26, "#31c4bf")
    rounded_bar(painter, size, 346, 498, 24, 98, "#31c4bf")

    for tick_x in (246, 300, 430, 494, 546):
        rounded_bar(painter, size, tick_x, 578, 14, 34, "#8aa1b8")

    document_rect = QRectF(scaled(582, size), scaled(294, size), scaled(256, size), scaled(348, size))
    document_path = QPainterPath()
    document_path.addRoundedRect(document_rect, scaled(44, size), scaled(44, size))
    painter.fillPath(document_path, QColor("#fff7ed"))

    fold_path = QPainterPath()
    fold_path.moveTo(scaled(748, size), scaled(294, size))
    fold_path.lineTo(scaled(838, size), scaled(294, size))
    fold_path.lineTo(scaled(838, size), scaled(384, size))
    fold_path.closeSubpath()
    painter.fillPath(fold_path, QColor("#ffd9bc"))

    draw_chevron(painter, size, ((644, 468), (690, 418), (736, 468)), "#ff8a4c")
    draw_chevron(painter, size, ((756, 468), (802, 518), (756, 568)), "#ff8a4c")

    rounded_bar(painter, size, 628, 554, 156, 30, "#ffb17f")

    accent_ring = QPainterPath()
    accent_ring.addEllipse(QPointF(scaled(764, size), scaled(296, size)), scaled(52, size), scaled(52, size))
    painter.fillPath(accent_ring, QColor(49, 196, 191, 210))

    painter.end()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(output_path))


def main() -> None:
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)
    for filename, size in OUTPUT_SPECS:
        draw_icon(size, ICONSET_DIR / filename)
    draw_icon(1024, MASTER_PATH)


if __name__ == "__main__":
    main()
