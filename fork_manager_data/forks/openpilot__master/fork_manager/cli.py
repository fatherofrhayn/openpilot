#!/usr/bin/env python3
"""
Openpilot Fork Manager 2.0 CLI

Main entry point for all fork/branch management operations.
"""

import argparse
import json
import logging
import os
import sys
from .config import load_config, get_config_value, set_config_value, config_help, LOGS_DIR, FORKS_DIR, OPENPILOT_SYMLINK
from .fork_swap import swap_fork, undo_swap
from .fork_installer import install_fork, update_fork, list_forks
from .settings_handler import backup_settings, restore_settings, list_backups
from .health import run_health_check, repair_all
from .profile_manager import (
    list_profiles, activate_profile, create_profile,
    delete_profile, rename_profile, profile_help
)
from .cleanup import list_disk_usage, delete_fork_branch, delete_old_backups, cleanup_help
from .dry_run import dry_run
from .updater import check_for_updates, self_update

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Main entry point for the Openpilot Fork Manager CLI.

    Handles command line argument parsing and dispatches to appropriate
    command handlers. Manages all fork/branch operations including:
    - Installing/updating forks
    - Swapping between forks/branches
    - Backup/restore of settings
    - Profile management
    - System health checks
    """
    parser = argparse.ArgumentParser(
        description="".join([
            "Openpilot Fork Manager 2.0 - ",
            "Manage, swap, and update Openpilot forks/branches safely."
        ])
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Swap command
    swap_parser = subparsers.add_parser("swap", help="Swap to a different fork/branch")
    swap_parser.add_argument("fork", help="Fork name")
    swap_parser.add_argument("branch", help="Branch name")

    # Undo swap
    _ = subparsers.add_parser("undo", help="Undo last fork/branch swap")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install a new fork/branch from GitHub")
    install_parser.add_argument("git_url", help="GitHub repo URL")
    install_parser.add_argument("branch", help="Branch name")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an installed fork/branch")
    update_parser.add_argument("fork", help="Fork name")
    update_parser.add_argument("branch", help="Branch name")

    # List forks/branches
    _ = subparsers.add_parser("list", help="List all installed forks/branches")

    # Backup settings
    backup_parser = subparsers.add_parser("backup", help="Backup settings for a fork/branch")
    backup_parser.add_argument("fork", help="Fork name")
    backup_parser.add_argument("branch", help="Branch name")

    # Restore settings
    restore_parser = subparsers.add_parser("restore", help="Restore settings for a fork/branch")
    restore_parser.add_argument("fork", help="Fork name")
    restore_parser.add_argument("branch", help="Branch name")
    restore_parser.add_argument(
        "--timestamp",
        help="Timestamp of backup to restore (default: latest)",
        default="latest"
    )

    # List backups
    list_backups_parser = subparsers.add_parser(
        "list-backups",
        help="List settings backups for a fork/branch"
    )
    list_backups_parser.add_argument("fork", help="Fork name")
    list_backups_parser.add_argument("branch", help="Branch name")

    # Health check
    _ = subparsers.add_parser("health", help="Run health check and self-healing")

    # Repair all
    _ = subparsers.add_parser("repair", help="Attempt to auto-repair all issues")

    # Cleanup
    # Cleanup commands
    _ = subparsers.add_parser("cleanup", help="Show cleanup help")
    _ = subparsers.add_parser("disk-usage", help="Show disk usage report")
    delete_fork_parser = subparsers.add_parser("delete-fork", help="Delete a specific fork/branch")
    delete_fork_parser.add_argument("fork", help="Fork name")
    delete_fork_parser.add_argument("branch", help="Branch name")
    delete_backups_parser = subparsers.add_parser(
        "delete-old-backups",
        help="Delete backups older than <days>"
    )
    delete_backups_parser.add_argument("fork", help="Fork name")
    delete_backups_parser.add_argument("branch", help="Branch name")
    delete_backups_parser.add_argument("days", type=int, help="Days old")

    # Profile commands
    _ = subparsers.add_parser("profile", help="Show profile help")
    _ = subparsers.add_parser("profiles", help="List all profiles")
    create_profile_parser = subparsers.add_parser("create-profile", help="Create a new profile")
    create_profile_parser.add_argument("name", help="Profile name")
    create_profile_parser.add_argument("fork", help="Fork name")
    create_profile_parser.add_argument("branch", help="Branch name")
    delete_profile_parser = subparsers.add_parser("delete-profile", help="Delete a profile")
    delete_profile_parser.add_argument("name", help="Profile name")
    rename_profile_parser = subparsers.add_parser("rename-profile", help="Rename a profile")
    rename_profile_parser.add_argument("old_name", help="Old profile name")
    rename_profile_parser.add_argument("new_name", help="New profile name")
    activate_profile_parser = subparsers.add_parser("activate-profile", help="Activate a profile")
    activate_profile_parser.add_argument("profile", help="Profile name")

    # Dry run
    dry_run_parser = subparsers.add_parser(
        "dry-run",
        help="Simulate a destructive action (no changes made)"
    )
    dry_run_parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to simulate")

    # Config commands
    _ = subparsers.add_parser("config", help="Show config help")
    _ = subparsers.add_parser("config-show", help="Show current configuration")
    config_get_parser = subparsers.add_parser("config-get", help="Get a specific config value")
    config_get_parser.add_argument("key", help="Configuration key")
    config_set_parser = subparsers.add_parser("config-set", help="Set a specific config value")
    config_set_parser.add_argument("key", help="Configuration key")
    config_set_parser.add_argument("value", help="Configuration value (true/false for booleans)")

    # Self-update command
    _ = subparsers.add_parser("self-update", help="Update the Fork Manager itself")


    args = parser.parse_args()

    # Load config early
    config = load_config()
    # migration guard: ensure active symlink under managed forks
    if os.path.islink(OPENPILOT_SYMLINK):
        real = os.readlink(OPENPILOT_SYMLINK)
        # If target is outside the managed forks directory and looks like an Openpilot repo, migrate it
        if not real.startswith(os.path.abspath(FORKS_DIR) + os.sep):
            base = os.path.basename(real.rstrip(os.sep))
            fork = base
            branch = "master"
            # Try to detect branch (optional: parse .git/HEAD)
            # Only migrate if selfdrive/ exists
            if os.path.isdir(os.path.join(real, "selfdrive")):
                import shutil
                dest = os.path.join(FORKS_DIR, f"{fork}__{branch}")
                if not os.path.exists(dest):
                    print(f"Copying local Openpilot repo from {real} to {dest}...")
                    shutil.copytree(real, dest, symlinks=True)
                # Update symlink
                print(f"Updating symlink {OPENPILOT_SYMLINK} -> {dest}")
                os.unlink(OPENPILOT_SYMLINK)
                os.symlink(dest, OPENPILOT_SYMLINK)
                print(f"Migrated active fork from {real} to managed forks dir as {fork} [{branch}]")
            else:
                print(f"WARNING: {real} does not look like a valid Openpilot repo (missing selfdrive/). Not migrating.")
        else:
            # If the symlink points to a managed fork but that directory is missing or incomplete, warn
            if not os.path.isdir(real) or not os.path.isdir(os.path.join(real, "selfdrive")):
                print(f"WARNING: Managed fork at {real} is missing or incomplete. Please repair or reinstall.")

    # Setup logging (now uses environment-variable-based path)
    os.makedirs(LOGS_DIR, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(LOGS_DIR, "cli.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # Command dispatch
    if args.command == "swap":
        swap_fork(args.fork, args.branch)
    elif args.command == "undo":
        undo_swap()
    elif args.command == "install":
        install_fork(args.git_url, args.branch)
    elif args.command == "update":
        update_fork(args.fork, args.branch)
    elif args.command == "list":
        list_forks()
    elif args.command == "backup":
        backup_settings(args.fork, args.branch)
    elif args.command == "restore":
        restore_settings(args.fork, args.branch, args.timestamp)
    elif args.command == "list-backups":
        list_backups(args.fork, args.branch)
    elif args.command == "health":
        run_health_check()
    elif args.command == "repair":
        repair_all()
    elif args.command == "cleanup":
        cleanup_help()
    elif args.command == "disk-usage":
        list_disk_usage()
    elif args.command == "delete-fork":
        delete_fork_branch(args.fork, args.branch)
    elif args.command == "delete-old-backups":
        delete_old_backups(args.fork, args.branch, args.days)
    elif args.command == "profile":
        profile_help()
    elif args.command == "profiles":
        list_profiles()
    elif args.command == "create-profile":
        create_profile(args.name, args.fork, args.branch)
    elif args.command == "delete-profile":
        delete_profile(args.name)
    elif args.command == "rename-profile":
        rename_profile(args.old_name, args.new_name)
    elif args.command == "activate-profile":
        activate_profile(args.profile)
    elif args.command == "config":
        config_help()
    elif args.command == "config-show":
        print(json.dumps(config, indent=2))
    elif args.command == "config-get":
        print(get_config_value(args.key))
    elif args.command == "config-set":
        # Handle boolean conversion
        value = args.value
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        set_config_value(args.key, value)
    elif args.command == "self-update":
        self_update()
    elif args.command == "dry-run":
        # Pass the remaining args to the dry_run function
        dry_run(args.command[1:]) # Pass only the remainder args
    else:
        parser.print_help()
        sys.exit(1)

def run():
    """Main execution function that handles:
    - Checking for updates if auto_update is enabled
    - Running the main CLI functionality

    This serves as the entry point when the script is run directly.
    """
    config = load_config()
    if config.get("auto_update"):
        check_for_updates() # Just check and notify, don't auto-install silently
    main()

if __name__ == "__main__":
    # When run directly, ensure package root is in path
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    run()
