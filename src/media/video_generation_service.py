from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from src.config.models import ModelProviderCredential
from src.media.providers import (
    KlingVideoProvider,
    ProviderVideoConfig,
    ProviderVideoRequest,
    SoraVideoProvider,
    SeedanceVideoProvider,
    VeoVideoProvider,
    VideoGenerationProvider,
)


@dataclass(frozen=True)
class VideoGenerationRequest:
    request_id: str
    provider: str
    model: str
    prompt: str
    duration_seconds: int
    aspect_ratio: str
    include_audio: bool = True


@dataclass
class VideoGenerationArtifact:
    output_path: Path
    provider: str
    model: str
    task_id: str
    mode: str
    duration_seconds: int
    latency_seconds: float
    notes: List[str] = field(default_factory=list)


PROVIDER_REGISTRY = {
    "kling_ai": KlingVideoProvider,
    "seedance_2": SeedanceVideoProvider,
    "veo3": VeoVideoProvider,
    "sora_api": SoraVideoProvider,
}


class VideoGenerationService:
    def __init__(
        self,
        output_dir: Path,
        credentials: Dict[str, ModelProviderCredential],
        poll_interval_seconds: int = 10,
        max_poll_attempts: int = 24,
    ) -> None:
        self.output_dir = output_dir
        self.credentials = credentials
        self.poll_interval_seconds = poll_interval_seconds
        self.max_poll_attempts = max_poll_attempts
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_with_fallback(self, request: VideoGenerationRequest) -> VideoGenerationArtifact:
        start = time.monotonic()
        try:
            artifact = self.generate(request)
            return artifact
        except Exception as exc:
            fallback_path = self.output_dir / f"{request.request_id}_{request.provider}_fallback.mp4"
            self._create_local_fallback_clip(
                destination=fallback_path,
                duration_seconds=max(6, min(request.duration_seconds, 20)),
                aspect_ratio=request.aspect_ratio,
            )
            latency = time.monotonic() - start
            return VideoGenerationArtifact(
                output_path=fallback_path,
                provider=request.provider,
                model=request.model,
                task_id="local_fallback",
                mode="local_fallback",
                duration_seconds=max(6, min(request.duration_seconds, 20)),
                latency_seconds=latency,
                notes=[f"provider_generation_failed: {exc}"],
            )

    def generate(self, request: VideoGenerationRequest) -> VideoGenerationArtifact:
        provider = self._build_provider(request.provider, request.model)
        if provider is None:
            raise ValueError(f"No provider adapter available for {request.provider}")

        start = time.monotonic()
        provider_request = ProviderVideoRequest(
            prompt=request.prompt,
            duration_seconds=request.duration_seconds,
            aspect_ratio=request.aspect_ratio,
            include_audio=request.include_audio,
            metadata={"request_id": request.request_id},
        )
        job = provider.submit(provider_request)
        notes = [f"submitted_task_id={job.task_id}"]
        terminal_status = ""
        for _ in range(self.max_poll_attempts):
            current = provider.poll(job.task_id)
            terminal_status = current.status.lower()
            if terminal_status in {"completed", "succeeded", "success", "done", "finished", "ready"}:
                job = current
                break
            if terminal_status in {"failed", "error", "cancelled", "rejected"}:
                raise RuntimeError(f"video generation failed with status={terminal_status}")
            time.sleep(self.poll_interval_seconds)
        else:
            raise TimeoutError(f"video generation timed out for task_id={job.task_id}")

        output_path = self.output_dir / f"{request.request_id}_{request.provider}.mp4"
        provider.download(job, output_path)
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("downloaded video artifact is missing or empty")

        latency = time.monotonic() - start
        notes.append(f"terminal_status={terminal_status}")
        return VideoGenerationArtifact(
            output_path=output_path,
            provider=request.provider,
            model=request.model,
            task_id=job.task_id,
            mode="provider_api",
            duration_seconds=request.duration_seconds,
            latency_seconds=latency,
            notes=notes,
        )

    def _build_provider(self, provider_name: str, selected_model: str) -> VideoGenerationProvider | None:
        provider_cls = PROVIDER_REGISTRY.get(provider_name)
        cred = self.credentials.get(provider_name)
        if provider_cls is None or cred is None or not cred.api_key:
            return None
        config = ProviderVideoConfig(
            api_key=cred.api_key,
            base_url=cred.base_url,
            model=selected_model or cred.model,
        )
        return provider_cls(config)

    def _create_local_fallback_clip(
        self,
        destination: Path,
        duration_seconds: int,
        aspect_ratio: str,
    ) -> None:
        resolution = "1280x720"
        if aspect_ratio == "9:16":
            resolution = "720x1280"
        elif aspect_ratio == "1:1":
            resolution = "960x960"

        destination.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s={resolution}:d={duration_seconds}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={duration_seconds}",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(destination),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except Exception:
            # Last resort: non-empty artifact so downstream diagnostics can continue.
            destination.write_bytes(b"local-fallback-video")
