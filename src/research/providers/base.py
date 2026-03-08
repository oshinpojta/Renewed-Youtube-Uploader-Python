from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.research.types import ResearchBundle, ResearchQuery


@dataclass(frozen=True)
class ResearchProviderConfig:
    api_key: str
    base_url: str
    timeout_seconds: int = 20


class ResearchProvider(ABC):
    provider_id: str

    @abstractmethod
    def search(self, query: ResearchQuery) -> ResearchBundle:
        raise NotImplementedError
