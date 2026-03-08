from __future__ import annotations

import argparse
from pathlib import Path

from src.compliance.constraints import list_constraints


def build_pipeline(workspace_root: Path):
    from src.content.script_builder import ScriptBuilder
    from src.content.story_builder import StoryBuilder
    from src.content.text_router import TextGenerationRouter
    from src.compliance.pre_upload import PreUploadComplianceChecker
    from src.compliance.remediation import RemediationEngine
    from src.config.loader import (
        load_channels,
        load_model_api_keys,
        load_model_generation_strategy,
        load_niches,
        load_research_api_keys,
        load_research_provider_strategy,
        load_text_api_keys,
        load_text_generation_strategy,
    )
    from src.media.factory import MediaFactory, MediaFactoryConfig
    from src.media.model_router import ModelProviderRouter
    from src.media.video_generation_service import VideoGenerationService
    from src.niches.engine import build_engine_map
    from src.orchestrator.niche_planner import NichePlanner
    from src.orchestrator.pipeline import ComplianceFirstPipeline, PipelineDependencies
    from src.orchestrator.trend_intel import TrendIntelCollector
    from src.orchestrator.upload_scheduler import UploadTimeScheduler
    from src.research.grounding import ResearchGroundingService
    from src.research.research_router import ResearchRouter
    from src.storage.event_logger import PipelineEventLogger
    from src.storage.job_store import JobStore
    from src.storage.token_store import EncryptedTokenStore
    from src.youtube.auth import YouTubeAuthManager
    from src.youtube.monitor import YouTubePostPublishMonitor
    from src.youtube.uploader import YouTubeUploader

    channels = load_channels(workspace_root / "config" / "channels.yaml")
    niches = load_niches(workspace_root / "config" / "niches.yaml")
    model_strategy = load_model_generation_strategy(
        workspace_root / "config" / "model_provider_strategy.yaml"
    )
    model_api_keys = load_model_api_keys(
        workspace_root / "config" / "model_api_keys.local.yaml"
    )
    text_strategy = load_text_generation_strategy(
        workspace_root / "config" / "text_provider_strategy.yaml"
    )
    text_api_keys = load_text_api_keys(workspace_root / "config" / "text_api_keys.local.yaml")
    research_strategy = load_research_provider_strategy(
        workspace_root / "config" / "research_provider_strategy.yaml"
    )
    research_api_keys = load_research_api_keys(
        workspace_root / "config" / "research_api_keys.local.yaml"
    )
    model_router = ModelProviderRouter(model_strategy, model_api_keys)
    text_router = TextGenerationRouter(text_strategy, text_api_keys)
    research_router = ResearchRouter(
        strategy=research_strategy,
        credentials=research_api_keys,
        grounding=ResearchGroundingService(),
    )
    video_generation_service = VideoGenerationService(
        output_dir=workspace_root / "outputs",
        credentials=model_api_keys,
    )

    engine_map = build_engine_map(niches)
    token_store = EncryptedTokenStore(
        root=workspace_root / "data" / "tokens",
        key_file=workspace_root / "data" / "tokens" / ".key",
    )
    auth_manager = YouTubeAuthManager(token_store)
    event_logger = PipelineEventLogger(workspace_root / "data" / "logs")
    job_store = JobStore(workspace_root / "data" / "jobs.db")
    deps = PipelineDependencies(
        trend_intel=TrendIntelCollector(research_router=research_router),
        niche_planner=NichePlanner(engine_map),
        media_factory=MediaFactory(
            MediaFactoryConfig(
                workspace_root=workspace_root,
                output_dir=workspace_root / "outputs",
                enable_ffmpeg=False,
                enable_model_generation=True,
                model_router=model_router,
                video_generation_service=video_generation_service,
            )
        ),
        research_router=research_router,
        story_builder=StoryBuilder(text_router),
        script_builder=ScriptBuilder(text_router),
        pre_upload_checker=PreUploadComplianceChecker(),
        scheduler=UploadTimeScheduler(),
        job_store=job_store,
        event_logger=event_logger,
        uploader=YouTubeUploader(auth_manager),
        monitor=YouTubePostPublishMonitor(auth_manager),
        remediation=RemediationEngine(max_retries=2),
    )
    return ComplianceFirstPipeline(deps), channels


