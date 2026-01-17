# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                      # Install dependencies
uv run reddit-sync           # Interactive mode (same as sync)
uv run reddit-sync sync      # Sync command
uv run reddit-sync diff      # Compare accounts without syncing
```

**Non-interactive sync:**
```bash
uv run reddit-sync sync -s SOURCE_COOKIE -t TARGET_COOKIE --subs --multis
uv run reddit-sync sync -f data/export.json -t TARGET_COOKIE --dry-run
```

**Diff mode:**
```bash
uv run reddit-sync diff -f data/export.json -t TARGET_COOKIE
uv run reddit-sync diff -s SOURCE_COOKIE -t TARGET_COOKIE --json
```

## Architecture

This is a CLI tool to sync subreddits and multireddits between Reddit accounts using cookie-based auth.

**Files:**
- `reddit_sync.py` - Click-based CLI with `sync` and `diff` commands, supports interactive and non-interactive modes
- `scraper.py` - `RedditScraper` class handling all Reddit API/scraping operations
- `config.py` - Credential storage in `~/.config/reddit_sync/credentials.json` (currently unused by main flow)

**Key patterns:**
- Uses `old.reddit.com` for scraping (more stable HTML structure)
- Requires `modhash` token for write operations (subscribe, create multi, etc) - fetched from HTML or `/api/me.json`
- All API calls have 2-second delay (`REQUEST_DELAY`) to avoid rate limiting
- Export files saved to `data/export_*.json` with timestamp

**RedditScraper methods:**
- `load_cookies()` - Set `reddit_session` cookie for auth
- `fetch_modhash()` - Get CSRF token needed for write operations
- `get_subscribed_subreddits()` - Scrape paginated subscription list
- `get_multireddits()` - Fetch via `/api/multi/mine` JSON endpoint
- `subscribe_to_subreddit()` / `unsubscribe_from_subreddit()` - Sub management
- `create_multireddit()` / `delete_multireddit()` - Multi management with retry backoff
- `add_sub_to_multi()` / `remove_sub_from_multi()` - Modify existing multis

## Gotchas

- **Modhash extraction**: The `/api/me.json` endpoint sometimes returns empty modhash with cookie auth. Prefer extracting from HTML via regex (`modhash["\s:]+([a-z0-9]+)`)
- **Rate limiting**: Reddit returns 429 on rapid requests. Multireddit creation has retry with exponential backoff (4s, 8s, 12s)
- **Password login blocked**: Reddit often returns HTML/captcha instead of JSON for password auth. Cookie auth is the reliable path
- **Subreddit regex**: Use `\w+` not `.+` to avoid matching combined subs like `r/sub1+sub2`

## Debugging

- Check `resp.status_code` and `resp.text[:200]` on failures
- "Not logged in" errors mean the cookie is invalid or expired
- Missing modhash causes all write operations to fail silently or return 403
