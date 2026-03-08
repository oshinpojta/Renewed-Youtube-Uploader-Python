# Compliance and Remediation Workflow

## Pre-upload gate (`src/compliance/pre_upload.py`)

Checks executed before upload:

- Rights/source credits present
- Recent-title duplication detection
- Metadata relevance sanity checks
- Outline depth/originality minimum
- Sensitive-topic check for religion/culture/legends/ghost niche:
  - respect language rules
  - banned phrase filtering
  - educational disclaimer expectations

Outcomes:

- `planned`
- `precheck_failed`
- `needs_review`

## Post-upload evaluation (`src/compliance/post_upload.py`)

Monitored fields:

- `status.uploadStatus`
- `status.failureReason`
- `status.rejectionReason`
- `processingDetails.processingFailureReason`

Routing:

- Technical failures (`codec`, `invalidFile`, etc.) -> retry path
- Policy/copyright/terms risks -> manual review path
- Successful processing -> publish-ready state

## Remediation (`src/compliance/remediation.py`)

- Technical retry path:
  - FFmpeg re-encode (`libx264` + `aac`)
  - bounded retries (`max_retries`)
- Policy-risk path:
  - hard-stop to manual review
  - no automated policy bypass behavior
