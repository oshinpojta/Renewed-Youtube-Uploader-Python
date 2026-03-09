from __future__ import annotations

from typing import Dict, List

from src.config.models import ChannelProfile, ContentBrief, TrendSeed
from src.niches.engine import NicheEngine


class NichePlanner:
    def __init__(self, engines: Dict[str, NicheEngine]) -> None:
        self.engines = engines

    def build_channel_briefs(
        self,
        channel: ChannelProfile,
        trend_map: Dict[str, List[TrendSeed]],
        briefs_per_niche: int = 1,
    ) -> List[ContentBrief]:
        briefs: List[ContentBrief] = []
        for niche_id in channel.niches:
            if niche_id not in self.engines:
                continue
            seeds = trend_map.get(niche_id, [])
            if not seeds:
                continue
            for seed in seeds[:briefs_per_niche]:
                brief = self.engines[niche_id].build_brief(channel.channel_profile_id, seed)
                brief.channel_name = channel.channel_name
                briefs.append(brief)
        return briefs
