from __future__ import annotations

from typing import Dict, List

import requests

from src.research.providers.base import ResearchProvider, ResearchProviderConfig
from src.research.types import ResearchBundle, ResearchHit, ResearchQuery


class TavilyResearchProvider(ResearchProvider):
    provider_id = "tavily_api"

    def __init__(self, config: ResearchProviderConfig) -> None:
        self.config = config

    def search(self, query: ResearchQuery) -> ResearchBundle:
        base_url = self.config.base_url.rstrip("/") or "https://api.tavily.com"
        url = f"{base_url}/search"
        payload = {
            "api_key": self.config.api_key,
            "query": query.query,
            "max_results": query.max_results,
            "search_depth": "basic",
        }
        response = requests.post(url, json=payload, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Tavily response is not a JSON object.")
        hits = self._parse_hits(data, query.max_results)
        return ResearchBundle(
            provider=self.provider_id,
            query=query.query,
            hits=hits,
            notes=["tavily_search_basic"],
        )

    @staticmethod
    def _parse_hits(data: Dict, max_results: int) -> List[ResearchHit]:
        rows = data.get("results", [])
        output: List[ResearchHit] = []
        if not isinstance(rows, list):
            return output
        for row in rows[:max_results]:
            if not isinstance(row, dict):
                continue
            url = str(row.get("url", "")).strip()
            if not url:
                continue
            output.append(
                ResearchHit(
                    title=str(row.get("title", "")).strip() or "Untitled",
                    url=url,
                    snippet=str(row.get("content", "")).strip(),
                    source="tavily",
                    confidence=float(row.get("score", 0.6) or 0.6),
                )
            )
        return output
