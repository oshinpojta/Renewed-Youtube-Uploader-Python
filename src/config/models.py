from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class JobStatus(str, Enum):
    QUEUED = "queued"
    PLANNED = "planned"
    PRECHECK_FAILED = "precheck_failed"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PUBLISHED = "published"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


@dataclass(frozen=True)
class ScheduleWindow:
    day_of_week: str
    start_hour: int
    end_hour: int
    timezone: str


@dataclass(frozen=True)
class ChannelProfile:
    channel_profile_id: str
    channel_name: str
    oauth_client_secrets_file: str
    token_store_key: str
    timezone: str
    default_privacy_status: str = "private"
    niches: List[str] = field(default_factory=list)
    schedule_windows: List[ScheduleWindow] = field(default_factory=list)
    fallback_hours: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class NicheBlueprint:
    niche_id: str
    display_name: str
    formats: List[str]
    source_policy: str
    trend_triggers: List[str]
    style_rules: List[str]
    is_sensitive_topic: bool = False


@dataclass(frozen=True)
class TrendSeed:
    source: str
    keyword: str
    confidence: float
    region: str = "global"


@dataclass
class ContentBrief:
    brief_id: str
    niche_id: str
    working_title: str
    hook: str
    outline: List[str]
    evidence_links: List[str]
    disclaimers: List[str]
    target_formats: List[str]
    channel_profile_id: str
    seed_keyword: str
    generated_at_utc: datetime


@dataclass(frozen=True)
class CharacterProfile:
    name: str
    role: str
    personality: str
    motivation: str


@dataclass(frozen=True)
class StoryArc:
    setting: str
    inciting_incident: str
    conflict: str
    resolution: str
    moral: str


@dataclass(frozen=True)
class ScriptScene:
    scene_id: str
    visual_prompt: str
    narration: str
    duration_seconds: int
    camera_direction: str = ""
    audio_direction: str = ""


@dataclass
class GeneratedScript:
    script_id: str
    channel_profile_id: str
    niche_id: str
    title: str
    hook: str
    scenes: List[ScriptScene]
    characters: List[CharacterProfile] = field(default_factory=list)
    story_arc: Optional[StoryArc] = None
    citations: List[str] = field(default_factory=list)
    text_provider: str = "template"
    generation_notes: List[str] = field(default_factory=list)
    requires_audio: bool = True


@dataclass
class RenderedMedia:
    media_path: str
    duration_seconds: int
    aspect_ratio: str
    contains_synthetic_media: bool
    source_credits: List[str]
    generation_provider: str = "none"
    generation_model: str = ""
    generation_mode: str = "placeholder"
    generation_notes: List[str] = field(default_factory=list)
    generation_task_id: str = ""
    render_latency_seconds: float = 0.0


@dataclass
class ComplianceDecision:
    passed: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    needs_human_review: bool = False
    contains_synthetic_media: bool = False


@dataclass
class UploadJob:
    job_id: str
    brief: ContentBrief
    media: RenderedMedia
    scheduled_publish_at_utc: datetime
    status: JobStatus
    metadata: Dict[str, object]
    retry_count: int = 0
    video_id: Optional[str] = None
    last_error: Optional[str] = None


@dataclass(frozen=True)
class DeploymentProfile:
    profile_id: str
    title: str
    monthly_cost_range_usd: str
    components: List[str]
    fit_for: str


@dataclass(frozen=True)
class ProviderCostGuardrail:
    max_cost_per_second_usd: float
    max_clip_cost_usd: float
    max_monthly_budget_usd: float
    allow_trial_only: bool = False


@dataclass(frozen=True)
class ModelProviderStrategy:
    provider_priority: List[str]
    fallback_order: Dict[str, List[str]]
    per_niche_provider_order: Dict[str, List[str]]
    cost_guardrails: Dict[str, ProviderCostGuardrail]


@dataclass(frozen=True)
class ModelProviderCredential:
    provider: str
    api_key: str
    base_url: str = ""
    model: str = ""


@dataclass(frozen=True)
class TextProviderStrategy:
    provider_priority: List[str]
    fallback_order: Dict[str, List[str]]
    per_niche_provider_order: Dict[str, List[str]]
    max_tokens: int = 1200
    temperature: float = 0.7


@dataclass(frozen=True)
class TextProviderCredential:
    provider: str
    api_key: str
    base_url: str = ""
    model: str = ""


@dataclass(frozen=True)
class ResearchProviderStrategy:
    provider_priority: List[str]
    fallback_order: Dict[str, List[str]]
    per_niche_provider_order: Dict[str, List[str]]
    max_results: int = 5


@dataclass(frozen=True)
class ResearchProviderCredential:
    provider: str
    api_key: str
    base_url: str = ""
