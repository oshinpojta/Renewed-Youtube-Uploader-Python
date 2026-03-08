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


class SeedanceVideoProvider(VideoGenerationProvider):
    provider_id = "seedance_2"

    def __init__(self, config: ProviderVideoConfig) -> None:
        self.config = config

    def submit(self, request: ProviderVideoRequest) -> ProviderVideoJob:
        base_url = self.config.base_url.rstrip("/") or "https://api.seedance.ai"
        url = f"{base_url}/v1/videos/generate"
        payload = {
            "model": self.config.model,
            "prompt": request.prompt,
            "duration_seconds": min(max(request.duration_seconds, 4), 15),
            "aspect_ratio": request.aspect_ratio,
            "audio": request.include_audio,
        }
        data = post_json(url, payload, headers=self._headers(), timeout_seconds=self.config.timeout_seconds)
        task_id = self._extract_task_id(data)
        return ProviderVideoJob(task_id=task_id, status="queued", raw_response=data)

    def poll(self, task_id: str) -> ProviderVideoJob:
        base_url = self.config.base_url.rstrip("/") or "https://api.seedance.ai"
        url = f"{base_url}/v1/videos/{task_id}"
        data = get_json(url, headers=self._headers(), timeout_seconds=self.config.timeout_seconds)
        status = self._extract_status(data)
        output_url = self._extract_output_url(data)
        return ProviderVideoJob(task_id=task_id, status=status, raw_response=data, output_url=output_url)

    def download(self, job: ProviderVideoJob, destination: Path) -> Path:
        output_url = job.output_url or self._extract_output_url(job.raw_response)
        if not output_url:
            raise ValueError("Seedance output URL missing.")
        return download_to_file(
            output_url,
            destination,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout_seconds=120,
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _extract_task_id(data: Dict[str, Any]) -> str:
        candidates = [
            data.get("task_id"),
            data.get("id"),
            data.get("taskId"),
            read_nested(data, "data", "task_id"),
            read_nested(data, "data", "id"),
            read_nested(data, "job", "id"),
        ]
        for value in candidates:
            if value:
                return str(value)
        raise ValueError("Seedance submit response missing task id.")

    @staticmethod
    def _extract_status(data: Dict[str, Any]) -> str:
        candidates = [
            data.get("status"),
            read_nested(data, "data", "status"),
            read_nested(data, "job", "status"),
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
            read_nested(data, "data", "video_url"),
            read_nested(data, "data", "output_url"),
            read_nested(data, "result", "url"),
            read_nested(data, "job", "video_url"),
        ]
        for value in candidates:
            if value:
                return str(value)
        return ""
