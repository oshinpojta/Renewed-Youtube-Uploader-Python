from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.media.validation import MediaValidationResult
from src.media.video_generation_service import VideoGenerationRequest, VideoGenerationService


class VideoGenerationServiceTests(unittest.TestCase):
    def test_generate_with_fallback_produces_non_empty_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = VideoGenerationService(output_dir=Path(tmpdir), credentials={})
            request = VideoGenerationRequest(
                request_id="req_test_001",
                provider="kling_ai",
                model="kling-v2.6-pro",
                prompt="A quick explainer with clean visuals",
                duration_seconds=8,
                aspect_ratio="9:16",
                include_audio=True,
            )

            def _fake_local_fallback(destination: Path, duration_seconds: int, aspect_ratio: str) -> None:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(
                    f"fallback duration={duration_seconds} aspect={aspect_ratio}".encode("utf-8")
                )

            with patch.object(
                VideoGenerationService,
                "_create_local_fallback_clip",
                side_effect=_fake_local_fallback,
            ):
                with patch(
                    "src.media.video_generation_service.validate_rendered_media",
                    return_value=MediaValidationResult(
                        is_valid=True,
                        has_video=True,
                        has_audio=True,
                        duration_seconds=8.0,
                    ),
                ):
                    artifact = service.generate_with_fallback(request)

            self.assertEqual(artifact.mode, "local_fallback")
            self.assertTrue(artifact.output_path.exists())
            self.assertGreater(artifact.output_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
