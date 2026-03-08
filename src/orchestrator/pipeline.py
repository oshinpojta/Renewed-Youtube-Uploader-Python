from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from src.content.script_builder import ScriptBuildInput, ScriptBuilder
from src.content.story_builder import StoryBuilder
from src.compliance.pre_upload import PreUploadComplianceChecker, PreUploadContext, build_recent_title_set
from src.compliance.remediation import RemediationEngine
from src.config.models import ChannelProfile, JobStatus, UploadJob
from src.media.factory import MediaFactory
from src.orchestrator.niche_planner import NichePlanner
from src.orchestrator.trend_intel import TrendIntelCollector
from src.orchestrator.upload_scheduler import UploadTimeScheduler
from src.research.grounding import ResearchGroundingService
from src.research.research_router import ResearchRouter
from src.storage.event_logger import PipelineEventLogger
from src.storage.job_store import JobStore
from src.youtube.monitor import YouTubePostPublishMonitor
from src.youtube.uploader import YouTubeUploadError, YouTubeUploader


@dataclass
class PipelineDependencies:
    trend_intel: TrendIntelCollector
    niche_planner: NichePlanner
    media_factory: MediaFactory
    research_router: ResearchRouter | None
    story_builder: StoryBuilder | None
    script_builder: ScriptBuilder | None
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
        grounding = ResearchGroundingService()

        for brief in briefs:
            research_provider = "none"
            research_notes: List[str] = []
            citation_urls = list(brief.evidence_links)
            citation_snippets: List[str] = []
            if self.deps.research_router:
                query = f"{brief.seed_keyword} {brief.niche_id.replace('_', ' ')}"
                routed_research = self.deps.research_router.search_for_niche(
                    niche_id=brief.niche_id,
                    query=query,
                    max_results=5,
                )
                research_provider = routed_research.bundle.provider
                research_notes = list(routed_research.bundle.notes)
                citation_urls = list(
                    dict.fromkeys(
                        citation_urls + grounding.citation_urls(routed_research.bundle.hits, limit=5)
                    )
                )
                citation_snippets = grounding.citation_snippets(routed_research.bundle.hits, limit=5)
            brief.evidence_links = citation_urls

            generated_script = None
            text_provider = "template"
            text_notes: List[str] = []
            if self.deps.story_builder and self.deps.script_builder:
                story = self.deps.story_builder.build_story(
                    brief=brief,
                    citation_summaries=citation_snippets,
                )
                generated_script = self.deps.script_builder.build(
                    ScriptBuildInput(
                        brief=brief,
                        story=story,
                        citations=citation_urls,
                        citation_snippets=citation_snippets,
                    )
                )
                text_provider = generated_script.text_provider
                text_notes = list(generated_script.generation_notes)

            media = self.deps.media_factory.render(
                brief,
                source_clips=[],
                generated_script=generated_script,
            )
            min_citations = 2 if brief.niche_id in {
                "niche_c_internet_culture_context",
                "niche_d_practical_law_and_safety",
                "niche_e_micro_doc_public_domain",
                "niche_f_religion_culture_legends_ghost_lore",
            } else 1
            decision = self.deps.pre_upload_checker.evaluate(
                brief=brief,
                media=media,
                generated_script=generated_script,
                context=PreUploadContext(
                    recent_titles=recent_titles,
                    require_source_credits=True,
                    min_citation_count=min_citations,
                ),
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
            title = generated_script.title if generated_script else brief.working_title
            if generated_script and generated_script.scenes:
                outline_for_description = [scene.narration for scene in generated_script.scenes]
            else:
                outline_for_description = brief.outline
            description_lines = outline_for_description + [""]
            if citation_urls:
                description_lines += ["Sources:"] + citation_urls[:5] + [""]
            description_lines += brief.disclaimers
            metadata = {
                "title": title,
                "description": "\n".join(description_lines),
                "tags": [brief.seed_keyword, brief.niche_id, "automation"],
                "category_id": "22",
                "compliance_warnings": "; ".join(decision.warnings),
                "compliance_violations": "; ".join(decision.violations),
                "schedule_source": selection.source,
                "schedule_local_hour": str(selection.local_hour),
                "schedule_score": f"{selection.score:.4f}",
                "text_provider": text_provider,
                "text_generation_notes": "; ".join(text_notes),
                "research_provider": research_provider,
                "research_notes": "; ".join(research_notes),
                "citation_count": len(citation_urls),
                "script_id": generated_script.script_id if generated_script else "",
                "script_scene_count": len(generated_script.scenes) if generated_script else 0,
                "generation_provider": media.generation_provider,
                "generation_model": media.generation_model,
                "generation_mode": media.generation_mode,
                "generation_notes": "; ".join(media.generation_notes),
                "video_generation_task_id": media.generation_task_id,
                "render_latency_seconds": media.render_latency_seconds,
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
                    "text_provider": text_provider,
                    "research_provider": research_provider,
                    "citation_count": len(citation_urls),
                    "generation_provider": media.generation_provider,
                    "generation_model": media.generation_model,
                    "generation_mode": media.generation_mode,
                    "generation_notes": media.generation_notes,
                    "video_generation_task_id": media.generation_task_id,
                    "render_latency_seconds": media.render_latency_seconds,
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
                            "retry_reason": "; ".join(decision.reasons),
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
