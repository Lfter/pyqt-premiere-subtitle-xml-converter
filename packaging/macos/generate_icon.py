from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


SIZE = 1024
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
MASTER_ICON_PATH = ASSETS_DIR / "srt_to_xml.png"


def _mix(start: tuple[int, int, int], end: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    return tuple(
        int(channel_start + (channel_end - channel_start) * ratio)
        for channel_start, channel_end in zip(start, end)
    )


def _draw_gradient(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    top = (34, 73, 155)
    bottom = (111, 173, 238)
    for y in range(SIZE):
        ratio = y / (SIZE - 1)
        draw.line([(0, y), (SIZE, y)], fill=_mix(top, bottom, ratio))


def _draw_background_card(canvas: Image.Image) -> None:
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((132, 132, 892, 892), radius=204, fill=(12, 29, 60, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    canvas.alpha_composite(shadow)

    card = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    card_draw.rounded_rectangle((112, 112, 912, 912), radius=196, fill=(247, 251, 255, 255))
    card_draw.rounded_rectangle((132, 132, 892, 892), radius=174, outline=(211, 225, 240, 255), width=8)
    fold = [(704, 112), (912, 112), (912, 320)]
    card_draw.polygon(fold, fill=(222, 234, 247, 255))
    card_draw.line([(704, 112), (704, 250), (840, 250)], fill=(188, 207, 229, 255), width=8)
    canvas.alpha_composite(card)


def _draw_subtitle_tracks(draw: ImageDraw.ImageDraw) -> None:
    pill_color = (124, 144, 168, 255)
    accent_color = (41, 108, 210, 255)
    y_positions = (296, 388, 480)
    widths = (472, 548, 432)
    for y, width in zip(y_positions, widths):
        draw.rounded_rectangle((236, y, 236 + width, y + 42), radius=21, fill=pill_color)
        draw.rounded_rectangle((196, y + 5, 222, y + 37), radius=13, fill=accent_color)
    draw.rounded_rectangle((236, 576, 620, 618), radius=21, fill=(178, 195, 213, 255))


def _draw_timeline_panel(draw: ImageDraw.ImageDraw) -> None:
    panel_bounds = (172, 660, 852, 842)
    draw.rounded_rectangle(panel_bounds, radius=72, fill=(28, 64, 132, 255))
    line_y = (714, 752, 790)
    line_lengths = (404, 310, 358)
    for y, length in zip(line_y, line_lengths):
        draw.rounded_rectangle((438, y, 438 + length, y + 18), radius=9, fill=(184, 214, 248, 255))
    for x in (236, 286, 336):
        draw.ellipse((x, 724, x + 22, 746), fill=(148, 205, 255, 255))
        draw.rounded_rectangle((x + 6, 752, x + 16, 812), radius=5, fill=(148, 205, 255, 255))


def _draw_xml_glyph(draw: ImageDraw.ImageDraw) -> None:
    stroke = 30
    left = [(280, 748), (214, 716), (280, 684)]
    right = [(372, 748), (438, 716), (372, 684)]
    slash = [(318, 770), (344, 662)]
    draw.line(left, fill=(255, 255, 255, 255), width=stroke, joint="curve")
    draw.line(right, fill=(255, 255, 255, 255), width=stroke, joint="curve")
    draw.line(slash, fill=(255, 255, 255, 255), width=24)


def build_icon() -> Path:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    _draw_gradient(image)
    image = image.filter(ImageFilter.GaussianBlur(0.4))
    _draw_background_card(image)

    draw = ImageDraw.Draw(image)
    _draw_subtitle_tracks(draw)
    _draw_timeline_panel(draw)
    _draw_xml_glyph(draw)

    highlight = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    highlight_draw = ImageDraw.Draw(highlight)
    highlight_draw.ellipse((152, 120, 730, 520), fill=(255, 255, 255, 40))
    highlight = highlight.filter(ImageFilter.GaussianBlur(24))
    image.alpha_composite(highlight)

    image.save(MASTER_ICON_PATH)
    return MASTER_ICON_PATH


if __name__ == "__main__":
    output_path = build_icon()
    print(output_path)
