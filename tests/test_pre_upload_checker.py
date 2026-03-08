from __future__ import annotations

import unittest
from datetime import datetime, timezone

from src.compliance.pre_upload import PreUploadComplianceChecker, PreUploadContext
from src.config.models import (
    CharacterProfile,
    ContentBrief,
    GeneratedScript,
    ScriptScene,
    StoryArc,
    RenderedMedia,
)


class PreUploadCheckerTests(unittest.TestCase):
    def test_blocks_unsupported_claims_and_low_citations(self) -> None:
        brief = ContentBrief(
            brief_id="brief_1",
            niche_id="niche_f_religion_culture_legends_ghost_lore",
            working_title="Ghost lore explained 100% true",
            hook="Decoded with sources",
            outline=["scene one", "scene two", "scene three"],
            evidence_links=["https://example.com/source-1"],
            disclaimers=["Educational cultural storytelling; not a claim of supernatural fact."],
            target_formats=["short_60"],
            channel_profile_id="channel_1",
            seed_keyword="ghost folklore",
            generated_at_utc=datetime.now(tz=timezone.utc),
        )
        media = RenderedMedia(
            media_path="output.mp4",
            duration_seconds=20,
            aspect_ratio="9:16",
            contains_synthetic_media=True,
            source_credits=brief.evidence_links,
        )
        script = GeneratedScript(
            script_id="script_1",
            channel_profile_id=brief.channel_profile_id,
            niche_id=brief.niche_id,
            title=brief.working_title,
            hook=brief.hook,
            scenes=[
                ScriptScene(
                    scene_id="scene_1",
                    visual_prompt="prompt",
                    narration="This is 100% true and undeniable proof.",
                    duration_seconds=8,
                ),
                ScriptScene(
                    scene_id="scene_2",
                    visual_prompt="prompt",
                    narration="more context",
                    duration_seconds=8,
                ),
                ScriptScene(
                    scene_id="scene_3",
                    visual_prompt="prompt",
                    narration="outro",
                    duration_seconds=8,
                ),
            ],
            characters=[CharacterProfile(name="Guide", role="Narrator", personality="Calm", motivation="Teach")],
            story_arc=StoryArc(
                setting="setting",
                inciting_incident="incident",
                conflict="conflict",
                resolution="resolution",
                moral="moral",
            ),
            citations=brief.evidence_links,
        )
        checker = PreUploadComplianceChecker()
        decision = checker.evaluate(
            brief=brief,
            media=media,
            generated_script=script,
            context=PreUploadContext(recent_titles=set(), min_citation_count=2),
        )

        self.assertFalse(decision.passed)
        self.assertTrue(any("Insufficient citations" in item for item in decision.violations))
        self.assertTrue(any("Unsupported certainty claim" in item for item in decision.violations))


if __name__ == "__main__":
    unittest.main()
