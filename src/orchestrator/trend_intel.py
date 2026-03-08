from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List

from src.config.models import NicheBlueprint, TrendSeed


@dataclass
class TrendIntelCollector:
    """Low-cost trend source collector using curated keyword pools."""

    def collect(self, blueprints: Dict[str, NicheBlueprint]) -> Dict[str, List[TrendSeed]]:
        grouped: Dict[str, List[TrendSeed]] = defaultdict(list)
        for niche_id, blueprint in blueprints.items():
            for keyword in self._unique_first(blueprint.trend_triggers, limit=8):
                grouped[niche_id].append(
                    TrendSeed(
                        source="curated_triggers",
                        keyword=keyword,
                        confidence=0.55,
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
