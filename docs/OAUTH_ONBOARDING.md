# Multi-Account OAuth and Channel Onboarding

## Token model

- One encrypted token per `channel_profile_id` using `token_store_key`.
- Storage path: `data/tokens/<token_store_key>.enc`.
- Encryption key path: `data/tokens/.key`.

## Initial authorization flow

1. Ensure each channel profile in `config/channels.yaml` has:
   - `oauth_client_secrets_file`
   - unique `token_store_key`
2. Run:
   - `python -m src.main run-once --channel-id <channel_profile_id>`
3. Browser OAuth flow opens, then credentials are encrypted and stored.

## Handling `youtubeSignupRequired`

- If an account has no YouTube channel attached, uploader surfaces onboarding-required state.
- Use the documented create-channel URL:
  - `https://m.youtube.com/create_channel?chromeless=1&next=/channel_creation_done`
- Complete account channel setup, then rerun command.
