from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.config.models import ContentBrief, RenderedMedia


@dataclass
class MediaFactoryConfig:
    workspace_root: Path
    output_dir: Path
    default_duration_seconds: int = 55
    enable_ffmpeg: bool = True


class MediaFactory:
    def __init__(self, config: MediaFactoryConfig) -> None:
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def render(self, brief: ContentBrief, source_clips: List[Path] | None = None) -> RenderedMedia:
        source_clips = source_clips or []
        output_path = self.config.output_dir / f"{brief.brief_id}.mp4"
        contains_synthetic = "ai" in brief.niche_id or "ghost_lore" in brief.niche_id

        if self.config.enable_ffmpeg and source_clips:
            concat_file = self.config.output_dir / f"{brief.brief_id}_concat.txt"
            concat_lines = [f"file '{clip.as_posix()}'" for clip in source_clips]
            concat_file.write_text("\n".join(concat_lines), encoding="utf-8")
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(output_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            concat_file.unlink(missing_ok=True)
            duration = self._probe_duration(output_path) or self.config.default_duration_seconds
        else:
            # Planning mode fallback: produce a virtual artifact path for downstream scheduling/upload metadata.
            output_path.touch(exist_ok=True)
            duration = self.config.default_duration_seconds

        return RenderedMedia(
            media_path=str(output_path),
            duration_seconds=duration,
            aspect_ratio="9:16" if "shorts" in " ".join(brief.target_formats).lower() else "16:9",
            contains_synthetic_media=contains_synthetic,
            source_credits=brief.evidence_links,
        )

    @staticmethod
    def _probe_duration(path: Path) -> int | None:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
        try:
            output = subprocess.run(cmd, check=True, capture_output=True, text=True)
        except Exception:
            return None
        try:
            return int(float(output.stdout.strip()))
        except ValueError:
            return None
