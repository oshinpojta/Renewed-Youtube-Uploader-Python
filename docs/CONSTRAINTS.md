# Non-Negotiable Constraints

This project enforces these constraints before any automated upload flow:

1. **No direct API channel creation endpoint**
   - The system handles onboarding via OAuth and the documented `youtubeSignupRequired` fallback web flow.
2. **Private-first upload required**
   - Upload videos as `private`, then apply schedule and publish controls after checks.
3. **No policy-evasion automation**
   - Rejected/policy-risk videos are escalated to manual review rather than blindly reuploaded.
4. **No scraped mass reposting**
   - Content must pass rights checks and originality checks.
5. **Synthetic media disclosure required**
   - `status.containsSyntheticMedia` is set for content requiring altered/synthetic disclosure.
6. **Sensitive topic guardrail**
   - Religion/culture/legend/ghost content must remain respectful, source-backed, and non-harmful.

## Unsupported asks and safe alternatives

- **Ask:** Fully programmatic channel creation
  - **Alternative:** Use OAuth onboarding, detect `youtubeSignupRequired`, complete web flow.
- **Ask:** Publish immediately without checks
  - **Alternative:** Keep private-first pipeline with compliance gate and slot scheduling.
- **Ask:** Auto-reupload policy-rejected content as-is
  - **Alternative:** Route to manual review with actionable remediation notes.
