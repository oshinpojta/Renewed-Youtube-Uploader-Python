from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.config.models import ChannelProfile, UploadJob


class PipelineEventLogger:
    """Writes structured JSONL logs for pipeline and metrics analysis."""

    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline_log_path = self.logs_dir / "pipeline_events.jsonl"
        self.metrics_log_path = self.logs_dir / "video_metrics.jsonl"

    def log_pipeline_event(
        self,
        event_type: str,
        channel: ChannelProfile,
        job: Optional[UploadJob] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        row: Dict[str, Any] = {
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            "event_type": event_type,
            "channel_profile_id": channel.channel_profile_id,
            "channel_name": channel.channel_name,
            "timezone": channel.timezone,
        }
        if job is not None:
            metadata = job.metadata or {}
            row.update(
                {
                    "job_id": job.job_id,
                    "niche_id": job.brief.niche_id,
                    "brief_id": job.brief.brief_id,
                    "seed_keyword": job.brief.seed_keyword,
                    "title": job.brief.working_title,
                    "scheduled_publish_at_utc": job.scheduled_publish_at_utc.isoformat(),
                    "status": job.status.value,
                    "video_id": job.video_id,
                    "retry_count": job.retry_count,
                    "duration_seconds": job.media.duration_seconds,
                    "aspect_ratio": job.media.aspect_ratio,
                    "contains_synthetic_media": job.media.contains_synthetic_media,
                    "generation_provider": job.media.generation_provider,
                    "generation_model": job.media.generation_model,
                    "generation_mode": job.media.generation_mode,
                    "generation_notes": job.media.generation_notes,
                    "generation_task_id": job.media.generation_task_id,
                    "render_latency_seconds": job.media.render_latency_seconds,
                    "text_provider": metadata.get("text_provider", ""),
                    "research_provider": metadata.get("research_provider", ""),
                    "citation_count": metadata.get("citation_count", 0),
                    "script_id": metadata.get("script_id", ""),
                    "script_scene_count": metadata.get("script_scene_count", 0),
                }
            )
        if payload:
            row["payload"] = payload
        self._append_jsonl(self.pipeline_log_path, row)

    def log_video_metrics(
        self,
        channel: ChannelProfile,
        job_id: str,
        video_id: str,
        niche_id: str,
        snapshot: Dict[str, Any],
    ) -> None:
        row = {
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            "channel_profile_id": channel.channel_profile_id,
            "channel_name": channel.channel_name,
            "job_id": job_id,
            "video_id": video_id,
            "niche_id": niche_id,
            "snapshot": snapshot,
        }
        self._append_jsonl(self.metrics_log_path, row)

    @staticmethod
    def _append_jsonl(path: Path, row: Dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as fileptr:
            fileptr.write(json.dumps(row, ensure_ascii=True, default=str))
            fileptr.write("\n")
