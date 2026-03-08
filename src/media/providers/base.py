from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import requests


@dataclass(frozen=True)
class ProviderVideoConfig:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int = 30


@dataclass(frozen=True)
class ProviderVideoRequest:
    prompt: str
    duration_seconds: int
    aspect_ratio: str
    include_audio: bool = True
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProviderVideoJob:
    task_id: str
    status: str
    raw_response: Dict[str, Any]
    output_url: str = ""


@dataclass
class ProviderVideoResult:
    task_id: str
    output_path: Path
    provider: str
    model: str
    notes: list[str] = field(default_factory=list)


class VideoGenerationProvider(ABC):
    provider_id: str

    @abstractmethod
    def submit(self, request: ProviderVideoRequest) -> ProviderVideoJob:
        raise NotImplementedError

    @abstractmethod
    def poll(self, task_id: str) -> ProviderVideoJob:
        raise NotImplementedError

    @abstractmethod
    def download(self, job: ProviderVideoJob, destination: Path) -> Path:
        raise NotImplementedError


def post_json(
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    timeout_seconds: int = 30,
) -> Dict[str, Any]:
    response = requests.post(url, json=payload, headers=headers, timeout=timeout_seconds)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Video provider returned invalid JSON payload.")
    return data


def get_json(url: str, headers: Dict[str, str], timeout_seconds: int = 30) -> Dict[str, Any]:
    response = requests.get(url, headers=headers, timeout=timeout_seconds)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Video provider returned invalid JSON payload.")
    return data


def download_to_file(
    url: str,
    destination: Path,
    headers: Optional[Dict[str, str]] = None,
    timeout_seconds: int = 60,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, headers=headers or {}, timeout=timeout_seconds, stream=True) as response:
        response.raise_for_status()
        with destination.open("wb") as fileptr:
            for chunk in response.iter_content(chunk_size=1024 * 128):
                if chunk:
                    fileptr.write(chunk)
    return destination


def read_nested(data: Dict[str, Any], *keys: str) -> Any:
    cursor: Any = data
    for key in keys:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    return cursor
