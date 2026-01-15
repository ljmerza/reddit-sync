import json
import time
import re
import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://old.reddit.com"
REQUEST_DELAY = 2


class RedditScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.username = None
        self.modhash = None

    def login(self, username, password):
        """Login to Reddit and store session cookies."""
        login_url = f"{BASE_URL}/api/login/{username}"
        data = {
            "op": "login",
            "user": username,
            "passwd": password,
            "api_type": "json",
        }
        resp = self.session.post(login_url, data=data)

        # Check if we got JSON or HTML (blocked/captcha)
        content_type = resp.headers.get("content-type", "")
        if "json" not in content_type:
            raise Exception(
                f"Reddit returned HTML instead of JSON (status {resp.status_code}). "
                "Likely blocked or requires captcha. Use cookie auth instead."
            )

        try:
            result = resp.json()
        except Exception:
            raise Exception(f"Invalid response from Reddit: {resp.text[:200]}")

        if result.get("json", {}).get("errors"):
            errors = result["json"]["errors"]
            raise Exception(f"Login failed: {errors}")

        self.username = username
        return True

    def load_cookies(self, cookies_dict):
        """Load cookies from a dict (exported from browser)."""
        for name, value in cookies_dict.items():
            self.session.cookies.set(name, value, domain=".reddit.com")

    def fetch_modhash(self):
        """Fetch the modhash token from HTML page."""
        time.sleep(REQUEST_DELAY)
        resp = self.session.get(f"{BASE_URL}/")

        # Try to extract from HTML (more reliable with cookie auth)
        match = re.search(r'modhash["\s:]+([a-z0-9]+)', resp.text)
        if match:
            self.modhash = match.group(1)
            print("Got modhash token")
            return

        # Fallback: try JSON API
        time.sleep(REQUEST_DELAY)
        resp = self.session.get(f"{BASE_URL}/api/me.json")
        try:
            data = resp.json()
            self.modhash = data.get("data", {}).get("modhash", "")
            if self.modhash:
                print("Got modhash token")
            else:
                print("WARNING: No modhash found, write actions may fail")
        except Exception:
            print("WARNING: Failed to get modhash")

    def get_subscribed_subreddits(self):
        """Scrape all subscribed subreddits."""
        subreddits = []
        url = f"{BASE_URL}/subreddits/mine/subscriber"

        while url:
            time.sleep(REQUEST_DELAY)
            resp = self.session.get(url)

            # Debug: check if we're logged in
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

    def get_multireddits(self):
        """Get all multireddits using Reddit's JSON API."""
        multis = []

        time.sleep(REQUEST_DELAY)
        resp = self.session.get(f"{BASE_URL}/api/multi/mine")

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
                multis.append({"name": name, "subreddits": sorted(subs)})

        return multis

    def delete_multireddit(self, name):
        """Delete a multireddit."""
        if not self.modhash:
            self.fetch_modhash()

        time.sleep(REQUEST_DELAY)
        url = f"{BASE_URL}/api/multi/user/{self.username}/m/{name}"
        data = {"uh": self.modhash}
        resp = self.session.delete(url, data=data)
        return resp.status_code in (200, 201, 204)

    def add_sub_to_multi(self, multi_name, subreddit):
        """Add a subreddit to an existing multireddit."""
        if not self.modhash:
            self.fetch_modhash()

        time.sleep(REQUEST_DELAY)
        url = f"{BASE_URL}/api/multi/user/{self.username}/m/{multi_name}/r/{subreddit}"
        data = {
            "model": json.dumps({"name": subreddit}),
            "uh": self.modhash,
        }
        resp = self.session.put(url, data=data)
        return resp.status_code in (200, 201)

    def remove_sub_from_multi(self, multi_name, subreddit):
        """Remove a subreddit from a multireddit."""
        if not self.modhash:
            self.fetch_modhash()

        time.sleep(REQUEST_DELAY)
        url = f"{BASE_URL}/api/multi/user/{self.username}/m/{multi_name}/r/{subreddit}"
        data = {"uh": self.modhash}
        resp = self.session.delete(url, data=data)
        return resp.status_code in (200, 201, 204)

    def subscribe_to_subreddit(self, subreddit):
        """Subscribe to a subreddit."""
        if not self.modhash:
            self.fetch_modhash()

        time.sleep(REQUEST_DELAY)
        url = f"{BASE_URL}/api/subscribe"
        data = {
            "action": "sub",
            "sr_name": subreddit,
            "uh": self.modhash,
        }
        resp = self.session.post(url, data=data)
        if resp.status_code != 200:
            print(f"    DEBUG: status={resp.status_code}, response={resp.text[:200]}")
        return resp.status_code == 200

    def unsubscribe_from_subreddit(self, subreddit):
        """Unsubscribe from a subreddit."""
        if not self.modhash:
            self.fetch_modhash()

        time.sleep(REQUEST_DELAY)
        url = f"{BASE_URL}/api/subscribe"
        data = {
            "action": "unsub",
            "sr_name": subreddit,
            "uh": self.modhash,
        }
        resp = self.session.post(url, data=data)
        return resp.status_code == 200

    def create_multireddit(self, name, subreddits, description=""):
        """Create a new multireddit."""
        if not self.modhash:
            self.fetch_modhash()

        url = f"{BASE_URL}/api/multi/user/{self.username}/m/{name}"

        model = {
            "display_name": name,
            "subreddits": [{"name": s} for s in subreddits],
            "description_md": description,
            "visibility": "private",
        }

        data = {
            "model": json.dumps(model),
            "uh": self.modhash,
        }

        # Retry with backoff for rate limiting
        for attempt in range(3):
            time.sleep(REQUEST_DELAY * (attempt + 1) * 2)  # 4s, 8s, 12s
            resp = self.session.put(url, data=data)
            if resp.status_code == 429:
                print(f"    Rate limited, waiting...")
                continue
            if resp.status_code not in (200, 201):
                print(f"    DEBUG: status={resp.status_code}, response={resp.text[:200]}")
            return resp.status_code in (200, 201)
        return False
