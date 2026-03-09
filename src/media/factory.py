from __future__ import annotations

import re
import shutil
import subprocess
from datetime import timezone
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.config.models import ContentBrief, GeneratedScript, RenderedMedia
from src.media.model_router import ModelProviderRouter
from src.media.video_generation_service import VideoGenerationRequest, VideoGenerationService


@dataclass
class MediaFactoryConfig:
    workspace_root: Path
    output_dir: Path
    generated_videos_dir: Optional[Path] = None
    default_duration_seconds: int = 55
    enable_ffmpeg: bool = True
    enable_model_generation: bool = True
    model_router: Optional[ModelProviderRouter] = None
    video_generation_service: Optional[VideoGenerationService] = None


class MediaFactory:
    def __init__(self, config: MediaFactoryConfig) -> None:
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.generated_videos_dir = self.config.generated_videos_dir or (
            self.config.workspace_root / "generated_videos"
        )
        self.generated_videos_dir.mkdir(parents=True, exist_ok=True)

    def render(
        self,
        brief: ContentBrief,
        source_clips: List[Path] | None = None,
        generated_script: GeneratedScript | None = None,
    ) -> RenderedMedia:
        source_clips = source_clips or []
        output_path = self.config.output_dir / f"{brief.brief_id}.mp4"
        contains_synthetic = "ai" in brief.niche_id or "ghost_lore" in brief.niche_id
        generation_provider = "none"
        generation_model = ""
        generation_mode = "placeholder"
        generation_notes: List[str] = []
        generation_task_id = ""
        render_latency_seconds = 0.0

        requested_duration = self.config.default_duration_seconds
        require_audio = True
        if generated_script and generated_script.scenes:
            requested_duration = sum(scene.duration_seconds for scene in generated_script.scenes)
            requested_duration = max(8, min(requested_duration, 60))
            require_audio = generated_script.requires_audio

        if self.config.enable_ffmpeg and source_clips:
            generation_provider = "source_clips"
            generation_model = "ffmpeg_copy"
            output_path = self._build_sorted_output_path(
                brief=brief,
                provider=generation_provider,
                model=generation_model,
            )
            concat_file = self.config.output_dir / f"{brief.brief_id}_concat.txt"
            concat_lines = [f"file '{clip.as_posix()}'" for clip in source_clips]
            concat_file.write_text("\n".join(concat_lines), encoding="utf-8")
            try:
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-c",
                    "copy",
                    str(output_path),
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                duration = self._probe_duration(output_path) or self.config.default_duration_seconds
                generation_mode = "ffmpeg_concat"
            except Exception as exc:
                output_path.unlink(missing_ok=True)
                duration = requested_duration
                generation_mode = "render_failed"
                generation_notes = [f"ffmpeg_concat_failed: {exc}"]
            finally:
                concat_file.unlink(missing_ok=True)
        else:
            prompt = self._build_generation_prompt(brief, generated_script)
            if (
                self.config.enable_model_generation
                and self.config.model_router
                and self.config.video_generation_service
            ):
                selection_duration = requested_duration
                selection_prefix_notes: List[str] = []
                selection = self.config.model_router.select_for_niche(
                    niche_id=brief.niche_id,
                    duration_seconds=selection_duration,
                    require_audio=require_audio,
                )
                if selection.provider == "none" and selection_duration > 10:
                    for capped_duration in (30, 20, 15, 10, 8):
                        if capped_duration >= selection_duration:
                            continue
                        capped_selection = self.config.model_router.select_for_niche(
                            niche_id=brief.niche_id,
                            duration_seconds=capped_duration,
                            require_audio=require_audio,
                        )
                        if capped_selection.provider != "none":
                            selection = capped_selection
                            selection_prefix_notes.append(
                                f"duration_clamped_for_provider_limits:{selection_duration}s->{capped_duration}s"
                            )
                            selection_duration = capped_duration
                            break
                generation_provider = selection.provider
                generation_model = selection.model
                try:
                    request = VideoGenerationRequest(
                        request_id=brief.brief_id,
                        provider=selection.provider,
                        model=selection.model,
                        prompt=prompt,
                        duration_seconds=selection_duration,
                        aspect_ratio="9:16"
                        if "shorts" in " ".join(brief.target_formats).lower()
                        else "16:9",
                        include_audio=require_audio,
                    )
                    artifact = self.config.video_generation_service.generate_with_fallback(request)
                    generation_provider = artifact.provider
                    generation_model = artifact.model
                    output_path = self._build_sorted_output_path(
                        brief=brief,
                        provider=artifact.provider or selection.provider,
                        model=artifact.model or selection.model or artifact.mode,
                    )
                    self._move_output_artifact(artifact.output_path, output_path)
                    generation_mode = artifact.mode
                    generation_task_id = artifact.task_id
                    render_latency_seconds = artifact.latency_seconds
                    generation_notes = selection_prefix_notes + selection.notes + artifact.notes
                    duration = artifact.duration_seconds
                except Exception as exc:
                    output_path = self._build_sorted_output_path(
                        brief=brief,
                        provider=generation_provider,
                        model=generation_model or "render_failed",
                    )
                    output_path.unlink(missing_ok=True)
                    duration = requested_duration
                    generation_mode = "render_failed"
                    generation_notes = selection_prefix_notes + selection.notes + [
                        f"model_generation_failed: {exc}"
                    ]
            else:
                output_path = self._build_sorted_output_path(
                    brief=brief,
                    provider="none",
                    model="render_failed",
                )
                output_path.unlink(missing_ok=True)
                duration = requested_duration
                generation_mode = "render_failed"
                generation_notes = [
                    "media generation is disabled or model service configuration is incomplete"
                ]

        return RenderedMedia(
            media_path=str(output_path),
            duration_seconds=duration,
            aspect_ratio="9:16" if "shorts" in " ".join(brief.target_formats).lower() else "16:9",
            contains_synthetic_media=contains_synthetic,
            source_credits=brief.evidence_links,
            generation_provider=generation_provider,
            generation_model=generation_model,
            generation_mode=generation_mode,
            generation_notes=generation_notes,
            generation_task_id=generation_task_id,
            render_latency_seconds=render_latency_seconds,
        )

    @staticmethod
    def _slug_token(value: str, fallback: str) -> str:
        token = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
        return token or fallback

    @staticmethod
    def _move_output_artifact(source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source == destination:
            return
        shutil.move(str(source), str(destination))

    def _build_sorted_output_path(self, brief: ContentBrief, provider: str, model: str) -> Path:
        timestamp_token = brief.generated_at_utc.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        channel_token = self._slug_token(
            brief.channel_name or brief.channel_profile_id,
            "channel",
        )
        niche_token = self._slug_token(brief.niche_id, "niche")
        provider_token = self._slug_token(provider, "unknown_provider")
        model_token = self._slug_token(model, "unknown_model")
        filename = (
            f"{channel_token}__{niche_token}__{brief.brief_id}_{timestamp_token}.mp4"
        )
        destination = self.generated_videos_dir / provider_token / model_token / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        return destination

    @staticmethod
    def _probe_duration(path: Path) -> int | None:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
        try:
            output = subprocess.run(cmd, check=True, capture_output=True, text=True)
        except Exception:
            return None
        try:
            return int(float(output.stdout.strip()))
        except ValueError:
            return None

    @staticmethod
    def _build_generation_prompt(brief: ContentBrief, generated_script: GeneratedScript | None) -> str:
        if generated_script and generated_script.scenes:
            scene_lines = []
            for scene in generated_script.scenes:
                scene_lines.append(
                    f"- {scene.scene_id}: visual={scene.visual_prompt}; narration={scene.narration}"
                )
            scenes_blob = "\n".join(scene_lines)
            return (
                f"Create a coherent short video for title: {generated_script.title}\n"
                f"Hook: {generated_script.hook}\n"
                f"Scenes:\n{scenes_blob}\n"
                "Maintain continuity and include clear spoken narration."
            )
        return (
            f"Create a short explanatory video titled '{brief.working_title}'. "
            f"Topic focus: {brief.seed_keyword}. "
            f"Use this hook: {brief.hook}."
        )
