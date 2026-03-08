from __future__ import annotations

from typing import Dict, List

from src.content.providers.base import ProviderClientConfig, TextProvider, post_json
from src.content.types import TextGenerationRequest, TextGenerationResult


class GeminiTextProvider(TextProvider):
    provider_id = "gemini_api"

    def __init__(self, config: ProviderClientConfig) -> None:
        self.config = config

    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        base_url = self.config.base_url.rstrip("/") or "https://generativelanguage.googleapis.com"
        model = self.config.model or "gemini-2.5-flash"
        url = f"{base_url}/v1beta/models/{model}:generateContent?key={self.config.api_key}"
        payload = {
            "contents": [{"parts": [{"text": request.prompt}]}],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        data = post_json(url, payload, headers={"Content-Type": "application/json"})
        text = self._extract_text(data)
        return TextGenerationResult(
            provider=self.provider_id,
            model=model,
            text=text,
            notes=["gemini_generate_content"],
        )

    @staticmethod
    def _extract_text(data: Dict) -> str:
        candidates: List[Dict] = list(data.get("candidates", []))
        if not candidates:
            raise ValueError("Gemini response had no candidates.")
        first = candidates[0]
        content = first.get("content", {})
        parts = list(content.get("parts", []))
        for part in parts:
            text = str(part.get("text", "")).strip()
            if text:
                return text
        raise ValueError("Gemini response had no text part.")
