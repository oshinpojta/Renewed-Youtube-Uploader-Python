from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import requests

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


class SoraVideoProvider(VideoGenerationProvider):
    provider_id = "sora_api"

    def __init__(self, config: ProviderVideoConfig) -> None:
        self.config = config

    def submit(self, request: ProviderVideoRequest) -> ProviderVideoJob:
        base_url = self.config.base_url.rstrip("/") or "https://api.openai.com"
        url = f"{base_url}/v1/videos"
        payload = {
            "model": self.config.model or "sora-2",
            "prompt": request.prompt,
            "seconds": str(min(max(request.duration_seconds, 4), 20)),
            "size": self._size_for_aspect(request.aspect_ratio),
        }
        data = post_json(url, payload, headers=self._headers(), timeout_seconds=self.config.timeout_seconds)
        task_id = self._extract_task_id(data)
        status = str(data.get("status", "queued")).lower()
        return ProviderVideoJob(task_id=task_id, status=status, raw_response=data)

    def poll(self, task_id: str) -> ProviderVideoJob:
        base_url = self.config.base_url.rstrip("/") or "https://api.openai.com"
        url = f"{base_url}/v1/videos/{task_id}"
        data = get_json(url, headers=self._headers(), timeout_seconds=self.config.timeout_seconds)
        status = str(data.get("status", "unknown")).lower()
        output_url = self._extract_output_url(data)
        return ProviderVideoJob(task_id=task_id, status=status, raw_response=data, output_url=output_url)

    def download(self, job: ProviderVideoJob, destination: Path) -> Path:
        output_url = job.output_url or self._extract_output_url(job.raw_response)
        if output_url:
            return download_to_file(output_url, destination, headers=self._headers(), timeout_seconds=180)

        base_url = self.config.base_url.rstrip("/") or "https://api.openai.com"
        url = f"{base_url}/v1/videos/{job.task_id}/content"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, headers=self._headers(), timeout=180, stream=True) as response:
            response.raise_for_status()
            with destination.open("wb") as fileptr:
                for chunk in response.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        fileptr.write(chunk)
        return destination

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _size_for_aspect(aspect_ratio: str) -> str:
        ratio = aspect_ratio.strip()
        if ratio == "9:16":
            return "720x1280"
        if ratio == "1:1":
            return "1024x1024"
        return "1280x720"

    @staticmethod
    def _extract_task_id(data: Dict[str, Any]) -> str:
        candidates = [
            data.get("id"),
            data.get("video_id"),
            read_nested(data, "data", "id"),
        ]
        for value in candidates:
            if value:
                return str(value)
        raise ValueError("Sora submit response missing task id.")

    @staticmethod
    def _extract_output_url(data: Dict[str, Any]) -> str:
        candidates = [
            data.get("output_url"),
            data.get("video_url"),
            read_nested(data, "data", "output_url"),
            read_nested(data, "data", "video_url"),
        ]
        for value in candidates:
            if value:
                return str(value)
        return ""
