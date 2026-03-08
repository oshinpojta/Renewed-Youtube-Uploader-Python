from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from src.config.models import ChannelProfile, UploadJob
from src.youtube.auth import YouTubeAuthManager
from src.youtube.channel_onboarding import handle_youtube_signup_required


@dataclass
class UploadResult:
    video_id: str
    upload_response: Dict


class YouTubeUploadError(RuntimeError):
    def __init__(self, message: str, requires_channel_onboarding: bool = False) -> None:
        super().__init__(message)
        self.requires_channel_onboarding = requires_channel_onboarding


class YouTubeUploader:
    def __init__(self, auth_manager: YouTubeAuthManager) -> None:
        self.auth_manager = auth_manager

    def upload_private(self, profile: ChannelProfile, job: UploadJob) -> UploadResult:
        service = self.auth_manager.build_service(profile)
        metadata = job.metadata
        body = {
            "snippet": {
                "title": metadata.get("title", job.brief.working_title),
                "description": metadata.get("description", ""),
                "tags": metadata.get("tags", []),
                "categoryId": metadata.get("category_id", "22"),
            },
            "status": {
                "privacyStatus": "private",
                "publishAt": job.scheduled_publish_at_utc.replace(tzinfo=timezone.utc).isoformat(),
                "selfDeclaredMadeForKids": False,
                "containsSyntheticMedia": job.media.contains_synthetic_media,
            },
        }
        media = MediaFileUpload(job.media.media_path, chunksize=-1, resumable=True, mimetype="video/*")
        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
            notifySubscribers=False,
        )
        try:
            response = request.execute()
        except HttpError as exc:
            onboarding = handle_youtube_signup_required(str(exc))
            raise YouTubeUploadError(
                message=f"Upload failed: {exc}",
                requires_channel_onboarding=onboarding.requires_user_action,
            ) from exc

        return UploadResult(video_id=response["id"], upload_response=response)

    def update_schedule(
        self,
        profile: ChannelProfile,
        video_id: str,
        publish_at_utc: datetime,
        contains_synthetic_media: bool,
    ) -> Dict:
        service = self.auth_manager.build_service(profile)
        body = {
            "id": video_id,
            "status": {
                "privacyStatus": "private",
                "publishAt": publish_at_utc.replace(tzinfo=timezone.utc).isoformat(),
                "containsSyntheticMedia": contains_synthetic_media,
                "selfDeclaredMadeForKids": False,
            },
        }
        return service.videos().update(part="status", body=body).execute()
