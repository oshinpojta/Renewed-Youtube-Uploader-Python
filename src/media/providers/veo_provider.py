from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from src.media.providers.base import (
    ProviderVideoConfig,
    ProviderVideoJob,
    ProviderVideoRequest,
    VideoGenerationProvider,
    download_to_file,
    get_json,
    post_json,
    read_nested,
)


class VeoVideoProvider(VideoGenerationProvider):
    provider_id = "veo3"

    def __init__(self, config: ProviderVideoConfig) -> None:
        self.config = config

    def submit(self, request: ProviderVideoRequest) -> ProviderVideoJob:
        base_url = self.config.base_url.rstrip("/") or "https://generativelanguage.googleapis.com"
        url = f"{base_url}/v1/videos/generate"
        payload = {
            "model": self.config.model,
            "prompt": request.prompt,
            "duration_seconds": min(max(request.duration_seconds, 4), 8),
            "aspect_ratio": request.aspect_ratio,
            "audio": request.include_audio,
        }
        data = post_json(url, payload, headers=self._headers(), timeout_seconds=self.config.timeout_seconds)
        task_id = self._extract_task_id(data)
        return ProviderVideoJob(task_id=task_id, status="queued", raw_response=data)

    def poll(self, task_id: str) -> ProviderVideoJob:
        base_url = self.config.base_url.rstrip("/") or "https://generativelanguage.googleapis.com"
        if task_id.startswith("operations/"):
            url = f"{base_url}/{task_id}"
        else:
            url = f"{base_url}/v1/videos/{task_id}"
        data = get_json(url, headers=self._headers(), timeout_seconds=self.config.timeout_seconds)
        status = self._extract_status(data)
        output_url = self._extract_output_url(data)
        return ProviderVideoJob(task_id=task_id, status=status, raw_response=data, output_url=output_url)

    def download(self, job: ProviderVideoJob, destination: Path) -> Path:
        output_url = job.output_url or self._extract_output_url(job.raw_response)
        if not output_url:
            raise ValueError("Veo output URL missing.")
        return download_to_file(
            output_url,
            destination,
            headers=self._headers(),
            timeout_seconds=120,
        )

    def _headers(self) -> Dict[str, str]:
        # Supports both bearer token style and API key-in-header style gateways.
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
            headers["x-goog-api-key"] = self.config.api_key
        return headers

    @staticmethod
    def _extract_task_id(data: Dict[str, Any]) -> str:
        candidates = [
            data.get("task_id"),
            data.get("id"),
            data.get("name"),
            read_nested(data, "operation", "name"),
            read_nested(data, "data", "task_id"),
        ]
        for value in candidates:
            if value:
                return str(value)
        raise ValueError("Veo submit response missing task id.")

    @staticmethod
    def _extract_status(data: Dict[str, Any]) -> str:
        if data.get("done") is True:
            return "completed"
        candidates = [
            data.get("status"),
            read_nested(data, "metadata", "state"),
            read_nested(data, "data", "status"),
        ]
        for value in candidates:
            if value:
                return str(value).lower()
        return "unknown"

    @staticmethod
    def _extract_output_url(data: Dict[str, Any]) -> str:
        candidates = [
            data.get("video_url"),
            data.get("output_url"),
            read_nested(data, "response", "videoUri"),
            read_nested(data, "response", "videos", "0", "uri"),
            read_nested(data, "data", "video_url"),
            read_nested(data, "result", "url"),
        ]
        for value in candidates:
            if value:
                return str(value)
        # nested list path support:
        response_videos = read_nested(data, "response", "videos")
        if isinstance(response_videos, list) and response_videos:
            first = response_videos[0]
            if isinstance(first, dict):
                uri = first.get("uri") or first.get("videoUrl")
                if uri:
                    return str(uri)
        return ""
