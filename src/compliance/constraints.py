from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ProjectConstraint:
    key: str
    statement: str
    safe_alternative: str


NON_NEGOTIABLE_CONSTRAINTS: Tuple[ProjectConstraint, ...] = (
    ProjectConstraint(
        key="channel_creation_api",
        statement="YouTube channel creation is not available as a normal Data API insert endpoint.",
        safe_alternative=(
            "Use OAuth onboarding; when youtubeSignupRequired occurs, send the user through "
            "the documented channel-creation web flow."
        ),
    ),
    ProjectConstraint(
        key="studio_checks_api_gap",
        statement="Ad suitability and full Studio checks are not fully exposed for end-to-end API automation.",
        safe_alternative=(
            "Upload as private first, run internal compliance gates, then move to scheduled publish. "
            "Escalate uncertain cases to human review."
        ),
    ),
    ProjectConstraint(
        key="policy_evasion_forbidden",
        statement="Do not build logic intended to bypass strikes, claims, or policy enforcement.",
        safe_alternative=(
            "Route policy-risk videos to remediation or manual review with transparent audit logging."
        ),
    ),
    ProjectConstraint(
        key="mass_reupload_forbidden",
        statement="Do not mass repost scraped third-party content across channels.",
        safe_alternative=(
            "Require substantive transformation, rights checks, and per-video originality scoring."
        ),
    ),
    ProjectConstraint(
        key="synthetic_disclosure_required",
        statement="Realistic altered/synthetic media must be disclosed.",
        safe_alternative=(
            "Set status.containsSyntheticMedia at upload/update time when content policy rules require it."
        ),
    ),
)


UNSUPPORTED_REQUEST_MAP: Dict[str, str] = {
    "create_channel_programmatically": (
        "Not supported as direct API create. Use onboarding web flow and persist account linkage."
    ),
    "auto_publish_without_private_stage": (
        "High risk. Require private-first upload with checks and controlled publishAt."
    ),
    "auto_reupload_after_policy_reject": (
        "Not allowed as blind retry. Require human review and content changes before resubmission."
    ),
}


def list_constraints() -> List[ProjectConstraint]:
    return list(NON_NEGOTIABLE_CONSTRAINTS)


def map_unsupported_capability(request_key: str) -> str:
    if request_key not in UNSUPPORTED_REQUEST_MAP:
        return "No known mapping. Escalate to human policy review."
    return UNSUPPORTED_REQUEST_MAP[request_key]
