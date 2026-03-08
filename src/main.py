from __future__ import annotations

import argparse
from pathlib import Path

from src.compliance.constraints import list_constraints


def build_pipeline(workspace_root: Path):
    from src.compliance.pre_upload import PreUploadComplianceChecker
    from src.compliance.remediation import RemediationEngine
    from src.config.loader import load_channels, load_niches
    from src.media.factory import MediaFactory, MediaFactoryConfig
    from src.niches.engine import build_engine_map
    from src.orchestrator.niche_planner import NichePlanner
    from src.orchestrator.pipeline import ComplianceFirstPipeline, PipelineDependencies
    from src.orchestrator.trend_intel import TrendIntelCollector
    from src.orchestrator.upload_scheduler import UploadTimeScheduler
    from src.storage.event_logger import PipelineEventLogger
    from src.storage.job_store import JobStore
    from src.storage.token_store import EncryptedTokenStore
    from src.youtube.auth import YouTubeAuthManager
    from src.youtube.monitor import YouTubePostPublishMonitor
    from src.youtube.uploader import YouTubeUploader

    channels = load_channels(workspace_root / "config" / "channels.yaml")
    niches = load_niches(workspace_root / "config" / "niches.yaml")

    engine_map = build_engine_map(niches)
    token_store = EncryptedTokenStore(
        root=workspace_root / "data" / "tokens",
        key_file=workspace_root / "data" / "tokens" / ".key",
    )
    auth_manager = YouTubeAuthManager(token_store)
    event_logger = PipelineEventLogger(workspace_root / "data" / "logs")
    job_store = JobStore(workspace_root / "data" / "jobs.db")
    deps = PipelineDependencies(
        trend_intel=TrendIntelCollector(),
        niche_planner=NichePlanner(engine_map),
        media_factory=MediaFactory(
            MediaFactoryConfig(
                workspace_root=workspace_root,
                output_dir=workspace_root / "outputs",
                enable_ffmpeg=False,
            )
        ),
        pre_upload_checker=PreUploadComplianceChecker(),
        scheduler=UploadTimeScheduler(),
        job_store=job_store,
        event_logger=event_logger,
        uploader=YouTubeUploader(auth_manager),
        monitor=YouTubePostPublishMonitor(auth_manager),
        remediation=RemediationEngine(max_retries=2),
    )
    return ComplianceFirstPipeline(deps), channels


def cmd_constraints() -> None:
    for constraint in list_constraints():
        print(f"[{constraint.key}] {constraint.statement}")
        print(f"  safe alternative: {constraint.safe_alternative}")


def cmd_plan(workspace_root: Path, channel_id: str | None) -> None:
    pipeline, channels = build_pipeline(workspace_root)
    for channel in channels:
        if channel_id and channel.channel_profile_id != channel_id:
            continue
        jobs = pipeline.plan_jobs_for_channel(channel)
        print(f"{channel.channel_profile_id}: planned {len(jobs)} jobs")
        for job in jobs:
            print(f"  - {job.job_id} [{job.status.value}] {job.brief.working_title}")


def cmd_run_once(workspace_root: Path, channel_id: str | None) -> None:
    pipeline, channels = build_pipeline(workspace_root)
    for channel in channels:
        if channel_id and channel.channel_profile_id != channel_id:
            continue
        jobs = pipeline.plan_jobs_for_channel(channel)
        print(f"{channel.channel_profile_id}: executing {len(jobs)} planned jobs")
        for job in jobs:
            result = pipeline.execute_job(channel, job)
            print(f"  - {result.job_id} => {result.status.value}")
            if result.last_error:
                print(f"    error: {result.last_error}")


def cmd_onboard(workspace_root: Path, channel_id: str | None) -> None:
    from src.config.loader import load_channels
    from src.storage.token_store import EncryptedTokenStore
    from src.youtube.auth import YouTubeAuthManager

    channels = load_channels(workspace_root / "config" / "channels.yaml")
    auth_manager = YouTubeAuthManager(
        EncryptedTokenStore(
            root=workspace_root / "data" / "tokens",
            key_file=workspace_root / "data" / "tokens" / ".key",
        )
    )
    for channel in channels:
        if channel_id and channel.channel_profile_id != channel_id:
            continue
        auth_manager.authorize(channel)
        print(f"Authorized: {channel.channel_profile_id}")


def cmd_budget_profiles(workspace_root: Path) -> None:
    from src.config.loader import load_deployment_profiles

    profiles = load_deployment_profiles(workspace_root / "config" / "deployment_profiles.yaml")
    for profile in profiles.values():
        print(f"{profile.profile_id} | {profile.monthly_cost_range_usd} | {profile.title}")
        print(f"  fit: {profile.fit_for}")
        for component in profile.components:
            print(f"  - {component}")


def cmd_metrics(workspace_root: Path, channel_id: str | None) -> None:
    from src.config.loader import load_channels
    from src.orchestrator.metrics import MetricsService
    from src.storage.job_store import JobStore

    channels = load_channels(workspace_root / "config" / "channels.yaml")
    service = MetricsService(JobStore(workspace_root / "data" / "jobs.db"))
    for channel in channels:
        if channel_id and channel.channel_profile_id != channel_id:
            continue
        summary = service.summarize_channel(channel.channel_profile_id)
        print(f"{channel.channel_profile_id}:")
        print(f"  upload_success_rate={summary.upload_success_rate:.2%}")
        print(f"  needs_review_rate={summary.needs_review_rate:.2%}")
        print(f"  failure_rate={summary.failure_rate:.2%}")
        print(f"  tracked_videos={summary.tracked_videos:.0f}")
        print(f"  avg_views={summary.avg_views:.2f}")
        print(f"  avg_likes={summary.avg_likes:.2f}")
        print(f"  avg_comments={summary.avg_comments:.2f}")


def cmd_collect_metrics(workspace_root: Path, channel_id: str | None) -> None:
    from src.orchestrator.metrics_collector import MetricsCollector

    pipeline, channels = build_pipeline(workspace_root)
    collector = MetricsCollector(
        job_store=pipeline.deps.job_store,
        monitor=pipeline.deps.monitor,
        event_logger=pipeline.deps.event_logger,
    )
    for channel in channels:
        if channel_id and channel.channel_profile_id != channel_id:
            continue
        collected = collector.collect_for_channel(channel)
        print(f"{channel.channel_profile_id}: collected {collected} video metric snapshots")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compliance-first multi-channel YouTube automation.")
    parser.add_argument("--workspace-root", default=".", help="Workspace root path.")
    parser.add_argument("--channel-id", default=None, help="Optional channel_profile_id filter.")
    parser.add_argument(
        "command",
        choices=[
            "constraints",
            "plan",
            "run-once",
            "onboard",
            "budget",
            "metrics",
            "collect-metrics",
        ],
        help="Execution mode.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    workspace_root = Path(args.workspace_root).resolve()

    if args.command == "constraints":
        cmd_constraints()
    elif args.command == "plan":
        cmd_plan(workspace_root, args.channel_id)
    elif args.command == "onboard":
        cmd_onboard(workspace_root, args.channel_id)
    elif args.command == "budget":
        cmd_budget_profiles(workspace_root)
    elif args.command == "metrics":
        cmd_metrics(workspace_root, args.channel_id)
    elif args.command == "collect-metrics":
        cmd_collect_metrics(workspace_root, args.channel_id)
    else:
        cmd_run_once(workspace_root, args.channel_id)


if __name__ == "__main__":
    main()
