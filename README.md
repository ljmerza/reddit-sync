# Reddit Sync

Copy subscribed subreddits and multireddits from one Reddit account to another.

## Setup

```bash
uv sync
```

## Usage

```bash
uv run python reddit_sync.py
```

The CLI will prompt for:
1. Source account username + reddit_session cookie
2. Target account username + reddit_session cookie

## Getting your reddit_session cookie

1. Open reddit.com in Chrome (logged in)
2. Press F12 > Application > Cookies > reddit.com
3. Find `reddit_session` row, double-click Value, Ctrl+C
4. Paste when prompted

## What it does

1. Fetches subscribed subreddits from source account
2. Fetches multireddits from source account
3. Saves backup to `data/export_<timestamp>.json`
4. Subscribes target account to all subreddits
5. Creates multireddits on target account
