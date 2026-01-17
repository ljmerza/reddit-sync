"""Pure business logic for computing diffs between accounts."""

from reddit_sync.models import Multireddit, MultiUpdate, SyncDiff


def compute_diff(
    source_subs: list[str],
    target_subs: list[str],
    source_multis: list[Multireddit],
    target_multis: list[Multireddit],
) -> SyncDiff:
    """Compute differences between source and target.

    Args:
        source_subs: Subreddits from source account
        target_subs: Subreddits from target account
        source_multis: Multireddits from source account
        target_multis: Multireddits from target account

    Returns:
        SyncDiff with all differences
    """
    # Case-insensitive subreddit comparison
    source_subs_lower = {s.lower(): s for s in source_subs}
    target_subs_lower = {s.lower(): s for s in target_subs}

    subs_to_add = [source_subs_lower[s] for s in source_subs_lower if s not in target_subs_lower]
    subs_to_remove = [target_subs_lower[s] for s in target_subs_lower if s not in source_subs_lower]

    # Case-insensitive multireddit comparison
    source_multi_map = {m.name.lower(): m for m in source_multis}
    target_multi_map = {m.name.lower(): m for m in target_multis}

    multis_to_add: list[Multireddit] = []
    multis_to_remove: list[Multireddit] = []
    multis_to_update: list[MultiUpdate] = []

    for name_lower, source_multi in source_multi_map.items():
        if name_lower not in target_multi_map:
            multis_to_add.append(source_multi)
        else:
            target_multi = target_multi_map[name_lower]
            source_sub_set = set(s.lower() for s in source_multi.subreddits)
            target_sub_set = set(s.lower() for s in target_multi.subreddits)
            to_add = source_sub_set - target_sub_set
            to_remove = target_sub_set - source_sub_set
            if to_add or to_remove:
                multis_to_update.append(
                    MultiUpdate(
                        name=source_multi.name,
                        add=list(to_add),
                        remove=list(to_remove),
                    )
                )

    for name_lower, target_multi in target_multi_map.items():
        if name_lower not in source_multi_map:
            multis_to_remove.append(target_multi)

    return SyncDiff(
        subs_to_add=subs_to_add,
        subs_to_remove=subs_to_remove,
        multis_to_add=multis_to_add,
        multis_to_remove=multis_to_remove,
        multis_to_update=multis_to_update,
    )
