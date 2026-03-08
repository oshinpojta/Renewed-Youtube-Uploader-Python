from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ResearchHit:
    title: str
    url: str
    snippet: str
    source: str
    confidence: float


@dataclass(frozen=True)
class ResearchQuery:
    niche_id: str
    query: str
    max_results: int = 5


@dataclass
class ResearchBundle:
    provider: str
    query: str
    hits: List[ResearchHit]
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