def _filtered_channels(channels, channel_id: str | None):
    for channel in channels:
        if channel_id and channel.channel_profile_id != channel_id:
            continue
        yield channel


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


def cmd_model_strategy(workspace_root: Path) -> None:
    from src.config.loader import load_model_api_keys, load_model_generation_strategy, load_niches
    from src.media.model_router import ModelProviderRouter

    niches = load_niches(workspace_root / "config" / "niches.yaml")
    strategy = load_model_generation_strategy(
        workspace_root / "config" / "model_provider_strategy.yaml"
    )
    api_keys = load_model_api_keys(workspace_root / "config" / "model_api_keys.local.yaml")
    router = ModelProviderRouter(strategy, api_keys)

    for niche_id in niches.keys():
        selection = router.select_for_niche(niche_id=niche_id, duration_seconds=10, require_audio=True)
        print(
            f"{niche_id}: provider={selection.provider} model={selection.model or 'n/a'} "
            f"estimated_cost_usd={selection.estimated_cost_usd:.2f}"
        )
        for note in selection.notes:
            print(f"  - {note}")


def cmd_research_preview(
    workspace_root: Path,
    channel_id: str | None,
    niche_id: str | None,
    query: str | None,
) -> None:
    pipeline, channels = build_pipeline(workspace_root)
    for channel in _filtered_channels(channels, channel_id):
        blueprints = {
            current_niche_id: engine.blueprint
            for current_niche_id, engine in pipeline.deps.niche_planner.engines.items()
        }
        trend_map = pipeline.deps.trend_intel.collect(blueprints)
        print(f"{channel.channel_profile_id}:")
        for current_niche_id in channel.niches:
            if niche_id and current_niche_id != niche_id:
                continue
            seeds = trend_map.get(current_niche_id, [])
            if not seeds:
                print(f"  - {current_niche_id}: no seeds")
                continue
            search_query = query or seeds[0].keyword
            if not pipeline.deps.research_router:
                print(f"  - {current_niche_id}: research router disabled")
                continue
            routed = pipeline.deps.research_router.search_for_niche(
                niche_id=current_niche_id,
                query=search_query,
                max_results=5,
            )
            print(f"  - {current_niche_id}: provider={routed.bundle.provider} query={search_query}")
            for hit in routed.bundle.hits[:5]:
                print(f"      * {hit.title} -> {hit.url}")


def cmd_script_preview(
    workspace_root: Path,
    channel_id: str | None,
    niche_id: str | None,
) -> None:
    from src.content.script_builder import ScriptBuildInput
    from src.research.grounding import ResearchGroundingService

    pipeline, channels = build_pipeline(workspace_root)
    grounding = ResearchGroundingService()
    for channel in _filtered_channels(channels, channel_id):
        blueprints = {
            current_niche_id: engine.blueprint
            for current_niche_id, engine in pipeline.deps.niche_planner.engines.items()
        }
        trend_map = pipeline.deps.trend_intel.collect(blueprints)
        print(f"{channel.channel_profile_id}:")
        for current_niche_id in channel.niches:
            if niche_id and current_niche_id != niche_id:
                continue
            engine = pipeline.deps.niche_planner.engines.get(current_niche_id)
            seeds = trend_map.get(current_niche_id, [])
            if not engine or not seeds:
                print(f"  - {current_niche_id}: missing engine or seed")
                continue
            brief = engine.build_brief(channel.channel_profile_id, seeds[0])
            citations = list(brief.evidence_links)
            snippets = []
            if pipeline.deps.research_router:
                routed = pipeline.deps.research_router.search_for_niche(
                    niche_id=current_niche_id,
                    query=seeds[0].keyword,
                    max_results=5,
                )
                citations = list(dict.fromkeys(citations + grounding.citation_urls(routed.bundle.hits, limit=5)))
                snippets = grounding.citation_snippets(routed.bundle.hits, limit=5)
            if not pipeline.deps.story_builder or not pipeline.deps.script_builder:
                print(f"  - {current_niche_id}: story/script builders are disabled")
                continue
            story = pipeline.deps.story_builder.build_story(brief=brief, citation_summaries=snippets)
            script = pipeline.deps.script_builder.build(
                ScriptBuildInput(
                    brief=brief,
                    story=story,
                    citations=citations,
                    citation_snippets=snippets,
                )
            )
            print(
                f"  - {current_niche_id}: provider={script.text_provider} scenes={len(script.scenes)} title={script.title}"
            )
            for scene in script.scenes[:4]:
                print(f"      * {scene.scene_id}: {scene.narration}")


