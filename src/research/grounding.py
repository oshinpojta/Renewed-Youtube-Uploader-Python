from __future__ import annotations

from typing import Dict, List

from src.research.types import ResearchHit


class ResearchGroundingService:
    def dedupe_and_rank(self, hits: List[ResearchHit], limit: int = 5) -> List[ResearchHit]:
        deduped: Dict[str, ResearchHit] = {}
        for hit in hits:
            key = hit.url.strip().lower()
            if not key:
                continue
            existing = deduped.get(key)
            if not existing or hit.confidence > existing.confidence:
                deduped[key] = hit
        ranked = sorted(
            deduped.values(),
            key=lambda item: (item.confidence, len(item.snippet)),
            reverse=True,
        )
        return ranked[:limit]

    @staticmethod
    def citation_urls(hits: List[ResearchHit], limit: int = 5) -> List[str]:
        return [hit.url for hit in hits[:limit]]

    @staticmethod
    def citation_snippets(hits: List[ResearchHit], limit: int = 5) -> List[str]:
        output: List[str] = []
        for hit in hits[:limit]:
            snippet = hit.snippet.strip()
            if snippet:
                output.append(f"{hit.title}: {snippet}")
            else:
                output.append(f"{hit.title}: {hit.url}")
        return output
