#!/usr/bin/env python3
import getpass
import json
from datetime import datetime
from pathlib import Path

from scraper import RedditScraper


def prompt_auth(label):
    """Prompt for username and cookie."""
    print(f"\n{label}")
    print("-" * 40)
    print("To get your reddit_session cookie:")
    print("  1. Open reddit.com in Chrome (logged in)")
    print("  2. Press F12 > Application > Cookies > reddit.com")
    print("  3. Find 'reddit_session' row, double-click Value, Ctrl+C")
    print()
    username = input("Username: ").strip()
    cookie_value = getpass.getpass("Paste reddit_session cookie: ")
    return username, cookie_value


def login_account(label):
    """Login to an account using cookie."""
    username, cookie_value = prompt_auth(label)

    scraper = RedditScraper()
    scraper.load_cookies({"reddit_session": cookie_value})
    scraper.username = username
    print(f"Loaded cookie for {username}")

    return scraper, username


def confirm(message):
    """Ask for y/n confirmation."""
    response = input(f"{message} [y/N]: ").strip().lower()
    return response == "y"


def load_from_file():
    """Load subreddits and multis from an export file."""
    file_path = input("Export file path: ").strip()
    with open(file_path) as f:
        data = json.load(f)

    subreddits = data.get("subreddits", [])
    multis = data.get("multireddits", [])
    source_user = data.get("source_account", "unknown")

    print(f"Loaded {len(subreddits)} subreddits and {len(multis)} multireddits from {file_path}")
    return subreddits, multis, source_user


def fetch_from_account():
    """Fetch subreddits and multis from a Reddit account."""
    try:
        source, source_user = login_account("SOURCE ACCOUNT (copy from)")
    except Exception as e:
        print(f"Login failed: {e}")
        return None, None, None

    print("\nFetching subscribed subreddits...")
    subreddits = source.get_subscribed_subreddits()

    print("Fetching multireddits...")
    multis = source.get_multireddits()

    # Save export immediately
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    export_file = data_dir / f"export_{datetime.now():%Y%m%d_%H%M%S}.json"

    export_data = {
        "exported_at": datetime.now().isoformat(),
        "source_account": source_user,
        "subreddits": subreddits,
        "multireddits": multis,
    }
    with open(export_file, "w") as f:
        json.dump(export_data, f, indent=2)
    print(f"\nSaved backup to {export_file}")

    return subreddits, multis, source_user


def main():
    print("Reddit Sync - Subreddit & Multireddit Copier")
    print("=" * 50)

    print("\nSource:")
    print("  1. Fetch from Reddit account")
    print("  2. Load from export file")
    choice = input("Choice [1]: ").strip() or "1"

    if choice == "2":
        try:
            subreddits, multis, source_user = load_from_file()
        except Exception as e:
            print(f"Failed to load file: {e}")
            return
    else:
        subreddits, multis, source_user = fetch_from_account()
        if subreddits is None:
            return

    # Show subreddits
    print(f"\nFound {len(subreddits)} subscribed subreddits:")
    print("-" * 40)
    for i, sub in enumerate(subreddits, 1):
        print(f"  {i:3}. r/{sub}")

    sync_subs = subreddits if confirm("\nSync these subreddits to target account?") else []

    # Show multireddits
    if multis:
        print(f"\nFound {len(multis)} multireddits:")
        print("-" * 40)
        for m in multis:
            print(f"  {m['name']} ({len(m['subreddits'])} subs)")
            for sub in m["subreddits"][:5]:
                print(f"    - r/{sub}")
            if len(m["subreddits"]) > 5:
                print(f"    ... and {len(m['subreddits']) - 5} more")

        sync_multis = multis if confirm("\nCopy these multireddits to target account?") else []
    else:
        print("\nNo multireddits found.")
        sync_multis = []

    if not sync_subs and not sync_multis:
        print("\nNothing to sync. Exiting.")
        return

    # Get target account
    try:
        target, target_user = login_account("TARGET ACCOUNT (copy to)")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # Subscribe to subreddits
    if sync_subs:
        print(f"\nSubscribing to {len(sync_subs)} subreddits...")
        for i, sub in enumerate(sync_subs, 1):
            success = target.subscribe_to_subreddit(sub)
            status = "OK" if success else "FAILED"
            print(f"  [{i}/{len(sync_subs)}] r/{sub}: {status}")

    # Create multireddits
    if sync_multis:
        print(f"\nCreating {len(sync_multis)} multireddits...")
        for m in sync_multis:
            success = target.create_multireddit(m["name"], m["subreddits"])
            status = "OK" if success else "FAILED"
            print(f"  {m['name']}: {status}")

    print("\nSync complete!")


if __name__ == "__main__":
    main()
