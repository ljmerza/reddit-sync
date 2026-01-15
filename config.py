import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "reddit_sync"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_credentials():
    if not CREDENTIALS_FILE.exists():
        return {}
    with open(CREDENTIALS_FILE) as f:
        return json.load(f)


def save_credentials(creds):
    ensure_config_dir()
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    os.chmod(CREDENTIALS_FILE, 0o600)


def get_account(username):
    creds = load_credentials()
    return creds.get(username)


def set_account(username, password):
    creds = load_credentials()
    creds[username] = {"password": password}
    save_credentials(creds)


def set_account_cookies(username, cookies):
    """Store cookies for an account (fallback when password login fails)."""
    creds = load_credentials()
    if username not in creds:
        creds[username] = {}
    creds[username]["cookies"] = cookies
    save_credentials(creds)
