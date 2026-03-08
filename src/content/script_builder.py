from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict, List

from src.config.models import ContentBrief, GeneratedScript, ScriptScene
from src.content.providers.base import try_parse_json_block
from src.content.story_builder import StoryBuildResult
from src.content.text_router import TextGenerationRouter


@dataclass
class ScriptBuildInput:
    brief: ContentBrief
    story: StoryBuildResult
    citations: List[str]
    citation_snippets: List[str]


class ScriptBuilder:
    def __init__(self, text_router: TextGenerationRouter) -> None:
        self.text_router = text_router

    def build(self, data: ScriptBuildInput) -> GeneratedScript:
        prompt = self._build_prompt(data)
        routed = self.text_router.generate_for_niche(
            niche_id=data.brief.niche_id,
            prompt=prompt,
            metadata={
                "title": data.brief.working_title,
                "seed_keyword": data.brief.seed_keyword,
            },
        )
        payload = try_parse_json_block(routed.result.text) or {}
        scenes = self._parse_scenes(payload, data.brief)
        return GeneratedScript(
            script_id=f"script_{uuid.uuid4().hex[:12]}",
            channel_profile_id=data.brief.channel_profile_id,
            niche_id=data.brief.niche_id,
            title=str(payload.get("title", data.brief.working_title)).strip() or data.brief.working_title,
            hook=str(payload.get("hook", data.brief.hook)).strip() or data.brief.hook,
            scenes=scenes,
            characters=data.story.characters,
            story_arc=data.story.story_arc,
            citations=list(dict.fromkeys(data.citations)),
            text_provider=routed.result.provider,
            generation_notes=data.story.generation_notes + routed.result.notes,
            requires_audio=True,
        )

    @staticmethod
    def _build_prompt(data: ScriptBuildInput) -> str:
        citations = "\n".join(f"- {line}" for line in data.citation_snippets[:4]) or "- no snippets"
        char_lines = "\n".join(f"- {c.name}: {c.role} ({c.personality})" for c in data.story.characters)
        return (
            "Create a JSON YouTube script with fields: title, hook, scenes.\n"
            "scenes must be an array of objects with visual_prompt, narration, duration_seconds, camera_direction, audio_direction.\n"
            "Use 4 to 6 scenes. Every narration must be one short paragraph.\n"
            "Avoid disallowed or absolutist claims.\n\n"
            f"Niche: {data.brief.niche_id}\n"
            f"Working title: {data.brief.working_title}\n"
            f"Story setting: {data.story.story_arc.setting}\n"
            f"Conflict: {data.story.story_arc.conflict}\n"
            f"Resolution: {data.story.story_arc.resolution}\n"
            f"Characters:\n{char_lines}\n"
            f"Citation notes:\n{citations}\n"
        )

    @staticmethod
    def _parse_scenes(payload: Dict, brief: ContentBrief) -> List[ScriptScene]:
        raw = payload.get("scenes", [])
        scenes: List[ScriptScene] = []
        if isinstance(raw, list):
            for index, item in enumerate(raw[:6], start=1):
                if not isinstance(item, dict):
                    continue
                narration = str(item.get("narration", "")).strip()
                visual_prompt = str(item.get("visual_prompt", "")).strip()
                if not narration:
                    continue
                if not visual_prompt:
                    visual_prompt = f"Visual sequence for {brief.seed_keyword} scene {index}"
                duration = int(item.get("duration_seconds", 10) or 10)
                duration = max(5, min(duration, 25))
                scenes.append(
                    ScriptScene(
                        scene_id=f"scene_{index}",
                        visual_prompt=visual_prompt,
                        narration=narration,
                        duration_seconds=duration,
                        camera_direction=str(item.get("camera_direction", "steady close-up")).strip(),
                        audio_direction=str(item.get("audio_direction", "subtle background ambience")).strip(),
                    )
                )
        if scenes:
            return scenes
        return ScriptBuilder._fallback_scenes(brief)

    @staticmethod
    def _fallback_scenes(brief: ContentBrief) -> List[ScriptScene]:
        seed = brief.seed_keyword
        return [
            ScriptScene(
                scene_id="scene_1",
                visual_prompt=f"High-energy opener introducing {seed}",
                narration=f"Here is why {seed} matters right now and why people are talking about it.",
                duration_seconds=8,
                camera_direction="fast intro zoom",
                audio_direction="energetic intro hit",
            ),
            ScriptScene(
                scene_id="scene_2",
                visual_prompt=f"Context board with references around {seed}",
                narration="Let's separate facts from assumptions using source-backed context.",
                duration_seconds=10,
                camera_direction="split-screen explainer",
                audio_direction="neutral explanatory tone",
            ),
            ScriptScene(
                scene_id="scene_3",
                visual_prompt=f"Practical takeaway card for {seed}",
                narration="Use this simple checklist before believing or sharing the next claim.",
                duration_seconds=10,
                camera_direction="clean text overlay",
                audio_direction="light beat under voice",
            ),
            ScriptScene(
                scene_id="scene_4",
                visual_prompt="Call-to-action with next episode teaser",
                narration="If this helped, save it and tell me which topic should be decoded next.",
                duration_seconds=8,
                camera_direction="center framing",
                audio_direction="soft outro",
            ),
        ]
