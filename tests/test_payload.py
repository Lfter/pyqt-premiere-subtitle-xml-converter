import base64
from pathlib import Path

import lxml.etree as etree

from converter.payload import extract_payload_text, normalize_premiere_text, replace_text_payload


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_text_payload_and_name() -> tuple[str, str]:
    tree = etree.parse(str(FIXTURES_DIR / "template_sample.xml"))
    effect = tree.find(".//effect[effectid='GraphicAndType']")
    if effect is None:
        raise AssertionError("Fixture template must contain GraphicAndType effect.")
    effect_name = effect.findtext("name")
    payload_node = effect.find("./parameter[name='源文本']/value")
    if payload_node is None or payload_node.text is None:
        raise AssertionError("Fixture template must contain source text payload.")
    if effect_name is None:
        raise AssertionError("Fixture template must contain effect name.")
    encoded_payload = payload_node.text
    return encoded_payload, effect_name


def test_normalize_premiere_text_uses_carriage_returns() -> None:
    assert normalize_premiere_text("第一行\n第二行") == "第一行\r第二行\r"


def test_replace_text_payload_updates_text_length_and_padding() -> None:
    encoded_payload, effect_name = _load_text_payload_and_name()
    replacement_text = "Long ASCII line\n第二行字幕"
    updated_payload = replace_text_payload(encoded_payload, replacement_text, effect_name)

    extracted_text = extract_payload_text(updated_payload, effect_name)
    assert extracted_text == normalize_premiere_text(replacement_text)

    payload_bytes = base64.b64decode(updated_payload.encode("ascii"))
    replacement_bytes = normalize_premiere_text(replacement_text).encode("utf-8")
    start = payload_bytes.rfind(replacement_bytes)
    assert start >= 4
    assert int.from_bytes(payload_bytes[start - 4:start], "little") == len(replacement_bytes)
    assert payload_bytes[start + len(replacement_bytes):] == b"\x00" * ((4 - len(replacement_bytes) % 4) % 4)


def test_extract_payload_text_reads_original_sample_text() -> None:
    encoded_payload, effect_name = _load_text_payload_and_name()
    assert extract_payload_text(encoded_payload, effect_name) == "我是总台节目主持人撒贝宁\r"
