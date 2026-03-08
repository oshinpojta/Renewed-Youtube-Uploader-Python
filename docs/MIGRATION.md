# Legacy to Modular Migration

## Legacy entrypoints retained as wrappers

- `tiktok.py` -> runs `src.main run-once --channel-id channel_gaming_tech`
- `reddit.py` -> runs `src.main run-once --channel-id channel_culture_trends`
- `insta.py` -> runs `src.main run-once --channel-id channel_practical_safety`
- `schedule.py` -> runs all channels every 12 hours using APScheduler

## New package layout

- `src/config/` typed config models and loaders
- `src/niches/` six niche brief engines
- `src/compliance/` constraints, pre/post checks, remediation
- `src/orchestrator/` trend intel, planner, scheduler, pipeline
- `src/youtube/` OAuth + uploader + monitor
- `src/storage/` encrypted token store + SQLite job store
- `src/media/` media render factory (FFmpeg-ready)
- `data/logs/` JSONL telemetry (`pipeline_events.jsonl`, `video_metrics.jsonl`)

## Legacy files removed as not required

- Old counter files: `CountSearch*.txt`, `CountTiktokVid*.txt`
- Old text log: `log.txt`
- Old sleep/wake helpers: `sleep.bat`, `wake.bat`
- Old browser driver artifact: `chromedriver.exe`

## Immediate run commands

- Plan jobs:
  - `python -m src.main plan`
- Run once (all channels):
  - `python -m src.main run-once`
- List policy constraints:
  - `python -m src.main constraints`
- Authorize one account/channel profile:
  - `python -m src.main onboard --channel-id <channel_profile_id>`
- Collect YouTube metric snapshots:
  - `python -m src.main collect-metrics`
