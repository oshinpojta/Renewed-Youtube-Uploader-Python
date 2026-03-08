# Budget Deployment Options ($0-$25/month)

## Option 1: Local First (~$0-$5)

- Run pipeline locally with `python -m src.main run-once`.
- Schedule with Windows Task Scheduler / cron.
- Keep `data/jobs.db` and token store local.
- Best for early validation and zero cloud lock-in.

## Option 2: Hybrid Low Cost (~$5-$20)

- Use low-cost cloud scheduler (or free tier) for timed triggers.
- Keep rendering local or on low-cost worker.
- Store artifacts in low-cost object storage.
- Good reliability/cost ratio for multi-channel posting.

## Option 3: Hosted Budget Cap (~$10-$25)

- Run orchestrator on always-free/low-cost VM.
- Use object storage + lightweight health checks.
- Supports near-24/7 automation with strict monthly cap.

## Spend controls

- Upload only planned jobs with passing compliance checks.
- Avoid unnecessary re-renders and failed retries.
- Keep default `briefs_per_niche=1` until metrics justify scaling.
- Store source media efficiently and prune stale artifacts.
