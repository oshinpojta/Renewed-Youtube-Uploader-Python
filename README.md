# Renewed YouTube Uploader (Python)

Automation scripts for collecting short videos from multiple sources (TikTok, Reddit, Instagram), preparing video output, and uploading to YouTube Studio.

This repository is currently optimized for a **Windows desktop automation setup** that uses `pyautogui` click coordinates and command-line tools such as `ffmpeg`.

## Table of Contents

- [Project Overview](#project-overview)
- [How the Current Code Works](#how-the-current-code-works)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [One-Time Setup](#one-time-setup)
- [How to Run](#how-to-run)
- [How Merging Works](#how-merging-works)
- [Scheduling and Batch Files](#scheduling-and-batch-files)
- [Logs and Counters](#logs-and-counters)
- [Troubleshooting](#troubleshooting)
- [Security and Compliance Notes](#security-and-compliance-notes)
- [Current Limitations](#current-limitations)

## Project Overview

The codebase automates three major steps:

1. **Fetch** videos from different sources:
   - TikTok search pages
   - Reddit video posts (`v.redd.it`)
   - Instagram hashtag media
2. **Prepare output media**:
   - Merge video+audio for Reddit posts
   - Concatenate multiple Instagram clips into one output
3. **Upload to YouTube Studio**:
   - Browser/UI automation with `pyautogui` and fixed click coordinates

This is not using the official YouTube upload API in the active flow. Uploading is done by automating browser clicks in YouTube Studio.

## How the Current Code Works

### 1) TikTok flow (`tiktok.py`)

`upload_tiktok()` runs automatically and also gets called by other scripts.

Main behavior:

- Iterates through four channel/content groups (`i = 0..3`).
- Uses `CountSearch{i}.txt` to pick the next search term from large hardcoded tag lists.
- Opens YouTube Studio and switches account using hardcoded screen coordinates.
- Launches Chrome through `pyppeteer`, opens TikTok search URL, and extracts up to 2 video sources from page elements.
- Downloads each selected video to `vids/output.mp4` via `IDMan` downloader integration.
- Builds title using `CountTiktokVid{i}.txt`, uploads with UI automation, waits, then deletes `vids/output.mp4`.

Important note:

- A **merge-multiple-TikTok-clips** approach exists in the script but is inside a triple-quoted block (commented), so it is **not active** in the current run path.

### 2) Reddit flow (`reddit.py`)

`upload_reddit()`:

- Authenticates with Reddit via `praw` (credentials are hardcoded in current code).
- Picks a random subreddit from a predefined list.
- Scans hot posts and selects `v.redd.it` video URLs.
- Calls Reddit JSON endpoint to extract:
  - `fallback_url` for video
  - corresponding `DASH_audio.mp4` for audio
- Downloads to:
  - `vids/video.mp4`
  - `vids/audio.mp3` (extension name, content is fetched from DASH audio URL)
- Merges audio+video into `vids/output.mp4` using `ffmpeg`.
- Uploads via YouTube Studio UI automation, logs title/time to `log.txt`, then cleans temporary files.

At script end, random logic runs:

- If random number is `1`, run Reddit upload.
- Otherwise, fallback to `upload_tiktok()`.

### 3) Instagram flow (`insta.py`)

Behavior:

- Reads `CountInstaVids.txt`, increments counter, and creates upload title.
- Uses `instaloader` command to fetch videos for a hashtag.
- Filters downloaded files to `.mp4`.
- Writes a concat list in `videonames.txt`.
- Uses `ffmpeg -f concat` to combine clips into `vids/output.mp4`.
- Deletes temporary files, uploads merged output with `pyautogui`, then deletes `vids/output.mp4`.

Important note:

- The script references hardcoded Windows user paths (for example under `C:\Users\Ritesh\...`), so path updates are usually required per machine.

### 4) Scheduler flow (`schedule.py`)

Behavior:

- Calls `upload_tiktok()` once immediately.
- Registers a 12-hour repeating interval job with APScheduler.
- In each cycle, performs some UI clicks/pixel checks, then runs `tiktok.bat`.

## Project Structure

```text
.
|- tiktok.py        # TikTok scraping/downloading/upload flow
|- reddit.py        # Reddit video+audio fetch, merge, upload (or TikTok fallback)
|- insta.py         # Instagram hashtag fetch, clip concat, upload
|- schedule.py      # Interval scheduler for repeated runs
|- tiktok.bat
|- reddit.bat
|- insta.bat
|- scheduler.bat
|- wake.bat
|- sleep.bat
|- CountSearch0.txt
|- CountSearch1.txt
|- CountSearch2.txt
|- CountSearch3.txt
|- CountTiktokVid0.txt
|- CountTiktokVid1.txt
|- CountTiktokVid2.txt
|- CountTiktokVid3.txt
|- log.txt
|- client_secrets.json  # currently not part of active upload flow
```

## Requirements

### OS and runtime

- Windows 10/11 (current scripts use Windows-only shell commands and paths)
- Python 3.8+ (recommended)
- Google Chrome installed at expected path

### External tools

- `ffmpeg` available in system `PATH`
- `instaloader` CLI available
- Internet Download Manager + Python integration used by `from idm import IDMan`

### Python packages used in code

- `requests`
- `praw`
- `pyautogui`
- `pyppeteer`
- `apscheduler`

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install requests praw pyautogui pyppeteer apscheduler instaloader
```

If `from idm import IDMan` fails, install/configure the IDM Python integration used in your environment.

## One-Time Setup

1. Create required folders/files if missing:
   - `vids/`
   - `CountSearch0.txt` ... `CountSearch3.txt` (numeric values)
   - `CountTiktokVid0.txt` ... `CountTiktokVid3.txt` (numeric values)
   - `CountInstaVids.txt` (numeric value; required by `insta.py`)
   - `log.txt`
2. Update hardcoded local paths in scripts to your own machine paths.
3. Update credentials:
   - Reddit API credentials in `reddit.py`
   - Instagram login values in `insta.py`
4. Log in to required web accounts in Chrome:
   - TikTok (if needed for content loading)
   - YouTube channels used for upload
5. Recalibrate all `pyautogui.click(x, y)` coordinates for your monitor resolution, scaling, and browser layout.

## How to Run

### TikTok upload automation

```bash
python tiktok.py
```

or:

```bash
tiktok.bat
```

### Reddit (with random TikTok fallback)

```bash
python reddit.py
```

### Instagram merge-and-upload

```bash
python insta.py
```

### Scheduled TikTok runs

```bash
python schedule.py
```

or:

```bash
scheduler.bat
```

## How Merging Works

### Reddit merge (audio + video mux)

The script fetches separate media streams and combines without re-encoding:

```bash
ffmpeg -i vids\video.mp4 -i vids\audio.mp3 -c copy vids\output.mp4
```

### Instagram merge (multiple clips concatenation)

The script builds `videonames.txt` with lines like:

```text
file clip1.mp4
file clip2.mp4
```

Then concatenates:

```bash
ffmpeg -f concat -i videonames.txt -c copy vids\output.mp4
```

### TikTok merge status

- Current active path uploads one downloaded clip at a time.
- A merge-based TikTok path exists in commented code and is not active by default.

## Scheduling and Batch Files

- `tiktok.bat`: runs `python tiktok.py`, then waits.
- `reddit.bat`: runs `python reddit.py`.
- `insta.bat`: runs `python insta.py`.
- `scheduler.bat`: waits, runs `python schedule.py`, waits.
- `wake.bat`: simple chain (`reddit.bat` then sleep trigger).
- `sleep.bat`: calls Windows sleep command.

## Logs and Counters

- `CountSearch*.txt`: remembers which search term index to use next per channel group.
- `CountTiktokVid*.txt`: increments video numbering in generated titles.
- `CountInstaVids.txt`: increments Instagram upload numbering.
- `log.txt`: Reddit upload history (title and timestamp).

## Troubleshooting

- **Upload clicks are wrong**: Re-record and replace all `pyautogui` coordinates.
- **TikTok extraction fails**: Selector/class names may have changed; update query selectors in `tiktok.py`.
- **No media output**: Verify `ffmpeg` is installed and in `PATH`.
- **Instagram command fails**: Confirm `instaloader` is installed and login/session values are valid.
- **Script hangs**: Current flow uses long fixed sleeps; reduce/increase delays based on network and machine speed.
- **Windows command errors on macOS/Linux**: Scripts currently depend on Windows commands such as `del`, `move`, `.bat`, and `taskkill`.

## Security and Compliance Notes

- Current code stores credentials directly in source files. Move them to environment variables or a local config file excluded from version control.
- Automated scraping/downloading/uploading may be subject to platform terms (TikTok/Instagram/Reddit/YouTube). Use responsibly and verify policy compliance.
- Do not commit secrets (`client_secrets.json`, API keys, usernames/passwords) to public repositories.

## Current Limitations

- Heavy reliance on fixed UI coordinates and static sleeps.
- Hardcoded machine-specific paths and account assumptions.
- Minimal error handling and retry strategy in some flows.
- No centralized config file or dependency lock file.
- No test suite.

---

If you want, the next step can be a **production-ready cleanup**:
- move credentials to `.env`,
- add `requirements.txt`,
- make paths/config configurable,
- and replace UI-based upload with official YouTube Data API upload flow.
