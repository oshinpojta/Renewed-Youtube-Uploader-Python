import subprocess
import sys


def main() -> None:
    cmd = [
        sys.executable,
        "-m",
        "src.main",
        "run-once",
        "--channel-id",
        "channel_culture_trends",
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
