from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
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


class KlingVideoProvider(VideoGenerationProvider):
    provider_id = "kling_ai"

    def __init__(self, config: ProviderVideoConfig) -> None:
        self.config = config

    def submit(self, request: ProviderVideoRequest) -> ProviderVideoJob:
        base_url = self.config.base_url.rstrip("/") or "https://api.kling.ai"
        url = f"{base_url}/v1/videos/text2video"
        requested_duration = max(int(request.duration_seconds), 5)
        normalized_duration = 10 if requested_duration >= 8 else 5
        payload = {
            "model": self.config.model,
            "prompt": request.prompt,
            "duration": normalized_duration,
            "aspect_ratio": request.aspect_ratio,
            "audio": request.include_audio,
        }
        data = post_json(url, payload, headers=self._headers(), timeout_seconds=self.config.timeout_seconds)
        task_id = self._extract_task_id(data)
        return ProviderVideoJob(task_id=task_id, status="queued", raw_response=data)

    def poll(self, task_id: str) -> ProviderVideoJob:
        base_url = self.config.base_url.rstrip("/") or "https://api.kling.ai"
        url = f"{base_url}/v1/videos/{task_id}"
        data = get_json(url, headers=self._headers(), timeout_seconds=self.config.timeout_seconds)
        status = self._extract_status(data)
        output_url = self._extract_output_url(data)
        return ProviderVideoJob(task_id=task_id, status=status, raw_response=data, output_url=output_url)

    def download(self, job: ProviderVideoJob, destination: Path) -> Path:
        output_url = job.output_url or self._extract_output_url(job.raw_response)
        if not output_url:
            raise ValueError("Kling output URL missing.")
        return download_to_file(
            output_url,
            destination,
            headers={"Authorization": f"Bearer {self._auth_token()}"},
            timeout_seconds=120,
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._auth_token()}",
            "Content-Type": "application/json",
        }

    def _auth_token(self) -> str:
        access_key = self.config.api_key.strip()
        secret_key = self.config.secret_key.strip()
        if not secret_key:
            return access_key

        now = int(time.time())
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "iss": access_key,
            "exp": now + 1800,
            "nbf": now - 5,
        }
        encoded_header = self._base64url_json(header)
        encoded_payload = self._base64url_json(payload)
        signing_input = f"{encoded_header}.{encoded_payload}"
        signature = hmac.new(
            secret_key.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        encoded_signature = self._base64url_bytes(signature)
        return f"{signing_input}.{encoded_signature}"

    @staticmethod
    def _base64url_json(blob: Dict[str, Any]) -> str:
        raw = json.dumps(blob, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return KlingVideoProvider._base64url_bytes(raw)

    @staticmethod
    def _base64url_bytes(blob: bytes) -> str:
        return base64.urlsafe_b64encode(blob).rstrip(b"=").decode("ascii")

    @staticmethod
    def _extract_task_id(data: Dict[str, Any]) -> str:
        candidates = [
            data.get("task_id"),
            data.get("id"),
            data.get("taskId"),
            read_nested(data, "data", "task_id"),
            read_nested(data, "data", "id"),
            read_nested(data, "result", "task_id"),
        ]
        for value in candidates:
            if value:
                return str(value)
        raise ValueError("Kling submit response missing task id.")

    @staticmethod
    def _extract_status(data: Dict[str, Any]) -> str:
        candidates = [
            data.get("status"),
            read_nested(data, "data", "status"),
            read_nested(data, "result", "status"),
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
            read_nested(data, "result", "video_url"),
            read_nested(data, "result", "url"),
        ]
        for value in candidates:
            if value:
                return str(value)
        return ""
