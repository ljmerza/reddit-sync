"""Protocol definitions for Reddit API interactions."""

from typing import Protocol

from reddit_sync.models import Multireddit


class RedditReader(Protocol):
    """Read-only Reddit operations."""

    def get_subscribed_subreddits(self) -> list[str]:
        """Get list of subscribed subreddit names."""
        ...

    def get_multireddits(self) -> list[Multireddit]:
        """Get list of user's multireddits."""
        ...


class RedditWriter(Protocol):
    """Write operations for Reddit."""

    username: str

    def subscribe_to_subreddit(self, subreddit: str) -> bool:
        """Subscribe to a subreddit. Returns True on success."""
        ...

    def unsubscribe_from_subreddit(self, subreddit: str) -> bool:
        """Unsubscribe from a subreddit. Returns True on success."""
        ...

    def create_multireddit(self, name: str, subreddits: list[str]) -> bool:
        """Create a new multireddit. Returns True on success."""
        ...

    def delete_multireddit(self, name: str) -> bool:
        """Delete a multireddit. Returns True on success."""
        ...

    def add_sub_to_multi(self, multi_name: str, subreddit: str) -> bool:
        """Add a subreddit to a multireddit. Returns True on success."""
        ...

    def remove_sub_from_multi(self, multi_name: str, subreddit: str) -> bool:
        """Remove a subreddit from a multireddit. Returns True on success."""
        ...
