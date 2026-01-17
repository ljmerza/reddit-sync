"""Click-based CLI commands."""

import click

from reddit_sync.diff import compute_diff
from reddit_sync.formatting import print_diff, print_multireddit_list, print_subreddit_list
from reddit_sync.io_utils import confirm, load_export, prompt_auth, save_export
from reddit_sync.models import AccountData
from reddit_sync.reddit.scraper import RedditScraper, create_scraper
from reddit_sync.sync import SyncService


def login_account(label: str) -> tuple[RedditScraper, str]:
    """Login to an account using cookie (interactive)."""
    username, cookie_value = prompt_auth(label)
    scraper = create_scraper(cookie_value)
    scraper.username = username
    print(f"Loaded cookie for {username}")
    return scraper, username


def fetch_from_account(
    scraper: RedditScraper | None = None,
    username: str | None = None,
) -> AccountData | None:
    """Fetch subreddits and multis from a Reddit account."""
    if scraper is None:
        try:
            scraper, username = login_account("SOURCE ACCOUNT (copy from)")
        except Exception as e:
            print(f"Login failed: {e}")
            return None

    print("\nFetching subscribed subreddits...")
    subreddits = scraper.get_subscribed_subreddits()

    print("Fetching multireddits...")
    multis = scraper.get_multireddits()

    account_data = AccountData(
        username=username or "unknown",
        subreddits=subreddits,
        multireddits=multis,
    )

    # Save export immediately
    save_export(account_data)

    return account_data


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Reddit Sync - Copy subreddits and multireddits between accounts."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(sync_cmd)


@cli.command("sync")
@click.option("--source-cookie", "-s", help="Source account reddit_session cookie")
@click.option("--target-cookie", "-t", help="Target account reddit_session cookie")
@click.option("--from-file", "-f", "from_file", help="Load source from export file")
@click.option("--subs/--no-subs", default=None, help="Sync subreddits")
@click.option("--multis/--no-multis", default=None, help="Sync multireddits")
@click.option("--clean", is_flag=True, help="Unsubscribe from subs not in source")
@click.option("--dry-run", is_flag=True, help="Show what would be done without executing")
def sync_cmd(source_cookie, target_cookie, from_file, subs, multis, clean, dry_run):
    """Sync subreddits and multireddits to target account."""
    print("Reddit Sync - Subreddit & Multireddit Copier")
    print("=" * 50)

    # Get source data
    if from_file:
        source_data = load_export(from_file)
    elif source_cookie:
        scraper = create_scraper(source_cookie)
        scraper.username = "source"
        source_data = fetch_from_account(scraper, "source")
    else:
        # Interactive mode
        print("\nSource:")
        print("  1. Fetch from Reddit account")
        print("  2. Load from export file")
        choice = input("Choice [1]: ").strip() or "1"

        if choice == "2":
            source_data = load_export()
        else:
            source_data = fetch_from_account()

    if source_data is None:
        return

    # Determine what to sync
    is_interactive = not source_cookie and not from_file

    if subs is None and is_interactive:
        print(f"\nFound {len(source_data.subreddits)} subscribed subreddits:")
        print_subreddit_list(source_data.subreddits)
        sync_subs = confirm("\nSync these subreddits to target account?")
    else:
        sync_subs = subs if subs is not None else True

    if multis is None and is_interactive:
        if source_data.multireddits:
            print(f"\nFound {len(source_data.multireddits)} multireddits:")
            print_multireddit_list(source_data.multireddits)
            sync_multis = confirm("\nCopy these multireddits to target account?")
        else:
            print("\nNo multireddits found.")
            sync_multis = False
    else:
        sync_multis = multis if multis is not None else True

    if not sync_subs and not sync_multis:
        print("\nNothing to sync. Exiting.")
        return

    # Get target account
    if target_cookie:
        target = create_scraper(target_cookie)
        target.username = "target"
    else:
        try:
            target, _ = login_account("TARGET ACCOUNT (copy to)")
        except Exception as e:
            print(f"Login failed: {e}")
            return

    # Fetch target's current state
    print("\nFetching target's current subscriptions...")
    target_subs = target.get_subscribed_subreddits()
    print(f"Found {len(target_subs)} existing subscriptions on target")

    print("Fetching target's multireddits...")
    target_multis = target.get_multireddits()
    print(f"Found {len(target_multis)} existing multireddits on target")

    # Compute diff
    diff = compute_diff(
        source_data.subreddits if sync_subs else [],
        target_subs if sync_subs else [],
        source_data.multireddits if sync_multis else [],
        target_multis if sync_multis else [],
    )

    # In interactive mode, ask about clean
    if is_interactive and not clean:
        if sync_subs and diff.subs_to_remove and confirm("\nUnsubscribe from subs not in source?"):
            clean = True

    # Show what will happen
    if dry_run:
        print("\n[DRY RUN MODE]")
    print_diff(diff, subs_only=not sync_multis, multis_only=not sync_subs)

    # Execute
    sync_service = SyncService(target, dry_run=dry_run)

    if not dry_run and not is_interactive:
        # Non-interactive, just do it
        sync_service.execute(diff, sync_subs=sync_subs, sync_multis=sync_multis, clean=clean)
    elif not dry_run:
        # Interactive, confirm first
        if confirm("\nProceed with sync?"):
            sync_service.execute(diff, sync_subs=sync_subs, sync_multis=sync_multis, clean=clean)
    else:
        sync_service.execute(diff, sync_subs=sync_subs, sync_multis=sync_multis, clean=clean)

    print("\nSync complete!" if not dry_run else "\n[DRY RUN] No changes made.")


@cli.command("diff")
@click.option("--source-cookie", "-s", help="Source account reddit_session cookie")
@click.option("--target-cookie", "-t", help="Target account reddit_session cookie")
@click.option("--from-file", "-f", "from_file", help="Load source from export file")
@click.option("--subs-only", is_flag=True, help="Only show subreddit differences")
@click.option("--multis-only", is_flag=True, help="Only show multireddit differences")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def diff_cmd(source_cookie, target_cookie, from_file, subs_only, multis_only, as_json):
    """Compare two accounts and show differences."""
    # Get source data
    if from_file:
        source_data = load_export(from_file)
    elif source_cookie:
        scraper = create_scraper(source_cookie)
        scraper.username = "source"
        print("Fetching source subreddits...")
        subreddits = scraper.get_subscribed_subreddits()
        print("Fetching source multireddits...")
        multis = scraper.get_multireddits()
        source_data = AccountData(username="source", subreddits=subreddits, multireddits=multis)
    else:
        click.echo("Error: --source-cookie or --from-file required", err=True)
        raise SystemExit(1)

    if source_data is None:
        return

    # Get target data
    if target_cookie:
        target = create_scraper(target_cookie)
        target.username = "target"
    else:
        click.echo("Error: --target-cookie required", err=True)
        raise SystemExit(1)

    print("Fetching target subreddits...")
    target_subs = target.get_subscribed_subreddits()
    print("Fetching target multireddits...")
    target_multis = target.get_multireddits()

    # Compute and print diff
    diff = compute_diff(
        source_data.subreddits if not multis_only else [],
        target_subs if not multis_only else [],
        source_data.multireddits if not subs_only else [],
        target_multis if not subs_only else [],
    )

    print_diff(diff, subs_only=subs_only, multis_only=multis_only, as_json=as_json)


def main():
    """Entry point for the CLI."""
    cli()
