from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from src.compliance.post_upload import PostUploadComplianceChecker, PostUploadDecision
from src.config.models import ChannelProfile
from src.youtube.auth import YouTubeAuthManager


@dataclass
class MonitorResult:
    video_id: str
    latest_resource: Dict
    decision: PostUploadDecision


class YouTubePostPublishMonitor:
    def __init__(
        self,
        auth_manager: YouTubeAuthManager,
        checker: Optional[PostUploadComplianceChecker] = None,
    ) -> None:
        self.auth_manager = auth_manager
        self.checker = checker or PostUploadComplianceChecker()

    def fetch_video_resource(self, profile: ChannelProfile, video_id: str) -> Dict:
        service = self.auth_manager.build_service(profile)
        response = (
            service.videos()
            .list(part="status,processingDetails,suggestions", id=video_id, maxResults=1)
            .execute()
        )
        items = response.get("items", [])
        if not items:
            raise RuntimeError(f"Video not found after upload: {video_id}")
        return items[0]

    def fetch_video_snapshot(self, profile: ChannelProfile, video_id: str) -> Dict:
        service = self.auth_manager.build_service(profile)
        response = (
            service.videos()
            .list(
                part="snippet,statistics,contentDetails,status,processingDetails",
                id=video_id,
                maxResults=1,
            )
            .execute()
        )
        items = response.get("items", [])
        if not items:
            raise RuntimeError(f"Video not found for metrics snapshot: {video_id}")
        return items[0]

    def monitor_until_terminal(
        self,
        profile: ChannelProfile,
        video_id: str,
        poll_seconds: int = 30,
        max_attempts: int = 20,
    ) -> MonitorResult:
        latest: Dict = {}
        decision = self.checker.evaluate_video_state({})
        for _ in range(max_attempts):
            latest = self.fetch_video_resource(profile, video_id)
            decision = self.checker.evaluate_video_state(latest)
            if decision.terminal_status:
                break
            time.sleep(poll_seconds)
        return MonitorResult(video_id=video_id, latest_resource=latest, decision=decision)
