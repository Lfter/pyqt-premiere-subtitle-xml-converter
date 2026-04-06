from __future__ import annotations

import base64
from dataclasses import dataclass

from .errors import ConversionError


@dataclass(frozen=True)
class PayloadTextSegment:
    length_offset: int
    text_start: int
    text_end: int


def normalize_premiere_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    if not normalized:
        return "\r"
    return normalized.replace("\n", "\r") + "\r"


def extract_payload_text(encoded_value: str, effect_name: str | None = None) -> str:
    payload = base64.b64decode(encoded_value.encode("ascii"))
    segment = _locate_payload_text_segment(payload, effect_name)
    return payload[segment.text_start:segment.text_end].decode("utf-8")


def replace_text_payload(encoded_value: str, new_text: str, effect_name: str | None = None) -> str:
    payload = base64.b64decode(encoded_value.encode("ascii"))
    segment = _locate_payload_text_segment(payload, effect_name)
    replacement = normalize_premiere_text(new_text).encode("utf-8")
    padding = b"\x00" * ((4 - (len(replacement) % 4)) % 4)
    updated = payload[:segment.length_offset] + len(replacement).to_bytes(4, "little") + replacement + padding
    return base64.b64encode(updated).decode("ascii")


def _locate_payload_text_segment(payload: bytes, effect_name: str | None) -> PayloadTextSegment:
    candidate_texts = []
    if effect_name:
        raw_name = effect_name.replace("\n", "\r")
        stripped_name = raw_name.rstrip("\r")
        candidate_texts.extend(
            [
                raw_name,
                stripped_name,
                normalize_premiere_text(stripped_name),
            ]
        )

    seen = set()
    for candidate in candidate_texts:
        if candidate in seen:
            continue
        seen.add(candidate)
        candidate_bytes = candidate.encode("utf-8")
        start = payload.rfind(candidate_bytes)
        if start == -1 or start < 4:
            continue
        if int.from_bytes(payload[start - 4:start], "little") != len(candidate_bytes):
            continue
        if not _has_supported_tail(payload, start + len(candidate_bytes)):
            continue
        return PayloadTextSegment(start - 4, start, start + len(candidate_bytes))

    search_floor = max(4, len(payload) - 1024)
    for text_start in range(len(payload) - 1, search_floor - 1, -1):
        length = int.from_bytes(payload[text_start - 4:text_start], "little")
        if length <= 0:
            continue
        text_end = text_start + length
        if text_end > len(payload):
            continue
        if not _has_supported_tail(payload, text_end):
            continue
        candidate_bytes = payload[text_start:text_end]
        try:
            candidate_bytes.decode("utf-8")
        except UnicodeDecodeError:
            continue
        return PayloadTextSegment(text_start - 4, text_start, text_end)

    raise ConversionError("无法识别 Premiere 图形字幕的源文本载荷结构。")


def _has_supported_tail(payload: bytes, text_end: int) -> bool:
    tail = payload[text_end:]
    return len(tail) <= 3 and all(byte == 0 for byte in tail)
