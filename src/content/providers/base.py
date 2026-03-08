from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from src.content.types import TextGenerationRequest, TextGenerationResult


class TextProvider(ABC):
    provider_id: str

    @abstractmethod
    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        raise NotImplementedError


@dataclass(frozen=True)
class ProviderClientConfig:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int = 30


def post_json(
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    timeout_seconds: int = 30,
) -> Dict[str, Any]:
    response = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Provider returned non-object JSON.")
    return data


def try_parse_json_block(text: str) -> Optional[Dict[str, Any]]:
    content = text.strip()
    if not content:
        return None
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    maybe = content[start : end + 1]
    try:
        decoded = json.loads(maybe)
    except Exception:
        return None
    if not isinstance(decoded, dict):
        return None
    return decoded
