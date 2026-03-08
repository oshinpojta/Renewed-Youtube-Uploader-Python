from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


TECHNICAL_FAILURE_REASONS = {
    "uploadAborted",
    "tooSmall",
    "invalidFile",
    "emptyFile",
    "conversion",
    "codec",
}

POLICY_RISK_REJECTION_REASONS = {
    "termsOfUse",
    "legal",
    "inappropriate",
    "copyright",
    "claim",
    "trademark",
}


@dataclass
class PostUploadDecision:
    terminal_status: bool
    ready_to_publish: bool
    needs_retry: bool
    needs_human_review: bool
    reasons: List[str]


class PostUploadComplianceChecker:
    def evaluate_video_state(self, api_video_resource: Dict) -> PostUploadDecision:
        status = api_video_resource.get("status", {})
        processing = api_video_resource.get("processingDetails", {})

        upload_status = status.get("uploadStatus")
        failure_reason = status.get("failureReason")
        rejection_reason = status.get("rejectionReason")
        processing_status = processing.get("processingStatus")
        processing_failure = processing.get("processingFailureReason")

        reasons: List[str] = []
        needs_retry = False
        needs_human_review = False
        terminal = False
        ready_to_publish = False

        if upload_status in {"processed", "uploaded"} and processing_status in {None, "succeeded"}:
            terminal = True
            ready_to_publish = True
            reasons.append("Upload processed successfully.")

        if failure_reason:
            reasons.append(f"failureReason={failure_reason}")
            terminal = True
            if failure_reason in TECHNICAL_FAILURE_REASONS:
                needs_retry = True
            else:
                needs_human_review = True

        if rejection_reason:
            reasons.append(f"rejectionReason={rejection_reason}")
            terminal = True
            if rejection_reason in POLICY_RISK_REJECTION_REASONS:
                needs_human_review = True
            else:
                needs_retry = True

        if processing_failure:
            reasons.append(f"processingFailureReason={processing_failure}")
            terminal = True
            needs_retry = True

        if upload_status == "failed":
            terminal = True
            needs_retry = True
            reasons.append("Upload status=failed")

        if upload_status == "rejected":
            terminal = True
            needs_human_review = True
            reasons.append("Upload status=rejected")

        if not reasons:
            reasons.append("Video still processing.")

        return PostUploadDecision(
            terminal_status=terminal,
            ready_to_publish=ready_to_publish,
            needs_retry=needs_retry,
            needs_human_review=needs_human_review,
            reasons=reasons,
        )
