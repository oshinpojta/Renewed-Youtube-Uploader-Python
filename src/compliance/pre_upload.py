from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set

from src.config.models import ComplianceDecision, ContentBrief, GeneratedScript, RenderedMedia


SENSITIVE_BANNED_PHRASES = {
    "this religion is false",
    "hate",
    "exterminate",
    "guaranteed miracle cure",
    "100% true ghost proof",
}

UNSUPPORTED_CLAIM_PHRASES = {
    "guaranteed result",
    "100% true",
    "undeniable proof",
    "always works",
    "instant cure",
}

FACTUAL_NICHES = {
    "niche_c_internet_culture_context",
    "niche_d_practical_law_and_safety",
    "niche_e_micro_doc_public_domain",
    "niche_f_religion_culture_legends_ghost_lore",
}


@dataclass
class PreUploadContext:
    recent_titles: Set[str]
    require_source_credits: bool = True
    min_citation_count: int = 1
    min_scene_count: int = 3
    max_scene_count: int = 8


class PreUploadComplianceChecker:
    def evaluate(
        self,
        brief: ContentBrief,
        media: RenderedMedia,
        context: PreUploadContext,
        generated_script: GeneratedScript | None = None,
    ) -> ComplianceDecision:
        violations: List[str] = []
        warnings: List[str] = []

        if context.require_source_credits and not media.source_credits:
            violations.append("Missing source credits for generated media.")
        if len(media.source_credits) < context.min_citation_count:
            violations.append(
                f"Insufficient citations: got {len(media.source_credits)}, need {context.min_citation_count}."
            )

        if brief.working_title.strip().lower() in context.recent_titles:
            violations.append("Title duplicates recent channel content.")

        if brief.seed_keyword.lower() not in brief.working_title.lower():
            warnings.append("Title does not include seed keyword; review metadata relevance.")

        if not brief.outline or len(brief.outline) < 3:
            violations.append("Outline is too thin for originality checks.")

        if media.duration_seconds < 6:
            violations.append("Rendered duration is too short for stable delivery.")
        if media.duration_seconds > 600:
            warnings.append("Rendered duration is very long; verify pacing and retention risks.")

        if generated_script is not None:
            self._evaluate_script_quality(generated_script, media, context, violations, warnings)

        self._evaluate_unsupported_claims(brief, generated_script, violations)

        if "niche_f_religion_culture_legends_ghost_lore" == brief.niche_id:
            self._evaluate_sensitive_topic_rules(brief, violations, warnings)
        elif brief.niche_id in FACTUAL_NICHES and len(media.source_credits) < 2:
            warnings.append("Factual niche should usually include at least two independent citations.")

        needs_human_review = bool(warnings) and "niche_f_religion_culture_legends_ghost_lore" == brief.niche_id

        return ComplianceDecision(
            passed=not violations,
            violations=violations,
            warnings=warnings,
            needs_human_review=needs_human_review,
            contains_synthetic_media=media.contains_synthetic_media,
        )

    @staticmethod
    def _evaluate_script_quality(
        script: GeneratedScript,
        media: RenderedMedia,
        context: PreUploadContext,
        violations: List[str],
        warnings: List[str],
    ) -> None:
        scene_count = len(script.scenes)
        if scene_count < context.min_scene_count:
            violations.append(
                f"Script has too few scenes ({scene_count}); minimum is {context.min_scene_count}."
            )
        if scene_count > context.max_scene_count:
            warnings.append(
                f"Script has {scene_count} scenes; consider trimming to {context.max_scene_count} for pacing."
            )
        for scene in script.scenes:
            if not scene.narration.strip():
                violations.append(f"{scene.scene_id} has empty narration.")
        if script.requires_audio and media.generation_mode == "silent_render":
            violations.append("Script requires audio but render mode produced no audio track.")

    @staticmethod
    def _evaluate_unsupported_claims(
        brief: ContentBrief,
        script: GeneratedScript | None,
        violations: List[str],
    ) -> None:
        chunks = [brief.working_title] + brief.outline + brief.disclaimers
        if script is not None:
            chunks += [script.hook] + [scene.narration for scene in script.scenes]
        blob = " ".join(chunks).lower()
        for phrase in UNSUPPORTED_CLAIM_PHRASES:
            if phrase in blob:
                violations.append(f"Unsupported certainty claim detected: {phrase}")

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
