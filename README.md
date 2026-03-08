# Renewed YouTube Uploader (Compliance-First, Multi-Channel)

This repository now implements an API-first YouTube automation system that:

- plans videos for multiple niches,
- routes jobs to multiple channel accounts,
- schedules publish times using channel windows + fallback strategy,
- enforces pre-upload and post-upload compliance checks,
- and applies safe remediation for technical failures.

The previous UI-click automation scripts are preserved as compatibility wrappers, but execution is now centered on the `src/` modular pipeline.

## Core Goals

- Build original, non-repetitive content workflows for multiple niches.
- Support multi-account channel operations with OAuth token isolation.
- Respect YouTube policies and API constraints by design.
- Stay budget-friendly (`$0-$25/month`) with local, hybrid, and hosted profiles.

## New Architecture

Pipeline modules are organized by responsibility:

- `src/orchestrator/`  
  Trend intake, niche planning, slot scheduling, pipeline execution.
- `src/niches/`  
  Niche brief engines and content template logic.
- `src/compliance/`  
  Constraints, pre-upload checks, post-upload checks, remediation.
- `src/youtube/`  
  OAuth auth manager, uploader, onboarding handling, processing monitor.
- `src/storage/`  
  SQLite job/performance store and encrypted token store.
- `src/media/`  
  Media factory, model routing, provider adapters, and async generation service.
- `src/content/`  
  Text provider routing + storyline/script generation.
- `src/research/`  
  Web search provider routing, grounding, and citation extraction.
- `src/config/`  
  Typed config models and YAML loaders.

## Niche Engines (6)

1. Roblox and UGC explainers
2. AI workflow micro tutorials
3. Internet culture context
4. Practical law and safety scenarios
5. Public-domain micro documentaries
6. Religion, culture, legends, and ghost lore (sensitive-topic guarded)

Niche definitions live in `config/niches.yaml`.

## Compliance-First Rules Implemented

- No direct YouTube channel create endpoint assumptions.
- Private-first upload strategy.
- No blind policy-evasion retries.
- Rights/originality/metadata checks before upload.
- `containsSyntheticMedia` support for altered/synthetic disclosure.
- Sensitive-topic language and disclaimer guardrails for religion/legend/ghost content.

See: `docs/CONSTRAINTS.md` and `docs/COMPLIANCE_WORKFLOW.md`.

## Repository Layout

```text
.
|- src/
|  |- main.py
|  |- orchestrator/
|  |- niches/
|  |- compliance/
|  |- youtube/
|  |- storage/
|  |- media/
|  |- content/
|  |- research/
|  |- config/
|- config/
|  |- channels.yaml
|  |- niches.yaml
|  |- deployment_profiles.yaml
|  |- model_provider_strategy.yaml
|  |- model_api_keys.local.example.yaml
|  |- text_provider_strategy.yaml
|  |- research_provider_strategy.yaml
|  |- text_api_keys.local.example.yaml
|  |- research_api_keys.local.example.yaml
|- docs/
|  |- ARCHITECTURE.md
|  |- GETTING_STARTED_LOCAL_AND_CLOUD.md
|  |- CONSTRAINTS.md
|  |- COMPLIANCE_WORKFLOW.md
|  |- MODEL_ADAPTER_STRATEGY.md
|  |- CONTENT_GENERATION_AND_RESEARCH.md
|  |- LOGGING_AND_METRICS.md
|  |- SCHEDULING.md
|  |- OAUTH_ONBOARDING.md
|  |- BUDGET_OPTIONS.md
|  |- IMPLEMENTATION_PHASES.md
|  |- MIGRATION.md
|- scripts/
|  |- run_pipeline.py
|  |- local_first.bat
|  |- hybrid_plan.bat
|- tiktok.py   (legacy wrapper -> new pipeline)
|- reddit.py   (legacy wrapper -> new pipeline)
|- insta.py    (legacy wrapper -> new pipeline)
|- schedule.py (legacy wrapper -> APScheduler + new pipeline)
|- requirements.txt
```

## Installation

For full startup and deployment steps, see:

- `docs/GETTING_STARTED_LOCAL_AND_CLOUD.md`

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

### 1) Channels

Edit `config/channels.yaml`:

