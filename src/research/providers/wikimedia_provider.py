from __future__ import annotations

from typing import Dict, List
from urllib.parse import quote_plus

import requests

from src.research.providers.base import ResearchProvider, ResearchProviderConfig
from src.research.types import ResearchBundle, ResearchHit, ResearchQuery


class WikimediaResearchProvider(ResearchProvider):
    provider_id = "wikimedia_api"

    def __init__(self, config: ResearchProviderConfig) -> None:
        self.config = config

    def search(self, query: ResearchQuery) -> ResearchBundle:
        # Wikimedia's public API can be used without a paid key.
        base_url = self.config.base_url.rstrip("/") or "https://en.wikipedia.org"
        url = (
            f"{base_url}/w/api.php?action=query&list=search&utf8=1&format=json"
            f"&srsearch={quote_plus(query.query)}&srlimit={query.max_results}"
        )
        response = requests.get(
            url,
            headers={"User-Agent": "RenewedUploader/1.0 (content-research-bot)"},
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Wikimedia response is not a JSON object.")
        hits = self._parse_hits(data, query.max_results)
        return ResearchBundle(
            provider=self.provider_id,
            query=query.query,
            hits=hits,
            notes=["wikimedia_search"],
        )

    @staticmethod
    def _parse_hits(data: Dict, max_results: int) -> List[ResearchHit]:
        query = data.get("query", {})
        rows = query.get("search", []) if isinstance(query, dict) else []
        output: List[ResearchHit] = []
        if not isinstance(rows, list):
            return output
        for row in rows[:max_results]:
            if not isinstance(row, dict):
                continue
            title = str(row.get("title", "")).strip()
            if not title:
                continue
            url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            snippet = str(row.get("snippet", "")).replace("<span class=\"searchmatch\">", "")
            snippet = snippet.replace("</span>", "").strip()
            output.append(
                ResearchHit(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="wikimedia",
                    confidence=0.58,
                )
            )
        return output
