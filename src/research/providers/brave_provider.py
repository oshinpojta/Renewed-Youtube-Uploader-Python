from __future__ import annotations

from typing import Dict, List
from urllib.parse import quote_plus

import requests

from src.research.providers.base import ResearchProvider, ResearchProviderConfig
from src.research.types import ResearchBundle, ResearchHit, ResearchQuery


class BraveResearchProvider(ResearchProvider):
    provider_id = "brave_search_api"

    def __init__(self, config: ResearchProviderConfig) -> None:
        self.config = config

    def search(self, query: ResearchQuery) -> ResearchBundle:
        base_url = self.config.base_url.rstrip("/") or "https://api.search.brave.com"
        url = f"{base_url}/res/v1/web/search?q={quote_plus(query.query)}&count={query.max_results}"
        response = requests.get(
            url,
            headers={"X-Subscription-Token": self.config.api_key},
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Brave response is not a JSON object.")
        hits = self._parse_hits(data, query.max_results)
        return ResearchBundle(
            provider=self.provider_id,
            query=query.query,
            hits=hits,
            notes=["brave_web_search"],
        )

    @staticmethod
    def _parse_hits(data: Dict, max_results: int) -> List[ResearchHit]:
        web = data.get("web", {})
        rows = web.get("results", []) if isinstance(web, dict) else []
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
                    snippet=str(row.get("description", "")).strip(),
                    source="brave",
                    confidence=0.62,
                )
            )
        return output
