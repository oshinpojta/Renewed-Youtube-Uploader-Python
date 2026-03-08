# Logging and Metrics

This project now records detailed pipeline logs and YouTube metric snapshots to support niche/channel optimization over time.

## Log files

Runtime logs are written under `data/logs/`:

- `pipeline_events.jsonl`
  - One JSON object per pipeline event.
  - Captures planning, upload, monitor, retry, review, and failure stages.
- `video_metrics.jsonl`
  - One JSON object per collected video snapshot.
  - Captures key YouTube performance fields for each video.

## Database tables

Stored in `data/jobs.db`:

- `jobs`  
  Current job state and metadata.
- `job_events`  
  Structured event history by `job_id`, `channel_profile_id`, and `niche_id`.
- `video_metric_snapshots`  
  Periodic snapshots of views/likes/comments/duration by video.
  Includes `text_provider`, `research_provider`, `generation_provider`, `generation_model`, and `citation_count`.
- `performance_metrics`  
  Internal CTR/retention aggregates used by the scheduler.

## Pipeline event fields (high-value)

Typical event payload includes:

- `timestamp_utc`
- `event_type`
- `channel_profile_id`, `channel_name`
- `job_id`, `video_id`, `niche_id`, `brief_id`
- `title`, `seed_keyword`
- `generation_provider`, `generation_model`, `generation_mode`
- `generation_task_id`, `render_latency_seconds`
- `text_provider`, `research_provider`, `citation_count`
- `script_id`, `script_scene_count`
- `scheduled_publish_at_utc`
- `status`, `retry_count`
- `duration_seconds`, `aspect_ratio`
- `contains_synthetic_media`
- stage-specific payload such as upload response, monitor decisions, and remediation outcomes

## Metrics collection command

Collect latest YouTube snapshots for already uploaded videos:

```bash
python -m src.main collect-metrics
```

Optional per-channel:

```bash
python -m src.main collect-metrics --channel-id channel_culture_trends
```

## Why this helps algorithm optimization

With channel+niche+publish-time level telemetry, you can:

- compare average views/likes/comments per niche
- compare text/research/video provider combinations by niche
- measure the impact of publish hour and day windows
- detect low-performing metadata patterns early
- identify which niches deserve more volume or format shifts
- feed future ranking models for topic and timing recommendations
