from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set

from src.config.models import ComplianceDecision, ContentBrief, RenderedMedia


SENSITIVE_BANNED_PHRASES = {
    "this religion is false",
    "hate",
    "exterminate",
    "guaranteed miracle cure",
    "100% true ghost proof",
}


@dataclass
class PreUploadContext:
    recent_titles: Set[str]
    require_source_credits: bool = True


class PreUploadComplianceChecker:
    def evaluate(
        self,
        brief: ContentBrief,
        media: RenderedMedia,
        context: PreUploadContext,
    ) -> ComplianceDecision:
        violations: List[str] = []
        warnings: List[str] = []

        if context.require_source_credits and not media.source_credits:
            violations.append("Missing source credits for generated media.")

        if brief.working_title.strip().lower() in context.recent_titles:
            violations.append("Title duplicates recent channel content.")

        if brief.seed_keyword.lower() not in brief.working_title.lower():
            warnings.append("Title does not include seed keyword; review metadata relevance.")

        if not brief.outline or len(brief.outline) < 3:
            violations.append("Outline is too thin for originality checks.")

        if "niche_f_religion_culture_legends_ghost_lore" == brief.niche_id:
            self._evaluate_sensitive_topic_rules(brief, violations, warnings)

        needs_human_review = bool(warnings) and "niche_f_religion_culture_legends_ghost_lore" == brief.niche_id

        return ComplianceDecision(
            passed=not violations,
            violations=violations,
            warnings=warnings,
            needs_human_review=needs_human_review,
            contains_synthetic_media=media.contains_synthetic_media,
        )

    @staticmethod
    def _evaluate_sensitive_topic_rules(
        brief: ContentBrief,
        violations: List[str],
        warnings: List[str],
    ) -> None:
        normalized_blob = " ".join(
            [brief.working_title] + brief.outline + brief.disclaimers
        ).lower()
        for phrase in SENSITIVE_BANNED_PHRASES:
            if phrase in normalized_blob:
                violations.append(f"Sensitive-topic phrase not allowed: {phrase}")

        if "educational cultural storytelling" not in normalized_blob:
            warnings.append("Sensitive-topic brief should include educational disclaimer language.")


def build_recent_title_set(titles: Iterable[str]) -> Set[str]:
    return {title.strip().lower() for title in titles if title.strip()}
