import copy
from pathlib import Path

import pytest
import srt
import lxml.etree as etree

from converter import ConversionError, ConversionService
from converter.payload import extract_payload_text


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_subtitles_supports_utf8_bom(tmp_path: Path) -> None:
    srt_path = tmp_path / "bom.srt"
    srt_path.write_text(
        "\ufeff1\n00:00:01,000 --> 00:00:02,100\n第一行\n\n2\n00:00:03,000 --> 00:00:04,000\n第二行\n",
        encoding="utf-8",
    )

    service = ConversionService()
    subtitles = service._load_subtitles(str(srt_path))

    assert len(subtitles) == 2
    assert subtitles[0].text == "第一行"
    assert subtitles[1].end_seconds == 4.0


def test_load_subtitles_raises_for_invalid_srt(tmp_path: Path) -> None:
    srt_path = tmp_path / "invalid.srt"
    srt_path.write_text("not a valid srt file", encoding="utf-8")

    service = ConversionService()
    with pytest.raises(ConversionError):
        service._load_subtitles(str(srt_path))


def test_find_template_prototype_supports_source_text_alias(tmp_path: Path) -> None:
    xml_text = (FIXTURES_DIR / "template_sample.xml").read_text(encoding="utf-8-sig")
    modified_text = xml_text.replace("<name>源文本</name>", "<name>Source Text</name>", 1)
    xml_path = tmp_path / "source-text-template.xml"
    xml_path.write_text(modified_text, encoding="utf-8")

    service = ConversionService()
    prototype = service._find_template_prototype(service._load_template_tree(str(xml_path)))

    assert prototype.text_param_name == "Source Text"


def test_find_template_prototype_requires_unique_candidate() -> None:
    service = ConversionService()
    tree = service._load_template_tree(str(FIXTURES_DIR / "template_sample.xml"))
    sequence = tree.getroot().find("./sequence")
    track = sequence.find("./media/video/track")
    clipitem = track.find("./clipitem")
    track.insert(1, copy.deepcopy(clipitem))

    with pytest.raises(ConversionError):
        service._find_template_prototype(tree)


def test_find_template_prototype_requires_graphic_candidate(tmp_path: Path) -> None:
    xml_text = (FIXTURES_DIR / "template_sample.xml").read_text(encoding="utf-8-sig")
    modified_text = xml_text.replace("<effectid>GraphicAndType</effectid>", "<effectid>OtherEffect</effectid>", 1)
    xml_path = tmp_path / "no-candidate.xml"
    xml_path.write_text(modified_text, encoding="utf-8")

    service = ConversionService()
    tree = service._load_template_tree(str(xml_path))

    with pytest.raises(ConversionError):
        service._find_template_prototype(tree)


def test_seconds_to_frame_uses_floor_and_ceiling() -> None:
    service = ConversionService()
    assert service._seconds_to_frame(5.866, 10160640000, round_up=False) == 146
    assert service._seconds_to_frame(7.466, 10160640000, round_up=True) == 187


def test_convert_sample_xml_generates_expected_output(tmp_path: Path) -> None:
    service = ConversionService()
    output_path = tmp_path / "converted.xml"

    result = service.convert(
        str(FIXTURES_DIR / "template_sample.xml"),
        str(FIXTURES_DIR / "input_sample.srt"),
        str(output_path),
    )

    assert output_path.exists()
    assert result.clip_count == 848

    output_text = output_path.read_text(encoding="utf-8")
    assert output_text.startswith("<?xml version='1.0' encoding='UTF-8'?>")
    assert "<!DOCTYPE xmeml>" in output_text

    tree = etree.parse(str(output_path))
    sequence = tree.getroot().find("./sequence")
    track = sequence.find("./media/video/track")
    clipitems = track.findall("./clipitem")
    assert len(clipitems) == 848

    subtitles = list(srt.parse((FIXTURES_DIR / "input_sample.srt").read_text(encoding="utf-8")))
    first_clip = clipitems[0]
    last_clip = clipitems[-1]

    assert first_clip.findtext("start") == "146"
    assert first_clip.findtext("end") == "187"
    assert last_clip.findtext("end") == "40534"
    assert sequence.findtext("duration") == "40534"

    first_effect = first_clip.find(".//effect[effectid='GraphicAndType']")
    last_effect = last_clip.find(".//effect[effectid='GraphicAndType']")
    assert first_effect.findtext("name") == "寻觅千年的药材\r"
    assert last_effect.findtext("name") == "更是与万物共荣\r"

    first_payload = first_effect.find("./parameter[name='源文本']/value").text
    last_payload = last_effect.find("./parameter[name='源文本']/value").text
    assert extract_payload_text(first_payload, first_effect.findtext("name")) == "寻觅千年的药材\r"
    assert extract_payload_text(last_payload, last_effect.findtext("name")) == "更是与万物共荣\r"

    expected_first = subtitles[0]
    assert expected_first.content == "寻觅千年的药材"
