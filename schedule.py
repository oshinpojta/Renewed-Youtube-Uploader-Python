from apscheduler.schedulers.blocking import BlockingScheduler
from pathlib import Path

from src.main import cmd_collect_metrics, cmd_run_once


def run_all_channels() -> None:
    cmd_run_once(workspace_root=Path("."), channel_id=None)


def collect_all_metrics() -> None:
    cmd_collect_metrics(workspace_root=Path("."), channel_id=None)


def main() -> None:
    scheduler = BlockingScheduler()
    run_all_channels()
    collect_all_metrics()
    scheduler.add_job(run_all_channels, trigger="interval", hours=12, misfire_grace_time=3600)
    scheduler.add_job(collect_all_metrics, trigger="interval", hours=12, misfire_grace_time=3600)
    scheduler.start()


if __name__ == "__main__":
    main()