def cmd_render_preview(
    workspace_root: Path,
    channel_id: str | None,
    niche_id: str | None,
) -> None:
    from src.content.script_builder import ScriptBuildInput
    from src.research.grounding import ResearchGroundingService

    pipeline, channels = build_pipeline(workspace_root)
    grounding = ResearchGroundingService()
    for channel in _filtered_channels(channels, channel_id):
        blueprints = {
            current_niche_id: engine.blueprint
            for current_niche_id, engine in pipeline.deps.niche_planner.engines.items()
        }
        trend_map = pipeline.deps.trend_intel.collect(blueprints)
        print(f"{channel.channel_profile_id}:")
        for current_niche_id in channel.niches:
            if niche_id and current_niche_id != niche_id:
                continue
            engine = pipeline.deps.niche_planner.engines.get(current_niche_id)
            seeds = trend_map.get(current_niche_id, [])
            if not engine or not seeds:
                print(f"  - {current_niche_id}: missing engine or seed")
                continue
            brief = engine.build_brief(channel.channel_profile_id, seeds[0])
            citations = list(brief.evidence_links)
            snippets = []
            if pipeline.deps.research_router:
                routed = pipeline.deps.research_router.search_for_niche(
                    niche_id=current_niche_id,
                    query=seeds[0].keyword,
                    max_results=5,
                )
                citations = list(dict.fromkeys(citations + grounding.citation_urls(routed.bundle.hits, limit=5)))
                snippets = grounding.citation_snippets(routed.bundle.hits, limit=5)
            brief.evidence_links = citations

            generated_script = None
            if pipeline.deps.story_builder and pipeline.deps.script_builder:
                story = pipeline.deps.story_builder.build_story(brief=brief, citation_summaries=snippets)
                generated_script = pipeline.deps.script_builder.build(
                    ScriptBuildInput(
                        brief=brief,
                        story=story,
                        citations=citations,
                        citation_snippets=snippets,
                    )
                )

            media = pipeline.deps.media_factory.render(
                brief=brief,
                source_clips=[],
                generated_script=generated_script,
            )
            print(
                f"  - {current_niche_id}: mode={media.generation_mode} "
                f"provider={media.generation_provider} path={media.media_path}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compliance-first multi-channel YouTube automation.")
    parser.add_argument("--workspace-root", default=".", help="Workspace root path.")
    parser.add_argument("--channel-id", default=None, help="Optional channel_profile_id filter.")
    parser.add_argument("--niche-id", default=None, help="Optional niche_id filter for preview commands.")
    parser.add_argument("--query", default=None, help="Optional search query for research-preview.")
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
            "model-strategy",
            "research-preview",
            "script-preview",
            "render-preview",
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
    elif args.command == "model-strategy":
        cmd_model_strategy(workspace_root)
    elif args.command == "research-preview":
        cmd_research_preview(workspace_root, args.channel_id, args.niche_id, args.query)
    elif args.command == "script-preview":
        cmd_script_preview(workspace_root, args.channel_id, args.niche_id)
    elif args.command == "render-preview":
        cmd_render_preview(workspace_root, args.channel_id, args.niche_id)
    else:
        cmd_run_once(workspace_root, args.channel_id)


if __name__ == "__main__":
    main()
