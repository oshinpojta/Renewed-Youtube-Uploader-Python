# Implementation Phases

## Phase 1: Foundation

- Build modular packages under `src/`.
- Add typed config files (`config/channels.yaml`, `config/niches.yaml`).
- Add encrypted token store and SQLite job store.

**Exit metric:** Pipeline can plan jobs end-to-end without upload execution failures.

## Phase 2: Uploader Core

- Integrate OAuth multi-account auth.
- Upload with `videos.insert` as private.
- Apply `publishAt` scheduling and synthetic media flag.

**Exit metric:** At least one channel uploads and schedules successfully via API.

## Phase 3: Compliance Gate

- Add pre-upload rights/originality/metadata checks.
- Add sensitive-topic checks for religion/legend/ghost niche.
- Add post-upload status parsing and remediation routing.

**Exit metric:** All jobs have deterministic compliance outcomes (`planned`, `needs_review`, `precheck_failed`).

## Phase 4: Niche Engines

- Ship 6 niche engines:
  - Roblox/UGC
  - AI workflow tutorials
  - Internet culture context
  - Practical law/safety
  - Public-domain micro docs
  - Religion/culture/legends/ghost lore

**Exit metric:** At least one generated brief per niche/channel run.

## Phase 5: Optimization

- Improve upload time scoring with CTR/retention data.
- Tune retry and remediation thresholds.
- Add richer monitoring dashboards/reports.

**Exit metric:** Higher publish success rate and lower manual review rate over 30-day window.
