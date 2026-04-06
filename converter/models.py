from dataclasses import dataclass


@dataclass(frozen=True)
class SubtitleCue:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class TemplatePrototype:
    track_node: object
    clipitem_node: object
    fps: float
    ntsc: bool
    ticks_per_frame: int
    text_param_name: str


@dataclass(frozen=True)
class ConversionResult:
    output_path: str
    clip_count: int
    sequence_duration_frames: int
    preview_lines: tuple[str, ...] = ()
