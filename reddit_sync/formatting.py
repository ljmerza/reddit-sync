"""Output formatting for diffs and sync results."""

import json

from reddit_sync.models import SyncDiff


def print_diff(
    diff: SyncDiff,
    subs_only: bool = False,
    multis_only: bool = False,
    as_json: bool = False,
) -> None:
    """Print the diff in human-readable or JSON format."""
    if as_json:
        print(json.dumps(diff.to_dict(), indent=2))
        return

    if not multis_only:
        print("\nSubreddits:")
        if diff.subs_to_add:
            for sub in sorted(diff.subs_to_add):
                print(f"  + r/{sub}")
        if diff.subs_to_remove:
            for sub in sorted(diff.subs_to_remove):
                print(f"  - r/{sub}")
        if not diff.subs_to_add and not diff.subs_to_remove:
            print("  (no differences)")

    if not subs_only:
        print("\nMultireddits:")
        if diff.multis_to_add:
            for m in diff.multis_to_add:
                print(f"  + {m.name} (new, {len(m.subreddits)} subs)")
        if diff.multis_to_update:
            for m in diff.multis_to_update:
                add_str = f"+{len(m.add)}" if m.add else ""
                remove_str = f"-{len(m.remove)}" if m.remove else ""
                changes = ", ".join(filter(None, [add_str, remove_str]))
                print(f"  ~ {m.name} ({changes} subs)")
        if diff.multis_to_remove:
            for m in diff.multis_to_remove:
                print(f"  - {m.name} (in target only)")
        if not diff.multis_to_add and not diff.multis_to_update and not diff.multis_to_remove:
            print("  (no differences)")


def print_subreddit_list(subreddits: list[str]) -> None:
    """Print a numbered list of subreddits."""
    print("-" * 40)
    for i, sub in enumerate(subreddits, 1):
        print(f"  {i:3}. r/{sub}")


def print_multireddit_list(multis: list) -> None:
    """Print multireddits with their subreddit counts."""
    print("-" * 40)
    for m in multis:
        name = m.name if hasattr(m, "name") else m["name"]
        subs = m.subreddits if hasattr(m, "subreddits") else m["subreddits"]
        print(f"  {name} ({len(subs)} subs)")
        for sub in subs[:5]:
            print(f"    - r/{sub}")
        if len(subs) > 5:
            print(f"    ... and {len(subs) - 5} more")
