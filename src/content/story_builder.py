from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import List

from src.config.models import CharacterProfile, ContentBrief, StoryArc
from src.content.providers.base import try_parse_json_block
from src.content.text_router import TextGenerationRouter


@dataclass
class StoryBuildResult:
    story_id: str
    characters: List[CharacterProfile]
    story_arc: StoryArc
    text_provider: str
    generation_notes: List[str]


class StoryBuilder:
    def __init__(self, text_router: TextGenerationRouter) -> None:
        self.text_router = text_router

    def build_story(
        self,
        brief: ContentBrief,
        citation_summaries: List[str] | None = None,
    ) -> StoryBuildResult:
        citation_summaries = citation_summaries or []
        prompt = self._build_prompt(brief, citation_summaries)
        routed = self.text_router.generate_for_niche(
            niche_id=brief.niche_id,
            prompt=prompt,
            metadata={
                "title": brief.working_title,
                "seed_keyword": brief.seed_keyword,
            },
        )
        payload = try_parse_json_block(routed.result.text) or {}
        characters = self._parse_characters(payload)
        story_arc = self._parse_story_arc(payload, brief.seed_keyword)
        return StoryBuildResult(
            story_id=f"story_{uuid.uuid4().hex[:12]}",
            characters=characters,
            story_arc=story_arc,
            text_provider=routed.result.provider,
            generation_notes=routed.result.notes,
        )

    @staticmethod
    def _build_prompt(brief: ContentBrief, citations: List[str]) -> str:
        source_lines = "\n".join(f"- {line}" for line in citations[:4]) or "- no external citations"
        outline_lines = "\n".join(f"- {line}" for line in brief.outline)
        return (
            "You are a YouTube short-form story architect.\n"
            "Return strict JSON with keys: characters, story_arc.\n"
            "characters must be an array of objects with name, role, personality, motivation.\n"
            "story_arc must have setting, inciting_incident, conflict, resolution, moral.\n\n"
            f"Niche: {brief.niche_id}\n"
            f"Title: {brief.working_title}\n"
            f"Hook: {brief.hook}\n"
            f"Outline:\n{outline_lines}\n"
            f"Evidence hints:\n{source_lines}\n"
            "Keep content compliant, respectful, and practical."
        )

    @staticmethod
    def _parse_characters(payload: dict) -> List[CharacterProfile]:
        raw_items = payload.get("characters", [])
        output: List[CharacterProfile] = []
        if isinstance(raw_items, list):
            for item in raw_items[:3]:
                if not isinstance(item, dict):
                    continue
                output.append(
                    CharacterProfile(
                        name=str(item.get("name", "Guide")).strip() or "Guide",
                        role=str(item.get("role", "Narrator")).strip() or "Narrator",
                        personality=str(item.get("personality", "Clear and curious")).strip()
                        or "Clear and curious",
                        motivation=str(item.get("motivation", "Explain the topic responsibly")).strip()
                        or "Explain the topic responsibly",
                    )
                )
        if output:
            return output
        return [
            CharacterProfile(
                name="Guide",
                role="Narrator",
                personality="Clear and concise",
                motivation="Deliver useful context quickly",
            ),
            CharacterProfile(
                name="Learner",
                role="Audience proxy",
                personality="Curious and practical",
                motivation="Understand the topic and apply it",
            ),
        ]

    @staticmethod
    def _parse_story_arc(payload: dict, seed_keyword: str) -> StoryArc:
        raw = payload.get("story_arc", {})
        if not isinstance(raw, dict):
            raw = {}
        return StoryArc(
            setting=str(raw.get("setting", f"A modern context around {seed_keyword}")).strip()
            or f"A modern context around {seed_keyword}",
            inciting_incident=str(raw.get("inciting_incident", f"A sudden trend around {seed_keyword}")).strip()
            or f"A sudden trend around {seed_keyword}",
            conflict=str(raw.get("conflict", "Conflicting claims and limited context")).strip()
            or "Conflicting claims and limited context",
            resolution=str(raw.get("resolution", "Ground the story with sourced explanation")).strip()
            or "Ground the story with sourced explanation",
            moral=str(raw.get("moral", "Context and evidence beat hype")).strip()
            or "Context and evidence beat hype",
        )
