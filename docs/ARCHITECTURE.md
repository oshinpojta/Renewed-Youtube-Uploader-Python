# Architecture Overview

The implementation follows a compliance-first pipeline:

1. **Trend Intel** (`src/orchestrator/trend_intel.py`)
2. **Niche Planner** (`src/orchestrator/niche_planner.py`)
3. **Media Factory** (`src/media/factory.py`)
4. **Pre-upload Compliance** (`src/compliance/pre_upload.py`)
5. **Upload Time Scheduler** (`src/orchestrator/upload_scheduler.py`)
6. **YouTube Uploader** (`src/youtube/uploader.py`)
7. **Post-upload Monitor** (`src/youtube/monitor.py`)
8. **Remediation Engine** (`src/compliance/remediation.py`)
9. **Stores and Event Logs** (`src/storage/job_store.py`, `src/storage/token_store.py`, `src/storage/event_logger.py`)
10. **Metrics Collector** (`src/orchestrator/metrics_collector.py`)

## Data flow

- `config/*.yaml` define channels, niches, and deployment options.
- `src/main.py plan` creates jobs and persists them in `data/jobs.db`.
- `src/main.py run-once` runs planning + upload/monitor loop.
- `src/main.py collect-metrics` captures current YouTube video snapshots into DB and JSONL.
- Failed technical processing is remediated via re-encode.
- Policy-risk outcomes are routed to human review.
