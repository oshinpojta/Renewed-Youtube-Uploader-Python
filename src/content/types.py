from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class TextGenerationRequest:
    niche_id: str
    prompt: str
    max_tokens: int
    temperature: float
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class TextGenerationResult:
    provider: str
    model: str
    text: str
    notes: List[str] = field(default_factory=list)
