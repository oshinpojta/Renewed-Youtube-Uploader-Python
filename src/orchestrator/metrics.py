from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from src.storage.job_store import JobStore


@dataclass(frozen=True)
class PipelineMetrics:
    upload_success_rate: float
    needs_review_rate: float
    failure_rate: float
    tracked_videos: float
    avg_views: float
    avg_likes: float
    avg_comments: float


class MetricsService:
    def __init__(self, job_store: JobStore) -> None:
        self.job_store = job_store

    def summarize_channel(self, channel_profile_id: str) -> PipelineMetrics:
        # Lightweight v1 metrics from stored jobs table.
        import sqlite3

        with sqlite3.connect(self.job_store.db_path) as conn:
            rows = conn.execute(
                """
                SELECT status, COUNT(*)
                FROM jobs
                WHERE channel_profile_id = ?
                GROUP BY status
                """,
                (channel_profile_id,),
            ).fetchall()

        counts: Dict[str, int] = {status: int(total) for status, total in rows}
        total = sum(counts.values()) or 1
        success = counts.get("published", 0) / total
        needs_review = counts.get("needs_review", 0) / total
        failed = counts.get("failed", 0) / total
        video_summary = self.job_store.summarize_latest_video_metrics(channel_profile_id)
        return PipelineMetrics(
            upload_success_rate=success,
            needs_review_rate=needs_review,
            failure_rate=failed,
            tracked_videos=video_summary["tracked_videos"],
            avg_views=video_summary["avg_views"],
            avg_likes=video_summary["avg_likes"],
            avg_comments=video_summary["avg_comments"],
        )
