"""Reddit scraper implementing reader and writer protocols."""

import json
import re
import time

from bs4 import BeautifulSoup

from reddit_sync.models import Multireddit
from reddit_sync.reddit.session import BASE_URL, REQUEST_DELAY, RedditSession


class RedditScraper:
    """Scrapes Reddit for subreddits and multireddits.

    Implements both RedditReader and RedditWriter protocols.
    """

    def __init__(self, session: RedditSession | None = None, cookie: str | None = None):
        """Initialize scraper.

        Args:
            session: Existing RedditSession to use
            cookie: Cookie value to create new session (ignored if session provided)
        """
        if session:
            self._session = session
        else:
            self._session = RedditSession(cookie)
        self.username: str = ""

    @property
    def session(self) -> RedditSession:
        """Access the underlying session."""
        return self._session

    # RedditReader methods

    def get_subscribed_subreddits(self) -> list[str]:
        """Scrape all subscribed subreddits."""
        subreddits = []
        url: str | None = f"{BASE_URL}/subreddits/mine/subscriber"

        while url:
            resp = self._session.get(url)

            if "login" in resp.url or "you must be logged in" in resp.text.lower():
                print(f"ERROR: Not logged in. Got redirected to: {resp.url}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")

            # Find subreddit entries - use \w+ to avoid capturing combined subs with +
            for entry in soup.select(".subscription-box .title"):
                href = entry.get("href", "")
                match = re.search(r"/r/(\w+)/?$", href)
                if match:
                    subreddits.append(match.group(1))

            # Alternative selector for different page layouts
            if not subreddits:
                for link in soup.select("a.title"):
                    href = link.get("href", "")
                    match = re.search(r"/r/(\w+)/?$", href)
                    if match:
                        subreddits.append(match.group(1))

            # Check for next page
            next_btn = soup.select_one(".next-button a")
            url = next_btn.get("href") if next_btn else None

        return sorted(set(subreddits))

    def get_multireddits(self) -> list[Multireddit]:
        """Get all multireddits using Reddit's JSON API."""
        multis = []

        resp = self._session.get(f"{BASE_URL}/api/multi/mine")

        try:
            data = resp.json()
        except Exception:
            print(f"Failed to parse multireddit response: {resp.text[:200]}")
            return []

        for multi in data:
            name = multi.get("data", {}).get("name", "")
            subs = [s.get("name", "") for s in multi.get("data", {}).get("subreddits", [])]
            subs = [s for s in subs if s]  # Filter empty

            if name:
                multis.append(Multireddit(name=name, subreddits=sorted(subs)))

        return multis

    # RedditWriter methods

    def subscribe_to_subreddit(self, subreddit: str) -> bool:
        """Subscribe to a subreddit."""
        url = f"{BASE_URL}/api/subscribe"
        data = {
            "action": "sub",
            "sr_name": subreddit,
            "uh": self._session.modhash,
        }
        resp = self._session.post(url, data=data)
        if resp.status_code != 200:
            print(f"    DEBUG: status={resp.status_code}, response={resp.text[:200]}")
        return resp.status_code == 200

    def unsubscribe_from_subreddit(self, subreddit: str) -> bool:
        """Unsubscribe from a subreddit."""
        url = f"{BASE_URL}/api/subscribe"
        data = {
            "action": "unsub",
            "sr_name": subreddit,
            "uh": self._session.modhash,
        }
        resp = self._session.post(url, data=data)
        return resp.status_code == 200

    def create_multireddit(self, name: str, subreddits: list[str], description: str = "") -> bool:
        """Create a new multireddit."""
        url = f"{BASE_URL}/api/multi/user/{self.username}/m/{name}"

        model = {
            "display_name": name,
            "subreddits": [{"name": s} for s in subreddits],
            "description_md": description,
            "visibility": "private",
        }

        data = {
            "model": json.dumps(model),
            "uh": self._session.modhash,
        }

        # Retry with backoff for rate limiting
        for attempt in range(3):
            time.sleep(REQUEST_DELAY * (attempt + 1) * 2)  # 4s, 8s, 12s
            resp = self._session.http.put(url, data=data)  # Direct http to avoid extra delay
            if resp.status_code == 429:
                print("    Rate limited, waiting...")
                continue
            if resp.status_code not in (200, 201):
                print(f"    DEBUG: status={resp.status_code}, response={resp.text[:200]}")
            return resp.status_code in (200, 201)
        return False

    def delete_multireddit(self, name: str) -> bool:
        """Delete a multireddit."""
        url = f"{BASE_URL}/api/multi/user/{self.username}/m/{name}"
        data = {"uh": self._session.modhash}
        resp = self._session.delete(url, data=data)
        return resp.status_code in (200, 201, 204)

    def add_sub_to_multi(self, multi_name: str, subreddit: str) -> bool:
        """Add a subreddit to an existing multireddit."""
        url = f"{BASE_URL}/api/multi/user/{self.username}/m/{multi_name}/r/{subreddit}"
        data = {
            "model": json.dumps({"name": subreddit}),
            "uh": self._session.modhash,
        }
        resp = self._session.put(url, data=data)
        return resp.status_code in (200, 201)

    def remove_sub_from_multi(self, multi_name: str, subreddit: str) -> bool:
        """Remove a subreddit from a multireddit."""
        url = f"{BASE_URL}/api/multi/user/{self.username}/m/{multi_name}/r/{subreddit}"
        data = {"uh": self._session.modhash}
        resp = self._session.delete(url, data=data)
        return resp.status_code in (200, 201, 204)


def create_scraper(cookie: str) -> RedditScraper:
    """Factory function to create a scraper with cookie auth."""
    return RedditScraper(cookie=cookie)
