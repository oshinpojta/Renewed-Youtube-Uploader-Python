from __future__ import annotations

import json
from pathlib import Path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.config.models import ChannelProfile
from src.storage.token_store import EncryptedTokenStore


YOUTUBE_SCOPES: List[str] = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


class YouTubeAuthManager:
    def __init__(self, token_store: EncryptedTokenStore) -> None:
        self.token_store = token_store

    def _load_credentials(self, profile: ChannelProfile) -> Credentials | None:
        payload = self.token_store.load(profile.token_store_key)
        if not payload:
            return None
        return Credentials.from_authorized_user_info(payload, scopes=YOUTUBE_SCOPES)

    def _save_credentials(self, profile: ChannelProfile, creds: Credentials) -> None:
        self.token_store.save(profile.token_store_key, json.loads(creds.to_json()))

    def authorize(self, profile: ChannelProfile) -> Credentials:
        creds = self._load_credentials(profile)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._save_credentials(profile, creds)
            return creds
        if creds and creds.valid:
            return creds

        client_secrets = Path(profile.oauth_client_secrets_file)
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), YOUTUBE_SCOPES)
        creds = flow.run_local_server(port=0)
        self._save_credentials(profile, creds)
        return creds

    def build_service(self, profile: ChannelProfile):
        creds = self.authorize(profile)
        return build("youtube", "v3", credentials=creds)
