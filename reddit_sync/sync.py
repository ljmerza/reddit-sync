"""Sync orchestration service."""

from reddit_sync.models import SyncDiff
from reddit_sync.reddit.protocols import RedditWriter


class SyncService:
    """Orchestrates sync operations to a target account."""

    def __init__(self, target: RedditWriter, dry_run: bool = False):
        self.target = target
        self.dry_run = dry_run

    def execute(
        self,
        diff: SyncDiff,
        sync_subs: bool = True,
        sync_multis: bool = True,
        clean: bool = False,
    ) -> None:
        """Execute sync operations based on the diff.

        Args:
            diff: The computed differences
            sync_subs: Whether to sync subreddits
            sync_multis: Whether to sync multireddits
            clean: Whether to unsubscribe from subs not in source
        """
        if sync_subs:
            self._sync_subreddits(diff, clean)

        if sync_multis:
            self._sync_multireddits(diff)

    def _sync_subreddits(self, diff: SyncDiff, clean: bool) -> None:
        """Sync subreddits (add/remove)."""
        if clean and diff.subs_to_remove:
            self._unsubscribe_from_subs(diff.subs_to_remove)

        if diff.subs_to_add:
            self._subscribe_to_subs(diff.subs_to_add)

    def _unsubscribe_from_subs(self, subs: list[str]) -> None:
        """Unsubscribe from a list of subreddits."""
        if self.dry_run:
            print(f"\n[DRY RUN] Would unsubscribe from {len(subs)} subreddits")
            for sub in subs[:10]:
                print(f"  - r/{sub}")
            if len(subs) > 10:
                print(f"  ... and {len(subs) - 10} more")
            return

        print(f"\nUnsubscribing from {len(subs)} subreddits...")
        for i, sub in enumerate(subs, 1):
            success = self.target.unsubscribe_from_subreddit(sub)
            status = "OK" if success else "FAILED"
            print(f"  [{i}/{len(subs)}] r/{sub}: {status}")

    def _subscribe_to_subs(self, subs: list[str]) -> None:
        """Subscribe to a list of subreddits."""
        if self.dry_run:
            print(f"\n[DRY RUN] Would subscribe to {len(subs)} subreddits")
            for sub in subs[:10]:
                print(f"  + r/{sub}")
            if len(subs) > 10:
                print(f"  ... and {len(subs) - 10} more")
            return

        print(f"\nSubscribing to {len(subs)} subreddits...")
        for i, sub in enumerate(subs, 1):
            success = self.target.subscribe_to_subreddit(sub)
            status = "OK" if success else "FAILED"
            print(f"  [{i}/{len(subs)}] r/{sub}: {status}")

    def _sync_multireddits(self, diff: SyncDiff) -> None:
        """Sync multireddits (create/update)."""
        for m in diff.multis_to_add:
            if self.dry_run:
                print(f"\n[DRY RUN] Would create multireddit: {m.name} ({len(m.subreddits)} subs)")
            else:
                print(f"\nCreating multireddit: {m.name}")
                success = self.target.create_multireddit(m.name, m.subreddits)
                print(f"  {'OK' if success else 'FAILED'}")

        for m in diff.multis_to_update:
            if self.dry_run:
                print(f"\n[DRY RUN] Would update multireddit: {m.name}")
                if m.add:
                    print(f"  + {len(m.add)} subs")
                if m.remove:
                    print(f"  - {len(m.remove)} subs")
            else:
                print(f"\nUpdating multireddit: {m.name}")
                for sub in m.add:
                    success = self.target.add_sub_to_multi(m.name, sub)
                    print(f"  + {sub}: {'OK' if success else 'FAILED'}")
                for sub in m.remove:
                    success = self.target.remove_sub_from_multi(m.name, sub)
                    print(f"  - {sub}: {'OK' if success else 'FAILED'}")
