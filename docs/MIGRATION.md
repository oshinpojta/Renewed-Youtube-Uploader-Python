# Legacy to Modular Migration

## Legacy entrypoints removed

Legacy compatibility wrappers were removed from the workspace:

- `tiktok.py`
- `reddit.py`
- `insta.py`
- `schedule.py`

Use direct CLI commands instead:

- all channels once: `python -m src.main run-once`
- single channel once: `python -m src.main run-once --channel-id <channel_profile_id>`
- default end-to-end flow (preview + execute): `python -m src.main auto-run`

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

- Legacy wrappers: `tiktok.py`, `reddit.py`, `insta.py`, `schedule.py`
- Legacy helper scripts: `scripts/run_pipeline.py`, `scripts/local_first.bat`, `scripts/hybrid_plan.bat`
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
