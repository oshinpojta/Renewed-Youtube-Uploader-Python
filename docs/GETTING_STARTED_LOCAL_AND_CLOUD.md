# Getting Started (Local and Cloud)

This guide explains how to start the project, run it locally, and deploy it in cloud environments.

## 1) What this project currently does

- Plans content jobs by niche and channel configuration.
- Runs compliance checks before upload.
- Schedules upload times with channel windows and fallback slots.
- Uploads through YouTube Data API (private-first flow).
- Logs detailed pipeline events and video metrics snapshots.

## 2) Prerequisites

- Python 3.9+
- `pip`
- YouTube API OAuth client file (`client_secrets.json`)
- FFmpeg (recommended when you enable real rendering)

Install FFmpeg:

- Windows: install FFmpeg and add to PATH.
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt-get install ffmpeg`

## 3) Local setup

### 3.1 Create environment and install dependencies

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2 Configure channels and niches

Edit:

- `config/channels.yaml`
- `config/niches.yaml`
- `config/model_provider_strategy.yaml`
- `config/text_provider_strategy.yaml`
- `config/research_provider_strategy.yaml`

Create local model API keys file:

```bash
cp config/model_api_keys.local.example.yaml config/model_api_keys.local.yaml
```

Create local text/research API key files:

```bash
cp config/text_api_keys.local.example.yaml config/text_api_keys.local.yaml
cp config/research_api_keys.local.example.yaml config/research_api_keys.local.yaml
```

Then fill provider API keys in:

- `config/model_api_keys.local.yaml`
- `config/text_api_keys.local.yaml`
- `config/research_api_keys.local.yaml`

This file is git-ignored and intended for local secrets only.

At minimum ensure each channel has:

- `channel_profile_id`
- `oauth_client_secrets_file`
- `token_store_key`
- `timezone`
- `niches`

### 3.3 OAuth onboarding per channel

Authorize each channel profile once:

```bash
python -m src.main onboard --channel-id <channel_profile_id>
```

### 3.4 Validate setup

```bash
python -m src.main constraints
python -m src.main plan
python -m src.main model-strategy
python -m src.main research-preview --channel-id channel_culture_trends
python -m src.main script-preview --channel-id channel_culture_trends
python -m src.main render-preview --channel-id channel_culture_trends
```

### 3.5 Run pipeline once

```bash
python -m src.main run-once
```

### 3.6 Collect and inspect metrics

```bash
python -m src.main collect-metrics
python -m src.main metrics
```

## 4) Local scheduling options

### Option A: Use Python scheduler wrapper

```bash
python schedule.py
```

### Option B: OS scheduler (recommended for production-like local runs)

- Windows Task Scheduler -> command:
  - `python -m src.main run-once`
- Linux/macOS cron example:
  - `0 */6 * * * cd /path/to/repo && .venv/bin/python -m src.main run-once`

## 5) Cloud deployment patterns

Current code is CLI-first (not a web service).  
So deploy it as a scheduled worker/job that runs commands.

### Pattern 1: Single cloud VM (simplest and stable)

1. Provision VM.
2. Clone repo and install dependencies.
3. Place `client_secrets.json` securely.
4. Run initial onboarding flow (or securely transfer encrypted tokens from trusted setup).
5. Set cron/systemd timer for:
   - `python -m src.main run-once`
6. Set another schedule for:
   - `python -m src.main collect-metrics`

### Pattern 2: Hybrid (local rendering + cloud orchestration)

- Cloud scheduler triggers planning and metrics jobs.
- Local machine performs render-heavy work and upload runs.
- Useful for low budget and limited cloud compute.

### Pattern 3: Hosted worker platform (budget-limited)

- Run the same CLI command in a scheduled worker/job:
  - `python -m src.main run-once`
- Store logs and DB backups persistently.
- Run periodic metrics command for analytics refresh.

## 6) Required runtime files in any environment

- `config/channels.yaml`
- `config/niches.yaml`
- `config/deployment_profiles.yaml`
- `config/text_provider_strategy.yaml`
- `config/research_provider_strategy.yaml`
- `client_secrets.json`
- `data/tokens/` (after onboarding)

## 7) Logging and analytics outputs

- JSON logs:
  - `data/logs/pipeline_events.jsonl`
  - `data/logs/video_metrics.jsonl`
- SQLite:
  - `data/jobs.db`

These are the main sources for future niche optimization and algorithm analysis.

## 8) Important operational note

If rendered media is missing or empty, jobs are automatically moved to `needs_review` and not uploaded.  
This protects channel quality and prevents invalid uploads.
