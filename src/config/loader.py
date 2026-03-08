from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

from src.config.models import (
    ChannelProfile,
    DeploymentProfile,
    NicheBlueprint,
    ScheduleWindow,
)


def _read_yaml(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as fileptr:
        data = yaml.safe_load(fileptr) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML structure in {path}")
    return data


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