- `channel_profile_id` (unique key)
- `oauth_client_secrets_file`
- `token_store_key` (one encrypted token per channel profile)
- `timezone`
- allowed `niches`
- `schedule_windows` + `fallback_hours`

### 2) Niches

Edit `config/niches.yaml` for:

- formats
- trend triggers
- source policy
- style rules
- sensitive-topic flag

### 3) Deployment profile metadata

See `config/deployment_profiles.yaml`.

### 4) Text generation providers

Configure:

- `config/text_provider_strategy.yaml`
- `config/text_api_keys.local.yaml` (local, git-ignored)
- `config/text_api_keys.local.example.yaml` (template)

### 5) Research providers

Configure:

- `config/research_provider_strategy.yaml`
- `config/research_api_keys.local.yaml` (local, git-ignored)
- `config/research_api_keys.local.example.yaml` (template)

## Commands

### Print non-negotiable constraints

```bash
python -m src.main constraints
```

### Authorize one channel profile (OAuth)

```bash
python -m src.main onboard --channel-id channel_culture_trends
```

### Plan jobs only (no upload)

```bash
python -m src.main plan
```

### Run planning + upload flow once

```bash
python -m src.main run-once
```

Note: if no real rendered media is attached yet, jobs are automatically routed to `needs_review` instead of uploading empty files.

### Show budget deployment options

```bash
python -m src.main budget
```

### Show per-channel pipeline metrics

```bash
python -m src.main metrics
```

### Collect latest YouTube video metric snapshots

```bash
python -m src.main collect-metrics
```

Optional single channel:

```bash
python -m src.main collect-metrics --channel-id channel_culture_trends
```

### Inspect provider adapter strategy (priority/fallback/cost checks)

```bash
python -m src.main model-strategy
```

### Preview web-research grounding (no upload)

```bash
python -m src.main research-preview --channel-id channel_culture_trends
```

### Preview generated scripts (no upload)

```bash
python -m src.main script-preview --channel-id channel_culture_trends
```

### Preview render output path/mode (no upload)

```bash
python -m src.main render-preview --channel-id channel_culture_trends
```

## Logs and Analytics Data

Detailed logs are now generated for planning, uploads, monitoring, retries, and metrics collection.

- JSONL logs:
  - `data/logs/pipeline_events.jsonl`
  - `data/logs/video_metrics.jsonl`
- SQLite tables:
  - `jobs`
  - `job_events`
  - `video_metric_snapshots`
  - `performance_metrics`

See `docs/LOGGING_AND_METRICS.md` for field details and analysis usage.

## Model Adapter Strategy

The media layer now supports configurable model selection with:

- `provider_priority`
- fallback order
- per-niche provider order
- provider-level cost guardrails

Use:

- `config/model_provider_strategy.yaml`
- `config/model_api_keys.local.yaml` (local, git-ignored)
- `config/model_api_keys.local.example.yaml` (template)

See `docs/MODEL_ADAPTER_STRATEGY.md` for full setup.

Text and research generation are configured separately with:

- `config/text_provider_strategy.yaml`
- `config/research_provider_strategy.yaml`
- `config/text_api_keys.local.yaml` / `config/text_api_keys.local.example.yaml`
- `config/research_api_keys.local.yaml` / `config/research_api_keys.local.example.yaml`

See `docs/CONTENT_GENERATION_AND_RESEARCH.md` for full setup and fallback behavior.

## Scheduling Strategy

Implemented in `src/orchestrator/upload_scheduler.py`:

- uses channel-local weekly windows,
- applies fallback slots,
- scores candidate hours by historical CTR/retention,
- and selects best slot with earliest tie-break.

## Legacy Wrappers

Legacy filenames remain for compatibility:

- `tiktok.py` -> `channel_gaming_tech`
- `reddit.py` -> `channel_culture_trends`
- `insta.py` -> `channel_practical_safety`
- `schedule.py` -> all channels every 12 hours

## Budget Guidance

- Local-first: `~$0-$5`
- Hybrid low-cost: `~$5-$20`
- Hosted budget cap: `~$10-$25`

See `docs/BUDGET_OPTIONS.md` for details.

## Important Policy Note

This system is built to reduce policy risk, not to bypass platform enforcement.  
Any policy-risk, copyright-risk, or ambiguous moderation outcome is routed to human review.
