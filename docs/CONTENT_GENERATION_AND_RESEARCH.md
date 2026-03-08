# Content Generation and Research

This pipeline adds a dedicated generation stack before media rendering:

1. `TrendIntelCollector` gathers seeds.
2. `ResearchRouter` fetches web grounding for each niche/query.
3. `StoryBuilder` creates character + storyline structure.
4. `ScriptBuilder` turns that into scenes and narration.
5. `MediaFactory` renders from generated script prompts.

## Text generation providers

Strategy file:

- `config/text_provider_strategy.yaml`

Local keys file:

- `config/text_api_keys.local.yaml` (git-ignored)

Template:

- `config/text_api_keys.local.example.yaml`

Supported text provider IDs:

- `gemini_api`
- `groq_api`
- `openrouter_api`
- `huggingface_api`

If all text providers fail or keys are missing, router falls back to deterministic template output.

## Research providers

Strategy file:

- `config/research_provider_strategy.yaml`

Local keys file:

- `config/research_api_keys.local.yaml` (git-ignored)

Template:

- `config/research_api_keys.local.example.yaml`

Supported research provider IDs:

- `tavily_api`
- `brave_search_api`
- `wikimedia_api`

If external research APIs are unavailable, router falls back to a safe Wikimedia search citation URL.

## Runtime flow

- `plan` / `run-once` now include: trend -> research -> story -> script -> render.
- Citation URLs are merged into `brief.evidence_links` and description sources.
- Script/provider metadata is stored in `job.metadata` for analytics.

## Preview commands

Use these commands to validate the generation stack without uploading:

```bash
python -m src.main research-preview --channel-id channel_culture_trends
python -m src.main script-preview --channel-id channel_culture_trends
python -m src.main render-preview --channel-id channel_culture_trends
```
