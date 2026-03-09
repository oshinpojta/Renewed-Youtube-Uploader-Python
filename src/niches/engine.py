from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List

from src.config.models import ContentBrief, NicheBlueprint, TrendSeed


def _title_from_seed(prefix: str, seed: TrendSeed) -> str:
    return f"{prefix}: {seed.keyword.title()}"


class NicheEngine:
    def __init__(self, blueprint: NicheBlueprint) -> None:
        self.blueprint = blueprint

    def build_outline(self, seed: TrendSeed) -> List[str]:
        return [
            f"Hook on {seed.keyword} and why it matters now",
            "Context and evidence-backed background",
            "Main analysis with clear audience value",
            "Actionable takeaway and next topic bridge",
        ]

    def build_disclaimers(self) -> List[str]:
        return []

    def build_brief(self, channel_profile_id: str, seed: TrendSeed) -> ContentBrief:
        return ContentBrief(
            brief_id=f"brief_{uuid.uuid4().hex[:12]}",
            niche_id=self.blueprint.niche_id,
            working_title=_title_from_seed(self.blueprint.display_name, seed),
            hook=f"Today we decode {seed.keyword} in a practical, viewer-first format.",
            outline=self.build_outline(seed),
            evidence_links=[
                "https://youtube.com/trends/report",
                "https://support.google.com/youtube/answer/1311392?hl=en",
            ],
            disclaimers=self.build_disclaimers(),
            target_formats=self.blueprint.formats,
            channel_profile_id=channel_profile_id,
            seed_keyword=seed.keyword,
            generated_at_utc=datetime.now(tz=timezone.utc),
        )


class RobloxUGCEngine(NicheEngine):
    def build_outline(self, seed: TrendSeed) -> List[str]:
        return [
            f"Quick setup: what {seed.keyword} is in the creator-game ecosystem",
            "Meta snapshot: update cycle, player intent, and retention hooks",
            "3 strategy insights that change outcomes",
            "One test challenge for the audience to try",
        ]


class AIWorkflowEngine(NicheEngine):
    def build_outline(self, seed: TrendSeed) -> List[str]:
        return [
            f"Problem statement: where {seed.keyword} wastes time",
            "60-second workflow template and tool chain",
            "Failure cases and quality checks",
            "Repeatable checklist for daily use",
        ]


class InternetCultureEngine(NicheEngine):
    def build_outline(self, seed: TrendSeed) -> List[str]:
        return [
            f"Origin story of {seed.keyword}",
            "How creators remixed and amplified it",
            "What it says about fan communities now",
            "What might trend next from this pattern",
        ]


class PracticalLawEngine(NicheEngine):
    def build_outline(self, seed: TrendSeed) -> List[str]:
        return [
            f"Scenario intro: {seed.keyword}",
            "What is commonly misunderstood",
            "Jurisdiction-aware guidance and caveats",
            "When to seek professional/legal advice",
        ]

    def build_disclaimers(self) -> List[str]:
        return ["Educational content only; not legal advice."]


class PublicDomainMicroDocEngine(NicheEngine):
    def build_outline(self, seed: TrendSeed) -> List[str]:
        return [
            f"Historical setup around {seed.keyword}",
            "Primary source excerpt and interpretation",
            "Visual timeline and implications",
            "Modern relevance in 1 minute",
        ]

    def build_disclaimers(self) -> List[str]:
        return ["Public-domain and licensed-source workflow applied."]


class ReligionCultureGhostLoreEngine(NicheEngine):
    def build_outline(self, seed: TrendSeed) -> List[str]:
        return [
            f"Cold open: the most surprising claim behind {seed.keyword}",
            "Trace the earliest documented references and historical timeline",
            "Compare how the legend changed across at least two cultures or regions",
            "Separate source-backed facts from folklore interpretation",
            "Close with modern cultural meaning and one memorable evidence-backed fact",
        ]

    def build_brief(self, channel_profile_id: str, seed: TrendSeed) -> ContentBrief:
        brief = super().build_brief(channel_profile_id, seed)
        brief.working_title = f"History vs Legend: {seed.keyword.title()}"
        brief.hook = (
            f"What if the real history behind {seed.keyword} is even more fascinating than the legend?"
        )
        return brief

    def build_disclaimers(self) -> List[str]:
        return [
            "Educational cultural storytelling; not a claim of supernatural fact.",
            "Respect all faiths and traditions; avoid harassment or denigration.",
        ]


ENGINE_REGISTRY = {
    "niche_a_roblox_ugc_explainers": RobloxUGCEngine,
    "niche_b_ai_workflow_micro_tutorials": AIWorkflowEngine,
    "niche_c_internet_culture_context": InternetCultureEngine,
    "niche_d_practical_law_and_safety": PracticalLawEngine,
    "niche_e_micro_doc_public_domain": PublicDomainMicroDocEngine,
    "niche_f_religion_culture_legends_ghost_lore": ReligionCultureGhostLoreEngine,
}


def build_engine_map(blueprints: Dict[str, NicheBlueprint]) -> Dict[str, NicheEngine]:
    engines: Dict[str, NicheEngine] = {}
    for niche_id, blueprint in blueprints.items():
        engine_cls = ENGINE_REGISTRY.get(niche_id, NicheEngine)
        engines[niche_id] = engine_cls(blueprint)
    return engines
