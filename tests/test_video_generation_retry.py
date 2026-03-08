from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.media.providers.base import ProviderVideoJob, ProviderVideoRequest, VideoGenerationProvider
from src.media.video_generation_service import VideoGenerationRequest, VideoGenerationService


class _FakeProvider(VideoGenerationProvider):
    provider_id = "fake"

    def __init__(self) -> None:
        self.poll_calls = 0

    def submit(self, request: ProviderVideoRequest) -> ProviderVideoJob:
        return ProviderVideoJob(task_id="task_1", status="queued", raw_response={})

    def poll(self, task_id: str) -> ProviderVideoJob:
        self.poll_calls += 1
        status = "completed" if self.poll_calls >= 2 else "queued"
        return ProviderVideoJob(task_id=task_id, status=status, raw_response={"status": status})

    def download(self, job: ProviderVideoJob, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"fake-video")
        return destination


class _ServiceWithFakeProvider(VideoGenerationService):
    def __init__(self, output_dir: Path, fake_provider: _FakeProvider) -> None:
        super().__init__(output_dir=output_dir, credentials={}, poll_interval_seconds=0, max_poll_attempts=3)
        self.fake_provider = fake_provider

    def _build_provider(self, provider_name: str, selected_model: str):  # type: ignore[override]
        return self.fake_provider


class VideoGenerationRetryTests(unittest.TestCase):
    def test_generate_retries_poll_until_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_provider = _FakeProvider()
            service = _ServiceWithFakeProvider(Path(tmpdir), fake_provider)
            request = VideoGenerationRequest(
                request_id="req_retry",
                provider="kling_ai",
                model="kling-v2.6-pro",
                prompt="Explain workflow",
                duration_seconds=8,
                aspect_ratio="9:16",
            )
            artifact = service.generate(request)

            self.assertEqual(artifact.mode, "provider_api")
            self.assertGreaterEqual(fake_provider.poll_calls, 2)
            self.assertTrue(artifact.output_path.exists())


if __name__ == "__main__":
    unittest.main()
