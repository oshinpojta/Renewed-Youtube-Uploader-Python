# Upload Scheduling Strategy

Implemented in `src/orchestrator/upload_scheduler.py`.

## Inputs

- Channel timezone and weekly windows (`config/channels.yaml`)
- Fallback hours for overflow/retries
- Historical CTR and retention by local hour (`data/jobs.db`)

## Logic

1. Generate candidate slots from the next 7 days of configured windows.
2. Add fallback slots from the next 48 hours using `fallback_hours`.
3. Score each hour with weighted CTR + retention.
4. Prefer highest score; use earliest timestamp as tie-breaker.
5. Enforce lead-time buffer (at least 20 minutes from now).

## Operational guardrails

- Private-first uploads only; publish time assigned via `status.publishAt`.
- Cooldown/fallback handling reduces burst uploads and repetitive posting patterns.
- Performance model defaults to conservative baseline when no history exists.
