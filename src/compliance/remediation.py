from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from src.config.models import UploadJob


@dataclass
class RemediationAction:
    action_type: str
    summary: str
    remediated_media_path: Optional[str] = None
    next_attempt_at_utc: Optional[datetime] = None


class RemediationEngine:
    def __init__(self, max_retries: int = 2) -> None:
        self.max_retries = max_retries

    def remediate_technical_failure(self, job: UploadJob) -> RemediationAction:
        if job.retry_count >= self.max_retries:
            return RemediationAction(
                action_type="manual_review",
                summary="Retry limit reached; escalation required.",
            )

        source = Path(job.media.media_path)
        fixed_output = source.with_name(f"{source.stem}_reencoded{source.suffix}")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(fixed_output),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except Exception as exc:
            return RemediationAction(
                action_type="manual_review",
                summary=f"Re-encode failed: {exc}",
            )

        next_time = datetime.now(tz=timezone.utc) + timedelta(minutes=15)
        return RemediationAction(
            action_type="retry_upload",
            summary="Transcoded media for retry.",
            remediated_media_path=str(fixed_output),
            next_attempt_at_utc=next_time,
        )

    @staticmethod
    def route_policy_risk(job: UploadJob, reason: str) -> RemediationAction:
        return RemediationAction(
            action_type="manual_review",
            summary=f"Policy/copyright risk requires human review: {reason}",
        )
