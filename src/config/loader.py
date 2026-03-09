from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

from src.config.models import (
    ChannelProfile,
    DeploymentProfile,
    ModelProviderCredential,
    ModelProviderStrategy,
    NicheBlueprint,
    ProviderCostGuardrail,
    ResearchProviderCredential,
    ResearchProviderStrategy,
    ScheduleWindow,
    TextProviderCredential,
    TextProviderStrategy,
)


def _read_yaml(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as fileptr:
        data = yaml.safe_load(fileptr) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML structure in {path}")
    return data


def _read_yaml_optional(path: Path) -> Dict:
    if not path.exists():
        return {}
    return _read_yaml(path)


def load_channels(config_path: Path) -> List[ChannelProfile]:
    data = _read_yaml(config_path)
    rows = data.get("channels", [])
    output: List[ChannelProfile] = []
    for row in rows:
        windows = [
            ScheduleWindow(
                day_of_week=item["day_of_week"],
                start_hour=int(item["start_hour"]),
                end_hour=int(item["end_hour"]),
                timezone=item.get("timezone", row["timezone"]),
            )
            for item in row.get("schedule_windows", [])
        ]
        profile = ChannelProfile(
            channel_profile_id=row["channel_profile_id"],
            channel_name=row["channel_name"],
            oauth_client_secrets_file=row["oauth_client_secrets_file"],
            token_store_key=row["token_store_key"],
            timezone=row["timezone"],
            default_privacy_status=row.get("default_privacy_status", "private"),
            niches=list(row.get("niches", [])),
            schedule_windows=windows,
            fallback_hours=[int(h) for h in row.get("fallback_hours", [])],
        )
        output.append(profile)
    return output


def load_niches(config_path: Path) -> Dict[str, NicheBlueprint]:
    data = _read_yaml(config_path)
    rows = data.get("niches", [])
    output: Dict[str, NicheBlueprint] = {}
    for row in rows:
        blueprint = NicheBlueprint(
            niche_id=row["niche_id"],
            display_name=row["display_name"],
            formats=list(row.get("formats", [])),
            source_policy=row["source_policy"],
            trend_triggers=list(row.get("trend_triggers", [])),
            style_rules=list(row.get("style_rules", [])),
            is_sensitive_topic=bool(row.get("is_sensitive_topic", False)),
        )
        output[blueprint.niche_id] = blueprint
    return output


def load_deployment_profiles(config_path: Path) -> Dict[str, DeploymentProfile]:
    data = _read_yaml(config_path)
    rows = data.get("deployment_profiles", [])
    output: Dict[str, DeploymentProfile] = {}
    for row in rows:
        profile = DeploymentProfile(
            profile_id=row["profile_id"],
            title=row["title"],
            monthly_cost_range_usd=row["monthly_cost_range_usd"],
            components=list(row.get("components", [])),
            fit_for=row["fit_for"],
        )
        output[profile.profile_id] = profile
    return output


def load_model_generation_strategy(config_path: Path) -> ModelProviderStrategy:
    data = _read_yaml(config_path)
    root = data.get("model_generation_strategy", data)
    guardrails: Dict[str, ProviderCostGuardrail] = {}
    for provider, row in root.get("cost_guardrails", {}).items():
        guardrails[provider] = ProviderCostGuardrail(
            max_cost_per_second_usd=float(row.get("max_cost_per_second_usd", 999.0)),
            max_clip_cost_usd=float(row.get("max_clip_cost_usd", 999.0)),
            max_monthly_budget_usd=float(row.get("max_monthly_budget_usd", 9999.0)),
            allow_trial_only=bool(row.get("allow_trial_only", False)),
        )
    return ModelProviderStrategy(
        provider_priority=list(root.get("provider_priority", [])),
        fallback_order={
            key: list(values)
            for key, values in dict(root.get("fallback_order", {})).items()
        },
        per_niche_provider_order={
            key: list(values)
            for key, values in dict(root.get("per_niche_provider_order", {})).items()
        },
        cost_guardrails=guardrails,
    )


def load_model_api_keys(config_path: Path) -> Dict[str, ModelProviderCredential]:
    data = _read_yaml_optional(config_path)
    providers = data.get("providers", {})
    output: Dict[str, ModelProviderCredential] = {}
    for provider, row in providers.items():
        output[provider] = ModelProviderCredential(
            provider=provider,
            api_key=str(row.get("api_key", "")).strip(),
            secret_key=str(row.get("secret_key", "")).strip(),
            base_url=str(row.get("base_url", "")).strip(),
            model=str(row.get("model", "")).strip(),
        )
    return output


def load_text_generation_strategy(config_path: Path) -> TextProviderStrategy:
    data = _read_yaml(config_path)
    root = data.get("text_generation_strategy", data)
    return TextProviderStrategy(
        provider_priority=list(root.get("provider_priority", [])),
        fallback_order={
            key: list(values)
            for key, values in dict(root.get("fallback_order", {})).items()
        },
        per_niche_provider_order={
            key: list(values)
            for key, values in dict(root.get("per_niche_provider_order", {})).items()
        },
        max_tokens=int(root.get("max_tokens", 1200)),
        temperature=float(root.get("temperature", 0.7)),
    )


def load_text_api_keys(config_path: Path) -> Dict[str, TextProviderCredential]:
    data = _read_yaml_optional(config_path)
    providers = data.get("providers", {})
    output: Dict[str, TextProviderCredential] = {}
    for provider, row in providers.items():
        output[provider] = TextProviderCredential(
            provider=provider,
            api_key=str(row.get("api_key", "")).strip(),
            base_url=str(row.get("base_url", "")).strip(),
            model=str(row.get("model", "")).strip(),
        )
    return output


def load_research_provider_strategy(config_path: Path) -> ResearchProviderStrategy:
    data = _read_yaml(config_path)
    root = data.get("research_provider_strategy", data)
    return ResearchProviderStrategy(
        provider_priority=list(root.get("provider_priority", [])),
        fallback_order={
            key: list(values)
            for key, values in dict(root.get("fallback_order", {})).items()
        },
        per_niche_provider_order={
            key: list(values)
            for key, values in dict(root.get("per_niche_provider_order", {})).items()
        },
        max_results=int(root.get("max_results", 5)),
    )


def load_research_api_keys(config_path: Path) -> Dict[str, ResearchProviderCredential]:
    data = _read_yaml_optional(config_path)
    providers = data.get("providers", {})
    output: Dict[str, ResearchProviderCredential] = {}
    for provider, row in providers.items():
        output[provider] = ResearchProviderCredential(
            provider=provider,
            api_key=str(row.get("api_key", "")).strip(),
            base_url=str(row.get("base_url", "")).strip(),
        )
    return output
