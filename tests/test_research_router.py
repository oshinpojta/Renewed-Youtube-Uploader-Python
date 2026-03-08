from __future__ import annotations

import unittest

from src.config.models import ResearchProviderStrategy
from src.research.research_router import ResearchRouter


class ResearchRouterTests(unittest.TestCase):
    def test_falls_back_to_template_without_credentials(self) -> None:
        strategy = ResearchProviderStrategy(
            provider_priority=["tavily_api"],
            fallback_order={"tavily_api": ["brave_search_api", "wikimedia_api"]},
            per_niche_provider_order={},
            max_results=3,
        )
        router = ResearchRouter(strategy=strategy, credentials={})

        routed = router.search_for_niche(
            niche_id="niche_e_micro_doc_public_domain",
            query="forgotten inventions",
        )

        self.assertIn(routed.bundle.provider, {"template", "wikimedia_api"})
        self.assertGreaterEqual(len(routed.bundle.hits), 1)
        self.assertTrue(
            "wikipedia.org" in routed.bundle.hits[0].url
            or "wikipedia.org" in routed.bundle.hits[0].title.lower()
        )


if __name__ == "__main__":
    unittest.main()
