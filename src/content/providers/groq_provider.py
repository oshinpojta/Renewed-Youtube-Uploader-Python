from __future__ import annotations

from typing import Dict, List

from src.content.providers.base import ProviderClientConfig, TextProvider, post_json
from src.content.types import TextGenerationRequest, TextGenerationResult


class GroqTextProvider(TextProvider):
    provider_id = "groq_api"

    def __init__(self, config: ProviderClientConfig) -> None:
        self.config = config

    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        base_url = self.config.base_url.rstrip("/") or "https://api.groq.com/openai/v1"
        model = self.config.model or "llama-3.3-70b-versatile"
        url = f"{base_url}/chat/completions"
        payload = {
            "model": model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        data = post_json(
            url=url,
            payload=payload,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self.config.timeout_seconds,
        )
        text = self._extract_text(data)
        return TextGenerationResult(
            provider=self.provider_id,
            model=model,
            text=text,
            notes=["groq_chat_completions"],
        )

    @staticmethod
    def _extract_text(data: Dict) -> str:
        choices: List[Dict] = list(data.get("choices", []))
        if not choices:
            raise ValueError("Groq response had no choices.")
        message = choices[0].get("message", {})
        text = str(message.get("content", "")).strip()
        if not text:
            raise ValueError("Groq response had empty content.")
        return text
