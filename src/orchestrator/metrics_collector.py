from __future__ import annotations

import re
from typing import Dict, Optional

from src.config.models import ChannelProfile
from src.storage.event_logger import PipelineEventLogger
from src.storage.job_store import JobStore
from src.youtube.monitor import YouTubePostPublishMonitor


ISO8601_DURATION_RE = re.compile(
    r"^P(?:\d+Y)?(?:\d+M)?(?:\d+D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$"
)


def parse_iso8601_duration_seconds(value: Optional[str]) -> int:
    if not value:
        return 0
    match = ISO8601_DURATION_RE.match(value)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


class MetricsCollector:
    def __init__(
        self,
        job_store: JobStore,
        monitor: YouTubePostPublishMonitor,
        event_logger: PipelineEventLogger,
    ) -> None:
        self.job_store = job_store
        self.monitor = monitor
        self.event_logger = event_logger

    def collect_for_channel(self, channel: ChannelProfile) -> int:
        jobs = self.job_store.list_jobs_with_video(channel.channel_profile_id, limit=300)
        collected = 0
        for row in jobs:
            video_id = row.get("video_id")
            if not video_id:
                continue
            try:
                snapshot = self.monitor.fetch_video_snapshot(channel, video_id)
            except Exception as exc:
                self.job_store.add_job_event(
                    event_type="video_metrics_collect_failed",
                    channel_profile_id=channel.channel_profile_id,
                    niche_id=row.get("niche_id"),
                    job_id=row.get("job_id"),
                    video_id=video_id,
                    payload={"error": str(exc)},
                )
                continue

            stats = snapshot.get("statistics", {})
            snippet = snapshot.get("snippet", {})
            content_details = snapshot.get("contentDetails", {})
            status = snapshot.get("status", {})
            duration_seconds = parse_iso8601_duration_seconds(content_details.get("duration"))
            payload = {
                "title": snippet.get("title"),
                "publishedAt": snippet.get("publishedAt"),
                "views": int(stats.get("viewCount", 0) or 0),
                "likes": int(stats.get("likeCount", 0) or 0),
                "comments": int(stats.get("commentCount", 0) or 0),
                "durationSeconds": duration_seconds,
                "privacyStatus": status.get("privacyStatus"),
                "uploadStatus": status.get("uploadStatus"),
            }
            self.job_store.add_video_metric_snapshot(
                channel_profile_id=channel.channel_profile_id,
                niche_id=row.get("niche_id"),
                job_id=row.get("job_id"),
                video_id=video_id,
                title=snippet.get("title") or row.get("title"),
                publish_at_utc=status.get("publishAt") or snippet.get("publishedAt"),
                views=payload["views"],
                likes=payload["likes"],
                comments=payload["comments"],
                duration_seconds=duration_seconds,
                payload=snapshot,
            )
            self.event_logger.log_video_metrics(
                channel=channel,
                job_id=row.get("job_id") or "",
                video_id=video_id,
                niche_id=row.get("niche_id") or "",
                snapshot=payload,
            )
            self.job_store.add_job_event(
                event_type="video_metrics_collected",
                channel_profile_id=channel.channel_profile_id,
                niche_id=row.get("niche_id"),
                job_id=row.get("job_id"),
                video_id=video_id,
                payload=payload,
            )
            collected += 1
        return collected
