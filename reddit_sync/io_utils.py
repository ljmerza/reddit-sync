"""File I/O and user prompts."""

import getpass
import json
from datetime import datetime
from pathlib import Path

from reddit_sync.models import AccountData


def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(__file__).parent.parent / "data"


def prompt_auth(label: str) -> tuple[str, str]:
    """Prompt for username and cookie.

    Returns:
        Tuple of (username, cookie_value)
    """
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


def confirm(message: str) -> bool:
    """Ask for y/n confirmation."""
    response = input(f"{message} [y/N]: ").strip().lower()
    return response == "y"


def load_export(file_path: Path | str | None = None) -> AccountData | None:
    """Load subreddits and multis from an export file.

    Args:
        file_path: Path to specific file, or None for interactive selection

    Returns:
        AccountData or None if loading failed
    """
    data_dir = get_data_dir()

    if file_path:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return None
        with open(file_path) as f:
            data = json.load(f)
        account_data = AccountData.from_dict(data)
        print(
            f"Loaded {len(account_data.subreddits)} subreddits and "
            f"{len(account_data.multireddits)} multireddits from {file_path}"
        )
        return account_data

    if not data_dir.exists():
        print("No data folder found.")
        return None

    files = sorted(data_dir.glob("export_*.json"), reverse=True)

    if not files:
        print("No export files found in data folder.")
        return None

    print("\nAvailable export files:")
    print("-" * 40)
    for i, f in enumerate(files, 1):
        with open(f) as fp:
            data = json.load(fp)
        account = data.get("source_account", "unknown")
        subs = len(data.get("subreddits", []))
        multis = len(data.get("multireddits", []))
        print(f"  {i}. {f.name} ({account}: {subs} subs, {multis} multis)")

    choice = input("\nSelect file [1]: ").strip() or "1"
    try:
        idx = int(choice) - 1
        file_path = files[idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None

    with open(file_path) as f:
        data = json.load(f)

    account_data = AccountData.from_dict(data)
    print(
        f"\nLoaded {len(account_data.subreddits)} subreddits and "
        f"{len(account_data.multireddits)} multireddits"
    )
    return account_data


def save_export(account_data: AccountData) -> Path:
    """Save account data to an export file.

    Returns:
        Path to the saved file
    """
    data_dir = get_data_dir()
    data_dir.mkdir(exist_ok=True)
    export_file = data_dir / f"export_{datetime.now():%Y%m%d_%H%M%S}.json"

    export_data = account_data.to_dict()
    export_data["exported_at"] = datetime.now().isoformat()

    with open(export_file, "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"\nSaved backup to {export_file}")
    return export_file
