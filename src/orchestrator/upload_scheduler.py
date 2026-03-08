from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Tuple
from zoneinfo import ZoneInfo

from src.config.models import ChannelProfile, ScheduleWindow


WEEKDAY_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


@dataclass
class SlotCandidate:
    publish_at_utc: datetime
    local_hour: int
    source: str
    score: float


class UploadTimeScheduler:
    def pick_slot_details(
        self,
        channel: ChannelProfile,
        performance_by_hour: Dict[int, Tuple[float, float]],
        now_utc: datetime | None = None,
    ) -> SlotCandidate:
        now_utc = now_utc or datetime.now(tz=timezone.utc)
        candidates = self._generate_candidates(channel, now_utc, performance_by_hour)
        if not candidates:
            fallback_dt = now_utc + timedelta(hours=2)
            return SlotCandidate(
                publish_at_utc=fallback_dt,
                local_hour=fallback_dt.hour,
                source="default_fallback",
                score=0.0,
            )
        ranked = sorted(candidates, key=lambda c: (-c.score, c.publish_at_utc))
        return ranked[0]

    def pick_slot(
        self,
        channel: ChannelProfile,
        performance_by_hour: Dict[int, Tuple[float, float]],
        now_utc: datetime | None = None,
    ) -> datetime:
        selection = self.pick_slot_details(channel, performance_by_hour, now_utc=now_utc)
        return selection.publish_at_utc

    def _generate_candidates(
        self,
        channel: ChannelProfile,
        now_utc: datetime,
        performance_by_hour: Dict[int, Tuple[float, float]],
    ) -> List[SlotCandidate]:
        tz = ZoneInfo(channel.timezone)
        now_local = now_utc.astimezone(tz)
        candidates: List[SlotCandidate] = []

        for delta_days in range(0, 8):
            target_date = now_local.date() + timedelta(days=delta_days)
            weekday = target_date.weekday()
            for window in channel.schedule_windows:
                if WEEKDAY_INDEX.get(window.day_of_week.lower()) != weekday:
                    continue
                for hour in range(window.start_hour, window.end_hour):
                    local_dt = datetime(
                        year=target_date.year,
                        month=target_date.month,
                        day=target_date.day,
                        hour=hour,
                        minute=0,
                        tzinfo=tz,
                    )
                    if local_dt <= now_local + timedelta(minutes=20):
                        continue
                    candidates.append(
                        SlotCandidate(
                            publish_at_utc=local_dt.astimezone(timezone.utc),
                            local_hour=hour,
                            source="window",
                            score=self._score_hour(hour, performance_by_hour, window_bonus=1.0),
                        )
                    )

        # Fallback queue: next 24 hours using fallback hours.
        for delta_days in range(0, 2):
            target_date = now_local.date() + timedelta(days=delta_days)
            for hour in channel.fallback_hours:
                local_dt = datetime(
                    year=target_date.year,
                    month=target_date.month,
                    day=target_date.day,
                    hour=hour,
                    minute=30,
                    tzinfo=tz,
                )
                if local_dt <= now_local + timedelta(minutes=20):
                    continue
                candidates.append(
                    SlotCandidate(
                        publish_at_utc=local_dt.astimezone(timezone.utc),
                        local_hour=hour,
                        source="fallback",
                        score=self._score_hour(hour, performance_by_hour, window_bonus=0.65),
                    )
                )
        return candidates

    @staticmethod
    def _score_hour(
        hour: int,
        performance_by_hour: Dict[int, Tuple[float, float]],
        window_bonus: float,
    ) -> float:
        ctr, retention = performance_by_hour.get(hour, (0.04, 0.35))
        return window_bonus + ctr * 2.2 + retention * 1.8
