from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from src.compliance.pre_upload import PreUploadComplianceChecker, PreUploadContext, build_recent_title_set
from src.compliance.remediation import RemediationEngine
from src.config.models import ChannelProfile, JobStatus, UploadJob
from src.media.factory import MediaFactory
from src.orchestrator.niche_planner import NichePlanner
from src.orchestrator.trend_intel import TrendIntelCollector
from src.orchestrator.upload_scheduler import UploadTimeScheduler
from src.storage.event_logger import PipelineEventLogger
from src.storage.job_store import JobStore
from src.youtube.monitor import YouTubePostPublishMonitor
from src.youtube.uploader import YouTubeUploadError, YouTubeUploader


@dataclass
class PipelineDependencies:
    trend_intel: TrendIntelCollector
    niche_planner: NichePlanner
    media_factory: MediaFactory
    pre_upload_checker: PreUploadComplianceChecker
    scheduler: UploadTimeScheduler
    job_store: JobStore
    event_logger: PipelineEventLogger
    uploader: YouTubeUploader
    monitor: YouTubePostPublishMonitor
    remediation: RemediationEngine


class ComplianceFirstPipeline:
    def __init__(self, deps: PipelineDependencies) -> None:
        self.deps = deps

    def _record_event(
        self,
        event_type: str,
        channel: ChannelProfile,
        job: Optional[UploadJob] = None,
        payload: Optional[Dict] = None,
    ) -> None:
        try:
            self.deps.event_logger.log_pipeline_event(
                event_type=event_type,
                channel=channel,
                job=job,
                payload=payload,
            )
            self.deps.job_store.add_job_event(
                event_type=event_type,
                channel_profile_id=channel.channel_profile_id,
                niche_id=job.brief.niche_id if job else None,
                job_id=job.job_id if job else None,
                video_id=job.video_id if job else None,
                payload=payload or {},
            )
        except Exception:
            # Logging should never block the delivery pipeline.
            return

    def plan_jobs_for_channel(self, channel: ChannelProfile) -> List[UploadJob]:
        blueprints = {
            niche_id: engine.blueprint
            for niche_id, engine in self.deps.niche_planner.engines.items()
        }
        trend_map = self.deps.trend_intel.collect(blueprints)
        briefs = self.deps.niche_planner.build_channel_briefs(channel, trend_map, briefs_per_niche=1)

        jobs: List[UploadJob] = []
        recent_titles = build_recent_title_set(self.deps.job_store.list_recent_titles(channel.channel_profile_id))
        performance = self.deps.job_store.average_performance_by_hour(channel.channel_profile_id)

        for brief in briefs:
            media = self.deps.media_factory.render(brief, source_clips=[])
            decision = self.deps.pre_upload_checker.evaluate(
                brief=brief,
                media=media,
                context=PreUploadContext(recent_titles=recent_titles, require_source_credits=True),
            )
            status = JobStatus.PLANNED if decision.passed and not decision.needs_human_review else JobStatus.NEEDS_REVIEW
            if not decision.passed:
                status = JobStatus.PRECHECK_FAILED

            selection = self.deps.scheduler.pick_slot_details(
                channel,
                performance,
                now_utc=datetime.now(tz=timezone.utc),
            )
            publish_at = selection.publish_at_utc
            metadata = {
                "title": brief.working_title,
                "description": "\n".join(brief.outline + [""] + brief.disclaimers),
                "tags": [brief.seed_keyword, brief.niche_id, "automation"],
                "category_id": "22",
                "compliance_warnings": "; ".join(decision.warnings),
                "compliance_violations": "; ".join(decision.violations),
                "schedule_source": selection.source,
                "schedule_local_hour": str(selection.local_hour),
                "schedule_score": f"{selection.score:.4f}",
            }
            job = UploadJob(
                job_id=f"job_{uuid.uuid4().hex[:12]}",
                brief=brief,
                media=media,
                scheduled_publish_at_utc=publish_at,
                status=status,
                metadata=metadata,
            )
            self.deps.job_store.upsert_job(job)
            self._record_event(
                "job_planned",
                channel,
                job,
                payload={
                    "decision_passed": decision.passed,
                    "needs_human_review": decision.needs_human_review,
                    "warnings": decision.warnings,
                    "violations": decision.violations,
                    "schedule_source": selection.source,
                    "schedule_local_hour": selection.local_hour,
                    "schedule_score": selection.score,
                },
            )
            jobs.append(job)
        return jobs

    def execute_job(self, channel: ChannelProfile, job: UploadJob) -> UploadJob:
        if job.status in {JobStatus.PRECHECK_FAILED, JobStatus.NEEDS_REVIEW}:
            self._record_event(
                "job_skipped",
                channel,
                job,
                payload={"reason": f"status={job.status.value}"},
            )
            return job
        media_path = Path(job.media.media_path)
        if not media_path.exists() or media_path.stat().st_size == 0:
            job.status = JobStatus.NEEDS_REVIEW
            job.last_error = (
                "Rendered media is missing/empty. Attach real source clips before upload execution."
            )
            self.deps.job_store.upsert_job(job)
            self._record_event(
                "job_needs_review",
                channel,
                job,
                payload={"reason": "media_missing_or_empty", "media_path": job.media.media_path},
            )
            return job

        try:
            job.status = JobStatus.UPLOADING
            self.deps.job_store.upsert_job(job)
            self._record_event("job_uploading", channel, job)
            upload_result = self.deps.uploader.upload_private(channel, job)
            job.video_id = upload_result.video_id
            job.status = JobStatus.PROCESSING
            self.deps.job_store.upsert_job(job)
            self._record_event(
                "job_uploaded_private",
                channel,
                job,
                payload={"upload_response": upload_result.upload_response},
            )

            monitor_result = self.deps.monitor.monitor_until_terminal(channel, upload_result.video_id)
            decision = monitor_result.decision
            self._record_event(
                "job_monitor_result",
                channel,
                job,
                payload={
                    "monitor_decision": {
                        "terminal_status": decision.terminal_status,
                        "ready_to_publish": decision.ready_to_publish,
                        "needs_retry": decision.needs_retry,
                        "needs_human_review": decision.needs_human_review,
                        "reasons": decision.reasons,
                    },
                    "latest_resource": monitor_result.latest_resource,
                },
            )
            if decision.ready_to_publish:
                job.status = JobStatus.PUBLISHED
                self.deps.job_store.upsert_job(job)
                self._record_event("job_published", channel, job)
                return job

            if decision.needs_retry:
                action = self.deps.remediation.remediate_technical_failure(job)
                if action.action_type == "retry_upload" and action.remediated_media_path:
                    job.media.media_path = action.remediated_media_path
                    job.retry_count += 1
                    job.status = JobStatus.QUEUED
                    self.deps.job_store.upsert_job(job)
                    self._record_event(
                        "job_retry_queued",
                        channel,
                        job,
                        payload={
                            "next_media_path": action.remediated_media_path,
                            "next_attempt_at_utc": (
                                action.next_attempt_at_utc.isoformat()
                                if action.next_attempt_at_utc
                                else None
                            ),
                        },
                    )
                    return job
                job.status = JobStatus.NEEDS_REVIEW
                job.last_error = action.summary
                self.deps.job_store.upsert_job(job)
                self._record_event(
                    "job_needs_review",
                    channel,
                    job,
                    payload={"reason": action.summary},
                )
                return job

            if decision.needs_human_review:
                job.status = JobStatus.NEEDS_REVIEW
                job.last_error = "; ".join(decision.reasons)
                self.deps.job_store.upsert_job(job)
                self._record_event(
                    "job_needs_review",
                    channel,
                    job,
                    payload={"reason": job.last_error},
                )
                return job
        except YouTubeUploadError as exc:
            job.status = JobStatus.NEEDS_REVIEW if exc.requires_channel_onboarding else JobStatus.FAILED
            job.last_error = str(exc)
            self.deps.job_store.upsert_job(job)
            self._record_event(
                "job_upload_error",
                channel,
                job,
                payload={
                    "requires_channel_onboarding": exc.requires_channel_onboarding,
                    "error": str(exc),
                },
            )
            return job
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.last_error = str(exc)
            self.deps.job_store.upsert_job(job)
            self._record_event("job_failed", channel, job, payload={"error": str(exc)})
            return job

        job.status = JobStatus.FAILED
        job.last_error = "Unknown terminal branch."
        self.deps.job_store.upsert_job(job)
        self._record_event("job_failed", channel, job, payload={"error": job.last_error})
        return job
