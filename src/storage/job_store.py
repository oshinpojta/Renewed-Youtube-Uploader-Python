from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config.models import JobStatus, UploadJob


class JobStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    channel_profile_id TEXT NOT NULL,
                    niche_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    scheduled_publish_at_utc TEXT NOT NULL,
                    video_id TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    metadata_json TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_profile_id TEXT NOT NULL,
                    publish_hour_local INTEGER NOT NULL,
                    ctr REAL NOT NULL,
                    retention REAL NOT NULL,
                    collected_at_utc TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_time_utc TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    channel_profile_id TEXT NOT NULL,
                    niche_id TEXT,
                    job_id TEXT,
                    video_id TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS video_metric_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    captured_at_utc TEXT NOT NULL,
                    channel_profile_id TEXT NOT NULL,
                    niche_id TEXT,
                    job_id TEXT,
                    video_id TEXT NOT NULL,
                    title TEXT,
                    publish_at_utc TEXT,
                    views INTEGER,
                    likes INTEGER,
                    comments INTEGER,
                    duration_seconds INTEGER,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def upsert_job(self, job: UploadJob) -> None:
        metadata_json = json.dumps(job.metadata)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, channel_profile_id, niche_id, title, status,
                    scheduled_publish_at_utc, video_id, retry_count, last_error,
                    metadata_json, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    status=excluded.status,
                    video_id=excluded.video_id,
                    retry_count=excluded.retry_count,
                    last_error=excluded.last_error,
                    metadata_json=excluded.metadata_json
                """,
                (
                    job.job_id,
                    job.brief.channel_profile_id,
                    job.brief.niche_id,
                    job.brief.working_title,
                    job.status.value,
                    job.scheduled_publish_at_utc.isoformat(),
                    job.video_id,
                    job.retry_count,
                    job.last_error,
                    metadata_json,
                    datetime.utcnow().isoformat(),
                ),
            )

    def list_recent_titles(self, channel_profile_id: str, limit: int = 30) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT title
                FROM jobs
                WHERE channel_profile_id = ?
                ORDER BY created_at_utc DESC
                LIMIT ?
                """,
                (channel_profile_id, limit),
            ).fetchall()
        return [row[0] for row in rows]

    def add_performance_metric(
        self,
        channel_profile_id: str,
        publish_hour_local: int,
        ctr: float,
        retention: float,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO performance_metrics (
                    channel_profile_id, publish_hour_local, ctr, retention, collected_at_utc
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    channel_profile_id,
                    publish_hour_local,
                    ctr,
                    retention,
                    datetime.utcnow().isoformat(),
                ),
            )

    def average_performance_by_hour(self, channel_profile_id: str) -> Dict[int, Tuple[float, float]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT publish_hour_local, AVG(ctr), AVG(retention)
                FROM performance_metrics
                WHERE channel_profile_id = ?
                GROUP BY publish_hour_local
                """,
                (channel_profile_id,),
            ).fetchall()
        return {int(hour): (float(ctr), float(ret)) for hour, ctr, ret in rows}

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        video_id: Optional[str] = None,
        last_error: Optional[str] = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, video_id = COALESCE(?, video_id), last_error = ?
                WHERE job_id = ?
                """,
                (status.value, video_id, last_error, job_id),
            )

    def add_job_event(
        self,
        event_type: str,
        channel_profile_id: str,
        niche_id: Optional[str],
        job_id: Optional[str],
        video_id: Optional[str],
        payload: Dict,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO job_events (
                    event_time_utc, event_type, channel_profile_id, niche_id, job_id, video_id, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    event_type,
                    channel_profile_id,
                    niche_id,
                    job_id,
                    video_id,
                    json.dumps(payload, default=str),
                ),
            )

    def list_jobs_with_video(
        self,
        channel_profile_id: str,
        limit: int = 200,
    ) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT job_id, niche_id, title, status, scheduled_publish_at_utc, video_id, metadata_json
                FROM jobs
                WHERE channel_profile_id = ? AND video_id IS NOT NULL
                ORDER BY created_at_utc DESC
                LIMIT ?
                """,
                (channel_profile_id, limit),
            ).fetchall()
        output: List[Dict] = []
        for row in rows:
            output.append(
                {
                    "job_id": row[0],
                    "niche_id": row[1],
                    "title": row[2],
                    "status": row[3],
                    "scheduled_publish_at_utc": row[4],
                    "video_id": row[5],
                    "metadata": json.loads(row[6] or "{}"),
                }
            )
        return output

    def add_video_metric_snapshot(
        self,
        channel_profile_id: str,
        niche_id: Optional[str],
        job_id: Optional[str],
        video_id: str,
        title: Optional[str],
        publish_at_utc: Optional[str],
        views: int,
        likes: int,
        comments: int,
        duration_seconds: Optional[int],
        payload: Dict,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO video_metric_snapshots (
                    captured_at_utc, channel_profile_id, niche_id, job_id, video_id, title,
                    publish_at_utc, views, likes, comments, duration_seconds, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    channel_profile_id,
                    niche_id,
                    job_id,
                    video_id,
                    title,
                    publish_at_utc,
                    views,
                    likes,
                    comments,
                    duration_seconds,
                    json.dumps(payload, default=str),
                ),
            )

    def summarize_latest_video_metrics(self, channel_profile_id: str) -> Dict[str, float]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) as n,
                    AVG(COALESCE(views, 0)),
                    AVG(COALESCE(likes, 0)),
                    AVG(COALESCE(comments, 0))
                FROM (
                    SELECT video_id,
                           MAX(captured_at_utc) as latest_at
                    FROM video_metric_snapshots
                    WHERE channel_profile_id = ?
                    GROUP BY video_id
                ) latest
                JOIN video_metric_snapshots vms
                  ON vms.video_id = latest.video_id
                 AND vms.captured_at_utc = latest.latest_at
                WHERE vms.channel_profile_id = ?
                """,
                (channel_profile_id, channel_profile_id),
            ).fetchone()
        if not row:
            return {"tracked_videos": 0.0, "avg_views": 0.0, "avg_likes": 0.0, "avg_comments": 0.0}
        return {
            "tracked_videos": float(row[0] or 0.0),
            "avg_views": float(row[1] or 0.0),
            "avg_likes": float(row[2] or 0.0),
            "avg_comments": float(row[3] or 0.0),
        }
