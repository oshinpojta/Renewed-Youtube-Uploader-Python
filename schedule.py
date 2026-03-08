from apscheduler.schedulers.blocking import BlockingScheduler
from pathlib import Path

from src.main import cmd_run_once


def run_all_channels() -> None:
    cmd_run_once(workspace_root=Path("."), channel_id=None)


def main() -> None:
    scheduler = BlockingScheduler()
    run_all_channels()
    scheduler.add_job(run_all_channels, trigger="interval", hours=12, misfire_grace_time=3600)
    scheduler.start()


if __name__ == "__main__":
    main()
