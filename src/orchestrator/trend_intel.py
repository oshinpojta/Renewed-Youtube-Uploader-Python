from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Iterable, List

from src.config.models import NicheBlueprint, TrendSeed
from src.research.types import ResearchHit

if TYPE_CHECKING:
    from src.research.research_router import ResearchRouter


@dataclass
class TrendIntelCollector:
    """Low-cost trend source collector using curated keyword pools."""
    research_router: "ResearchRouter | None" = None

    def collect(self, blueprints: Dict[str, NicheBlueprint]) -> Dict[str, List[TrendSeed]]:
        grouped: Dict[str, List[TrendSeed]] = defaultdict(list)
        for niche_id, blueprint in blueprints.items():
            niche_keywords = self._unique_first(blueprint.trend_triggers, limit=8)
            for keyword in niche_keywords:
                grouped[niche_id].append(
                    TrendSeed(
                        source="curated_triggers",
                        keyword=keyword,
                        confidence=0.55,
                        region="global",
                    )
                )
            if self.research_router and niche_keywords:
                query = f"{niche_keywords[0]} {blueprint.display_name}"
                try:
                    routed = self.research_router.search_for_niche(
                        niche_id=niche_id,
                        query=query,
                        max_results=3,
                    )
                except Exception:
                    continue
                for hit in routed.bundle.hits[:3]:
                    grouped[niche_id].append(
                        TrendSeed(
                            source=routed.bundle.provider,
                            keyword=self._keyword_from_hit(hit),
                            confidence=max(0.35, min(hit.confidence, 0.9)),
                            region="global",
                        )
                    )
        return grouped

    @staticmethod
    def _unique_first(values: Iterable[str], limit: int) -> List[str]:
        seen = set()
        output: List[str] = []
        for value in values:
            clean = value.strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            output.append(clean)
            if len(output) >= limit:
                break
        return output

    @staticmethod
    def _keyword_from_hit(hit: ResearchHit) -> str:
        title = hit.title.strip()
        if title:
            return title.lower()[:80]
        return hit.url.lower()[:80]
