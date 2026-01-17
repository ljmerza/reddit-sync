"""Reddit session management - cookie and modhash handling."""

import re
import time

import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://old.reddit.com"
REQUEST_DELAY = 2


class RedditSession:
    """Manages Reddit authentication state (cookies, modhash)."""

    def __init__(self, cookie: str | None = None):
        self.http = requests.Session()
        self.http.headers.update({"User-Agent": USER_AGENT})
        self._modhash: str | None = None

        if cookie:
            self.load_cookie(cookie)

    def load_cookie(self, value: str) -> None:
        """Set the reddit_session cookie."""
        self.http.cookies.set("reddit_session", value, domain=".reddit.com")
        self._modhash = None  # Clear cached modhash

    @property
    def modhash(self) -> str:
        """Get modhash token, fetching if needed."""
        if self._modhash is None:
            self._fetch_modhash()
        return self._modhash or ""

    def _fetch_modhash(self) -> None:
        """Fetch the modhash token from HTML page."""
        time.sleep(REQUEST_DELAY)
        resp = self.http.get(f"{BASE_URL}/")

        # Try to extract from HTML (more reliable with cookie auth)
        match = re.search(r'modhash["\s:]+([a-z0-9]+)', resp.text)
        if match:
            self._modhash = match.group(1)
            print("Got modhash token")
            return

        # Fallback: try JSON API
        time.sleep(REQUEST_DELAY)
        resp = self.http.get(f"{BASE_URL}/api/me.json")
        try:
            data = resp.json()
            self._modhash = data.get("data", {}).get("modhash", "")
            if self._modhash:
                print("Got modhash token")
            else:
                print("WARNING: No modhash found, write actions may fail")
        except Exception:
            print("WARNING: Failed to get modhash")

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make a GET request with rate limiting."""
        time.sleep(REQUEST_DELAY)
        return self.http.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Make a POST request with rate limiting."""
        time.sleep(REQUEST_DELAY)
        return self.http.post(url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        """Make a PUT request with rate limiting."""
        time.sleep(REQUEST_DELAY)
        return self.http.put(url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """Make a DELETE request with rate limiting."""
        time.sleep(REQUEST_DELAY)
        return self.http.delete(url, **kwargs)
