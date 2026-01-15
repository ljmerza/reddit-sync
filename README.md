# Reddit Sync

Copy subscribed subreddits and multireddits from one Reddit account to another.

## Features

- Sync subscribed subreddits between accounts
- Copy multireddits to target account
- Load from previous export file instead of re-scraping
- Auto-saves backup before syncing
- Skip already subscribed subreddits (no duplicate API calls)
- Option to unsubscribe from all target subs first (clean slate)
- Cookie-based auth (no password needed)

## Setup

```bash
uv sync
```

## Usage

```bash
uv run python reddit_sync.py
```

## Getting your reddit_session cookie

1. Open reddit.com in Chrome (logged in)
2. Press F12 > Application > Cookies > reddit.com
3. Find `reddit_session` row, double-click Value, Ctrl+C
4. Paste when prompted

## Workflow

1. Choose source: fetch from account or load from export file
2. Review subreddits and multireddits to sync
3. Login to target account
4. Optionally unsubscribe from all existing target subs
5. Sync only new subreddits (skips existing)
6. Create multireddits on target
