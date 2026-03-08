from __future__ import annotations

from dataclasses import dataclass


CREATE_CHANNEL_URL = "https://m.youtube.com/create_channel?chromeless=1&next=/channel_creation_done"
CHANNEL_DONE_URL = "https://m.youtube.com/channel_creation_done"


@dataclass(frozen=True)
class OnboardingAction:
    requires_user_action: bool
    message: str
    create_channel_url: str | None = None


def handle_youtube_signup_required(api_error_text: str) -> OnboardingAction:
    normalized = (api_error_text or "").lower()
    if "youtubesignuprequired" in normalized:
        return OnboardingAction(
            requires_user_action=True,
            message=(
                "Google account is not linked to a YouTube channel. "
                "Complete the channel creation web flow and retry."
            ),
            create_channel_url=CREATE_CHANNEL_URL,
        )
    return OnboardingAction(
        requires_user_action=False,
        message="No youtubeSignupRequired signal detected.",
        create_channel_url=None,
    )
