# Model Adapter Strategy

This project includes a configurable provider routing layer and executable adapter service for AI video generation.

## What it controls

- Global `provider_priority`
- Explicit `fallback_order`
- `per_niche_provider_order`
- Provider-level `cost_guardrails`
  - `max_cost_per_second_usd`
  - `max_clip_cost_usd`
  - `max_monthly_budget_usd`
  - `allow_trial_only`

## Strategy config file

Edit:

- `config/model_provider_strategy.yaml`

This is where you tune which provider is preferred for each niche and where fallback should go if a provider is unavailable or too expensive.

## API keys file (separate local file)

Use:

- `config/model_api_keys.local.yaml`

Template:

- `config/model_api_keys.local.example.yaml`

`model_api_keys.local.yaml` is git-ignored so you can safely store local credentials there.

## Current provider IDs supported

- `kling_ai`
- `seedance_2`
- `veo3`
- `sora_api`
- `bing_sora_ui` (documented as non-API automation path; skipped by router)

## How selection works

1. Router gets provider order for a niche from `per_niche_provider_order`.
2. It expands candidates with fallback order.
3. It skips providers that fail:
   - API automation capability
   - audio requirement
   - max duration support
   - missing API key
   - cost guardrail limits
4. First eligible provider is selected and logged.
5. Selected providers are executed through `VideoGenerationService` with async polling + download.
6. If generation fails or no provider is eligible, media factory uses local fallback rendering.

## Verify strategy at runtime

```bash
python -m src.main model-strategy
```

This prints selected provider/model and reasons for skipped providers per niche.

## Integration points in code

- Strategy loader: `src/config/loader.py`
- Router logic: `src/media/model_router.py`
- Provider adapters: `src/media/providers/`
- Execution service: `src/media/video_generation_service.py`
- Media factory integration: `src/media/factory.py`
- Pipeline metadata/logging: `src/orchestrator/pipeline.py`
