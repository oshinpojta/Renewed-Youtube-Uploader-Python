from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from src.config.models import TextProviderCredential, TextProviderStrategy
from src.content.providers import (
    GeminiTextProvider,
    GroqTextProvider,
    HuggingFaceTextProvider,
    OpenRouterTextProvider,
    TextProvider,
)
from src.content.providers.base import ProviderClientConfig
from src.content.types import TextGenerationRequest, TextGenerationResult


PROVIDER_REGISTRY = {
    "gemini_api": GeminiTextProvider,
    "groq_api": GroqTextProvider,
    "openrouter_api": OpenRouterTextProvider,
    "huggingface_api": HuggingFaceTextProvider,
}


@dataclass
class RoutedText:
    result: TextGenerationResult
    attempted_providers: List[str]


class TextGenerationRouter:
    def __init__(
        self,
        strategy: TextProviderStrategy,
        credentials: Dict[str, TextProviderCredential],
    ) -> None:
        self.strategy = strategy
        self.credentials = credentials

    def generate_for_niche(
        self,
        niche_id: str,
        prompt: str,
        metadata: Dict[str, str] | None = None,
    ) -> RoutedText:
        metadata = metadata or {}
        request = TextGenerationRequest(
            niche_id=niche_id,
            prompt=prompt,
            max_tokens=self.strategy.max_tokens,
            temperature=self.strategy.temperature,
            metadata=metadata,
        )
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
                generated = provider.generate(request)
            except Exception as exc:
                notes.append(f"{provider_name}: failed ({exc})")
                continue
            generated.notes = notes + generated.notes
            return RoutedText(result=generated, attempted_providers=attempted)

        fallback = TextGenerationResult(
            provider="template",
            model="local-template",
            text=self._template_fallback_text(prompt, metadata),
            notes=notes + ["fallback_template_used"],
        )
        return RoutedText(result=fallback, attempted_providers=attempted)

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

    def _build_provider(self, provider_name: str) -> TextProvider | None:
        provider_cls = PROVIDER_REGISTRY.get(provider_name)
        credential = self.credentials.get(provider_name)
        if provider_cls is None or credential is None or not credential.api_key:
            return None
        config = ProviderClientConfig(
            api_key=credential.api_key,
            base_url=credential.base_url,
            model=credential.model,
        )
        return provider_cls(config)

    @staticmethod
    def _template_fallback_text(prompt: str, metadata: Dict[str, str]) -> str:
        title = metadata.get("title", "Untitled brief")
        seed = metadata.get("seed_keyword", "topic")
        return (
            "{\n"
            f'  "title": "{title}",\n'
            '  "hook": "A quick, practical breakdown that stays useful and respectful.",\n'
            '  "summary": "Template fallback output because no text API provider was available.",\n'
            '  "scenes": [\n'
            f'    {{"scene": 1, "narration": "Start with why {seed} matters right now."}},\n'
            '    {"scene": 2, "narration": "Explain context with one concrete source-backed point."},\n'
            '    {"scene": 3, "narration": "Close with a practical takeaway and next-step prompt."}\n'
            "  ],\n"
            f'  "prompt_excerpt": "{prompt[:180].replace(chr(34), chr(39))}"\n'
            "}"
        )
