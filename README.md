# Reddit Sync

Copy subscribed subreddits and multireddits from one Reddit account to another.

## Features

- Sync subscribed subreddits between accounts
- Copy multireddits to target account
- Diff mode to compare accounts without syncing
- Dry-run to preview changes
- Load from previous export file instead of re-scraping
- Auto-saves backup before syncing
- Skip already subscribed subreddits (no duplicate API calls)
- Cookie-based auth (no password needed)

## Setup

```bash
uv sync
```

## Usage

**Interactive mode:**
```bash
uv run reddit-sync
```

**Non-interactive sync:**
```bash
uv run reddit-sync sync -s SOURCE_COOKIE -t TARGET_COOKIE --subs --multis
uv run reddit-sync sync -f data/export.json -t TARGET_COOKIE --dry-run
```

**Diff mode (compare without syncing):**
```bash
uv run reddit-sync diff -f data/export.json -t TARGET_COOKIE
uv run reddit-sync diff -s SOURCE_COOKIE -t TARGET_COOKIE --json
```

**Options:**
- `-s, --source-cookie` - Source account reddit_session cookie
- `-t, --target-cookie` - Target account reddit_session cookie
- `-f, --from-file` - Load source from export file
- `--subs/--no-subs` - Toggle subreddit sync
- `--multis/--no-multis` - Toggle multireddit sync
- `--clean` - Remove target subs not in source
- `--dry-run` - Preview changes without executing

## Getting your reddit_session cookie

1. Open reddit.com in Chrome (logged in)
2. Press F12 > Application > Cookies > reddit.com
3. Find `reddit_session` row, double-click Value, Ctrl+C
4. Paste when prompted (or pass via `-s`/`-t` flags)
