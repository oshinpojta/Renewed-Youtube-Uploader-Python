from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MediaValidationResult:
    is_valid: bool
    reason: str = ""
    has_video: bool = False
    has_audio: bool = False
    duration_seconds: float = 0.0


def validate_rendered_media(
    path: Path,
    require_audio: bool = True,
    min_duration_seconds: float = 6.0,
) -> MediaValidationResult:
    if not path.exists():
        return MediaValidationResult(is_valid=False, reason=f"file_missing:{path}")
    if path.stat().st_size <= 0:
        return MediaValidationResult(is_valid=False, reason="file_empty")

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type:format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        output = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        return MediaValidationResult(is_valid=False, reason="ffprobe_not_installed")
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        reason = f"ffprobe_failed:{details}" if details else "ffprobe_failed"
        return MediaValidationResult(is_valid=False, reason=reason)
    except Exception as exc:  # pragma: no cover - defensive guard
        return MediaValidationResult(is_valid=False, reason=f"ffprobe_error:{exc}")

    try:
        payload = json.loads(output.stdout or "{}")
    except json.JSONDecodeError:
        return MediaValidationResult(is_valid=False, reason="ffprobe_invalid_json")

    streams = payload.get("streams", [])
    has_video = any(stream.get("codec_type") == "video" for stream in streams if isinstance(stream, dict))
    has_audio = any(stream.get("codec_type") == "audio" for stream in streams if isinstance(stream, dict))

    duration_seconds = 0.0
    format_blob = payload.get("format", {})
    if isinstance(format_blob, dict):
        raw_duration = format_blob.get("duration")
        try:
            duration_seconds = float(raw_duration)
        except (TypeError, ValueError):
            duration_seconds = 0.0

    if not has_video:
        return MediaValidationResult(
            is_valid=False,
            reason="missing_video_stream",
            has_video=has_video,
            has_audio=has_audio,
            duration_seconds=duration_seconds,
        )
    if require_audio and not has_audio:
        return MediaValidationResult(
            is_valid=False,
            reason="missing_audio_stream",
            has_video=has_video,
            has_audio=has_audio,
            duration_seconds=duration_seconds,
        )
    if duration_seconds <= 0:
        return MediaValidationResult(
            is_valid=False,
            reason="invalid_duration",
            has_video=has_video,
            has_audio=has_audio,
            duration_seconds=duration_seconds,
        )
    if duration_seconds < min_duration_seconds:
        return MediaValidationResult(
            is_valid=False,
            reason=f"duration_too_short:{duration_seconds:.2f}s",
            has_video=has_video,
            has_audio=has_audio,
            duration_seconds=duration_seconds,
        )

    return MediaValidationResult(
        is_valid=True,
        has_video=has_video,
        has_audio=has_audio,
        duration_seconds=duration_seconds,
    )
