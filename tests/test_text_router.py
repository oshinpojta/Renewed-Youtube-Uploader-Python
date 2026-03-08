from __future__ import annotations

import unittest

from src.config.models import TextProviderStrategy
from src.content.text_router import TextGenerationRouter


class TextRouterTests(unittest.TestCase):
    def test_falls_back_to_template_without_credentials(self) -> None:
        strategy = TextProviderStrategy(
            provider_priority=["gemini_api"],
            fallback_order={"gemini_api": ["groq_api"]},
            per_niche_provider_order={},
            max_tokens=800,
            temperature=0.7,
        )
        router = TextGenerationRouter(strategy=strategy, credentials={})

        routed = router.generate_for_niche(
            niche_id="niche_b_ai_workflow_micro_tutorials",
            prompt="Write a short script.",
            metadata={"title": "Test", "seed_keyword": "automation"},
        )

        self.assertEqual(routed.result.provider, "template")
        self.assertIn("gemini_api", routed.attempted_providers)


if __name__ == "__main__":
    unittest.main()
