from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from src.config.models import (
    ModelProviderCredential,
    ModelProviderStrategy,
)


@dataclass(frozen=True)
class ProviderCapability:
    supports_audio: bool
    max_duration_seconds: int
    estimated_cost_per_second_usd: float
    supports_api_automation: bool = True


@dataclass
class ProviderSelection:
    provider: str
    model: str
    estimated_cost_usd: float
    notes: List[str] = field(default_factory=list)


PROVIDER_CAPABILITIES: Dict[str, ProviderCapability] = {
    "veo3": ProviderCapability(
        supports_audio=True,
        max_duration_seconds=60,
        estimated_cost_per_second_usd=0.40,
        supports_api_automation=True,
    ),
    "kling_ai": ProviderCapability(
        supports_audio=True,
        max_duration_seconds=10,
        estimated_cost_per_second_usd=0.09,
        supports_api_automation=True,
    ),
    "seedance_2": ProviderCapability(
        supports_audio=True,
        max_duration_seconds=15,
        estimated_cost_per_second_usd=0.12,
        supports_api_automation=True,
    ),
    "sora_api": ProviderCapability(
        supports_audio=True,
        max_duration_seconds=25,
        estimated_cost_per_second_usd=0.10,
        supports_api_automation=True,
    ),
    "bing_sora_ui": ProviderCapability(
        supports_audio=False,
        max_duration_seconds=5,
        estimated_cost_per_second_usd=0.0,
        supports_api_automation=False,
    ),
}


class ModelProviderRouter:
    def __init__(
        self,
        strategy: ModelProviderStrategy,
        credentials: Dict[str, ModelProviderCredential],
    ) -> None:
        self.strategy = strategy
        self.credentials = credentials

    def select_for_niche(
        self,
        niche_id: str,
        duration_seconds: int,
        require_audio: bool = True,
    ) -> ProviderSelection:
        notes: List[str] = []
        order = list(self.strategy.per_niche_provider_order.get(niche_id, []))
        if not order:
            order = list(self.strategy.provider_priority)

        expanded_order: List[str] = []
        for provider in order:
            if provider not in expanded_order:
                expanded_order.append(provider)
            for fallback in self.strategy.fallback_order.get(provider, []):
                if fallback not in expanded_order:
                    expanded_order.append(fallback)

        for provider in expanded_order:
            capability = PROVIDER_CAPABILITIES.get(provider)
            if not capability:
                notes.append(f"{provider}: skipped (unknown capability)")
                continue
            if not capability.supports_api_automation:
                notes.append(f"{provider}: skipped (no stable API automation path)")
                continue
            if require_audio and not capability.supports_audio:
                notes.append(f"{provider}: skipped (audio required)")
                continue
            if duration_seconds > capability.max_duration_seconds:
                notes.append(
                    f"{provider}: skipped (duration {duration_seconds}s exceeds {capability.max_duration_seconds}s)"
                )
                continue

            guard = self.strategy.cost_guardrails.get(provider)
            estimated_cost = capability.estimated_cost_per_second_usd * float(duration_seconds)
            if guard:
                if capability.estimated_cost_per_second_usd > guard.max_cost_per_second_usd:
                    notes.append(
                        f"{provider}: skipped (cost/sec {capability.estimated_cost_per_second_usd:.3f} exceeds {guard.max_cost_per_second_usd:.3f})"
                    )
                    continue
                if estimated_cost > guard.max_clip_cost_usd:
                    notes.append(
                        f"{provider}: skipped (clip cost {estimated_cost:.2f} exceeds {guard.max_clip_cost_usd:.2f})"
                    )
                    continue

            cred = self.credentials.get(provider)
            if not cred or not cred.api_key:
                notes.append(f"{provider}: skipped (missing API key)")
                continue

            model_name = cred.model or "default"
            notes.append(
                f"{provider}: selected model={model_name} estimated_cost_usd={estimated_cost:.2f}"
            )
            return ProviderSelection(
                provider=provider,
                model=model_name,
                estimated_cost_usd=estimated_cost,
                notes=notes,
            )

        return ProviderSelection(
            provider="none",
            model="",
            estimated_cost_usd=0.0,
            notes=notes + ["no eligible provider selected; fallback to local/placeholder rendering"],
        )
