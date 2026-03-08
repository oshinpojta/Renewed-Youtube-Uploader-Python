from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
from urllib.parse import quote_plus

from src.config.models import ResearchProviderCredential, ResearchProviderStrategy
from src.research.grounding import ResearchGroundingService
from src.research.providers import (
    BraveResearchProvider,
    ResearchProvider,
    TavilyResearchProvider,
    WikimediaResearchProvider,
)
from src.research.providers.base import ResearchProviderConfig
from src.research.types import ResearchBundle, ResearchHit, ResearchQuery


PROVIDER_REGISTRY = {
    "tavily_api": TavilyResearchProvider,
    "brave_search_api": BraveResearchProvider,
    "wikimedia_api": WikimediaResearchProvider,
}


@dataclass
class RoutedResearch:
    bundle: ResearchBundle
    attempted_providers: List[str]


class ResearchRouter:
    def __init__(
        self,
        strategy: ResearchProviderStrategy,
        credentials: Dict[str, ResearchProviderCredential],
        grounding: ResearchGroundingService | None = None,
    ) -> None:
        self.strategy = strategy
        self.credentials = credentials
        self.grounding = grounding or ResearchGroundingService()

    def search_for_niche(self, niche_id: str, query: str, max_results: int | None = None) -> RoutedResearch:
        max_items = int(max_results or self.strategy.max_results)
        request = ResearchQuery(niche_id=niche_id, query=query, max_results=max_items)
        order = self._expanded_provider_order(niche_id)
        attempted: List[str] = []
        notes: List[str] = []

        for provider_name in order:
            attempted.append(provider_name)
            provider = self._build_provider(provider_name)
            if provider is None:
                notes.append(f"{provider_name}: skipped (unknown provider or missing key)")
                continue
            try:
                bundle = provider.search(request)
            except Exception as exc:
                notes.append(f"{provider_name}: failed ({exc})")
                continue
            ranked = self.grounding.dedupe_and_rank(bundle.hits, limit=max_items)
            bundle.hits = ranked
            bundle.notes = notes + bundle.notes
            return RoutedResearch(bundle=bundle, attempted_providers=attempted)

        fallback_hits = self._fallback_hits(query)
        fallback_bundle = ResearchBundle(
            provider="template",
            query=query,
            hits=fallback_hits,
            notes=notes + ["fallback_research_used"],
        )
        return RoutedResearch(bundle=fallback_bundle, attempted_providers=attempted)

    def _expanded_provider_order(self, niche_id: str) -> List[str]:
        primary = list(self.strategy.per_niche_provider_order.get(niche_id, []))
        if not primary:
            primary = list(self.strategy.provider_priority)
        expanded: List[str] = []
        for provider in primary:
            if provider not in expanded:
                expanded.append(provider)
            for fallback in self.strategy.fallback_order.get(provider, []):
                if fallback not in expanded:
                    expanded.append(fallback)
        return expanded

    def _build_provider(self, provider_name: str) -> ResearchProvider | None:
        provider_cls = PROVIDER_REGISTRY.get(provider_name)
        if provider_cls is None:
            return None
        credential = self.credentials.get(provider_name)
        if provider_name != "wikimedia_api" and (credential is None or not credential.api_key):
            return None
        config = ResearchProviderConfig(
            api_key=credential.api_key if credential else "",
            base_url=credential.base_url if credential else "",
        )
        return provider_cls(config)

    @staticmethod
    def _fallback_hits(query: str) -> List[ResearchHit]:
        wiki_url = f"https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(query)}"
        return [
            ResearchHit(
                title=f"Background on {query}",
                url=wiki_url,
                snippet="Fallback citation generated locally when external search APIs are unavailable.",
                source="template",
                confidence=0.4,
            )
        ]
