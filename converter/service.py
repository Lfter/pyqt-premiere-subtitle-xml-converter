from __future__ import annotations

import copy
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path
from typing import Iterable

from lxml import etree
import srt

from .errors import ConversionError
from .models import ConversionResult, SubtitleCue, TemplatePrototype
from .payload import normalize_premiere_text, replace_text_payload

PREMIERE_TICKS_PER_SECOND = 254_016_000_000


@dataclass
class IdAllocator:
    clipitem: int
    masterclip: int
    file: int

    def next_clipitem_id(self) -> str:
        current = f"clipitem-{self.clipitem}"
        self.clipitem += 1
        return current

    def next_masterclip_id(self) -> str:
        current = f"masterclip-{self.masterclip}"
        self.masterclip += 1
        return current

    def next_file_id(self) -> str:
        current = f"file-{self.file}"
        self.file += 1
        return current


class ConversionService:
    def convert(self, template_xml_path: str, srt_path: str, output_xml_path: str) -> ConversionResult:
        template_tree = self._load_template_tree(template_xml_path)
        subtitles = self._load_subtitles(srt_path)
        prototype = self._find_template_prototype(template_tree)
        id_allocator = self._build_id_allocator(template_tree)
        generated_clips = [
            self._build_clipitem(prototype, cue, id_allocator)
            for cue in subtitles
        ]
        self._replace_prototype_clip(template_tree, prototype, generated_clips)
        sequence_duration = self._update_sequence_duration(template_tree, generated_clips)
        self._write_tree(template_tree, output_xml_path)
        return ConversionResult(
            output_path=str(output_xml_path),
            clip_count=len(generated_clips),
            sequence_duration_frames=sequence_duration,
            preview_lines=tuple(cue.text for cue in subtitles[:3]),
        )

    def _load_template_tree(self, template_xml_path: str):
        try:
            parser = etree.XMLParser(remove_blank_text=False, recover=False)
            tree = etree.parse(template_xml_path, parser)
        except (OSError, etree.XMLSyntaxError) as exc:
            raise ConversionError(f"无法读取 XML 模板文件：{exc}") from exc

        root = tree.getroot()
        if root.tag != "xmeml":
            raise ConversionError("仅支持 Premiere 导出的 xmeml 序列 XML 模板。")
        if tree.docinfo.doctype and "xmeml" not in tree.docinfo.doctype.lower():
            raise ConversionError("XML 模板缺少有效的 xmeml DOCTYPE。")
        if root.find("./sequence") is None:
            raise ConversionError("XML 模板中缺少 sequence 节点。")
        return tree

    def _load_subtitles(self, srt_path: str) -> list[SubtitleCue]:
        try:
            raw_text = Path(srt_path).read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise ConversionError(f"无法读取 SRT 文件：{exc}") from exc

        try:
            parsed_subtitles = list(srt.parse(raw_text))
        except srt.SRTParseError as exc:
            raise ConversionError(f"SRT 解析失败：{exc}") from exc

        if not parsed_subtitles:
            raise ConversionError("SRT 文件中没有可转换的字幕条目。")

        cues = []
        for item in parsed_subtitles:
            text = item.content.strip()
            if not text:
                continue
            cues.append(
                SubtitleCue(
                    start_seconds=item.start.total_seconds(),
                    end_seconds=item.end.total_seconds(),
                    text=text,
                )
            )

        if not cues:
            raise ConversionError("SRT 文件中的字幕文本为空。")

        return cues

    def _find_template_prototype(self, tree) -> TemplatePrototype:
        sequence = tree.getroot().find("./sequence")
        rate_node = sequence.find("./rate")
        if rate_node is None:
            raise ConversionError("XML 模板缺少 sequence/rate 帧率信息。")

        timebase_text = (rate_node.findtext("timebase") or "").strip()
        ntsc_text = (rate_node.findtext("ntsc") or "").strip().upper()
        if not timebase_text.isdigit():
            raise ConversionError("XML 模板中的 timebase 无法识别。")

        timebase = int(timebase_text)
        ntsc = ntsc_text == "TRUE"
        fps = timebase * 1000 / 1001 if ntsc else float(timebase)

        candidates = []
        for track in sequence.findall("./media/video/track"):
            for clipitem in track.findall("./clipitem"):
                text_param_name = self._find_text_parameter_name(clipitem)
                if text_param_name:
                    candidates.append((track, clipitem, text_param_name))

        if not candidates:
            raise ConversionError("模板中没有找到可复制的 Premiere 图形字幕原型。")
        if len(candidates) > 1:
            raise ConversionError("模板中识别到多个图形字幕原型，请保留一个参考字幕片段后再转换。")

        track_node, clipitem_node, text_param_name = candidates[0]
        ticks_per_frame = self._infer_ticks_per_frame(clipitem_node, fps, ntsc, timebase)
        return TemplatePrototype(
            track_node=track_node,
            clipitem_node=clipitem_node,
            fps=fps,
            ntsc=ntsc,
            ticks_per_frame=ticks_per_frame,
            text_param_name=text_param_name,
        )

    def _find_text_parameter_name(self, clipitem_node) -> str | None:
        for effect in clipitem_node.findall("./filter/effect"):
            effect_id = (effect.findtext("effectid") or "").strip()
            if effect_id != "GraphicAndType":
                continue
            for parameter in effect.findall("./parameter"):
                parameter_name = (parameter.findtext("name") or "").strip()
                if parameter_name in {"源文本", "Source Text"}:
                    return parameter_name
        return None

    def _infer_ticks_per_frame(self, clipitem_node, fps: float, ntsc: bool, timebase: int) -> int:
        clip_in = self._safe_int(clipitem_node.findtext("in"))
        clip_out = self._safe_int(clipitem_node.findtext("out"))
        ppro_ticks_in = self._safe_int(clipitem_node.findtext("pproTicksIn"))
        ppro_ticks_out = self._safe_int(clipitem_node.findtext("pproTicksOut"))
        clip_duration = clip_out - clip_in
        if clip_duration > 0 and ppro_ticks_out > ppro_ticks_in:
            ticks_delta = ppro_ticks_out - ppro_ticks_in
            if ticks_delta % clip_duration == 0:
                return ticks_delta // clip_duration

        fps_decimal = Decimal(timebase) * (Decimal("1000") / Decimal("1001") if ntsc else Decimal(1))
        return int((Decimal(PREMIERE_TICKS_PER_SECOND) / fps_decimal).to_integral_value())

    def _build_id_allocator(self, tree) -> IdAllocator:
        clipitem_ids = [node.get("id", "") for node in tree.findall(".//clipitem")]
        masterclip_ids = [node.text or "" for node in tree.findall(".//masterclipid")]
        file_ids = [node.get("id", "") for node in tree.findall(".//file")]
        return IdAllocator(
            clipitem=self._next_sequence_number(clipitem_ids, "clipitem"),
            masterclip=self._next_sequence_number(masterclip_ids, "masterclip"),
            file=self._next_sequence_number(file_ids, "file"),
        )

    def _next_sequence_number(self, values: Iterable[str], prefix: str) -> int:
        max_number = 0
        expected_prefix = f"{prefix}-"
        for value in values:
            if not value.startswith(expected_prefix):
                continue
            try:
                max_number = max(max_number, int(value[len(expected_prefix):]))
            except ValueError:
                continue
        return max_number + 1

    def _build_clipitem(self, prototype: TemplatePrototype, cue: SubtitleCue, ids: IdAllocator):
        clipitem = copy.deepcopy(prototype.clipitem_node)
        start_frame = self._seconds_to_frame(cue.start_seconds, prototype.ticks_per_frame, round_up=False)
        end_frame = self._seconds_to_frame(cue.end_seconds, prototype.ticks_per_frame, round_up=True)
        if end_frame <= start_frame:
            end_frame = start_frame + 1
        duration_frames = end_frame - start_frame

        clipitem.set("id", ids.next_clipitem_id())
        self._set_child_text(clipitem, "masterclipid", ids.next_masterclip_id())
        file_node = clipitem.find("./file")
        if file_node is not None:
            file_node.set("id", ids.next_file_id())

        display_text = cue.text.replace("\r\n", "\n").replace("\r", "\n").strip()
        safe_clip_name = " ".join(part for part in display_text.splitlines() if part).strip() or "Subtitle"
        self._set_child_text(clipitem, "name", safe_clip_name)
        self._set_child_text(clipitem, "start", str(start_frame))
        self._set_child_text(clipitem, "end", str(end_frame))

        prototype_in = self._safe_int(prototype.clipitem_node.findtext("in"))
        prototype_ticks_in = self._safe_int(prototype.clipitem_node.findtext("pproTicksIn"))
        self._set_child_text(clipitem, "in", str(prototype_in))
        self._set_child_text(clipitem, "out", str(prototype_in + duration_frames))
        if clipitem.find("./pproTicksIn") is not None:
            self._set_child_text(clipitem, "pproTicksIn", str(prototype_ticks_in))
        if clipitem.find("./pproTicksOut") is not None:
            self._set_child_text(
                clipitem,
                "pproTicksOut",
                str(prototype_ticks_in + duration_frames * prototype.ticks_per_frame),
            )

        graphic_effect = self._find_graphic_effect(clipitem)
        current_effect_name = graphic_effect.findtext("name") or ""
        normalized_text = normalize_premiere_text(display_text)
        graphic_effect.find("name").text = normalized_text
        for parameter in graphic_effect.findall("./parameter"):
            parameter_name = (parameter.findtext("name") or "").strip()
            if parameter_name != prototype.text_param_name:
                continue
            value_node = parameter.find("./value")
            if value_node is None or not value_node.text:
                raise ConversionError("模板中的字幕源文本参数缺少有效的 value。")
            value_node.text = replace_text_payload(value_node.text, display_text, current_effect_name)
            break

        return clipitem

    def _replace_prototype_clip(self, tree, prototype: TemplatePrototype, generated_clips: list) -> None:
        track_node = prototype.track_node
        children = list(track_node)
        insertion_index = children.index(prototype.clipitem_node)
        track_node.remove(prototype.clipitem_node)
        for offset, clipitem in enumerate(generated_clips):
            track_node.insert(insertion_index + offset, clipitem)

    def _update_sequence_duration(self, tree, generated_clips: list) -> int:
        if not generated_clips:
            raise ConversionError("没有生成任何字幕片段。")

        sequence = tree.getroot().find("./sequence")
        sequence_duration_node = sequence.find("./duration")
        if sequence_duration_node is None:
            raise ConversionError("模板中的 sequence 缺少 duration 节点。")

        current_duration = self._safe_int(sequence_duration_node.text)
        final_clip_end = max(self._safe_int(node.findtext("end")) for node in generated_clips)
        updated_duration = max(current_duration, final_clip_end)
        sequence_duration_node.text = str(updated_duration)
        return updated_duration

    def _write_tree(self, tree, output_xml_path: str) -> None:
        doctype = tree.docinfo.doctype or "<!DOCTYPE xmeml>"
        output_path = Path(output_xml_path)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            tree.write(
                str(output_path),
                encoding="UTF-8",
                xml_declaration=True,
                doctype=doctype,
                pretty_print=True,
            )
        except OSError as exc:
            raise ConversionError(f"无法写入输出 XML 文件：{exc}") from exc

    def _find_graphic_effect(self, clipitem_node):
        for effect in clipitem_node.findall("./filter/effect"):
            if (effect.findtext("effectid") or "").strip() == "GraphicAndType":
                return effect
        raise ConversionError("模板中的 clipitem 缺少 GraphicAndType effect。")

    def _seconds_to_frame(self, seconds: float, ticks_per_frame: int, round_up: bool) -> int:
        seconds_decimal = Decimal(str(seconds))
        frame_value = (seconds_decimal * Decimal(PREMIERE_TICKS_PER_SECOND)) / Decimal(ticks_per_frame)
        rounding_mode = ROUND_CEILING if round_up else ROUND_FLOOR
        return int(frame_value.to_integral_value(rounding=rounding_mode))

    def _safe_int(self, value: str | None) -> int:
        try:
            return int((value or "0").strip())
        except ValueError:
            raise ConversionError(f"无法解析 XML 中的整数值：{value!r}")

    def _set_child_text(self, parent, xpath: str, value: str) -> None:
        node = parent.find(f"./{xpath}")
        if node is not None:
            node.text = value
