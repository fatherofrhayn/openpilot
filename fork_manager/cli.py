#!/usr/bin/env python3
"""
Openpilot Fork Manager 2.0 CLI

Main entry point for all fork/branch management operations.
"""

import argparse
import sys
import logging
import json
from fork_swap import swap_fork, undo_swap
from fork_installer import install_fork, update_fork, list_forks
from settings_handler import backup_settings, restore_settings, list_backups
from health import run_health_check, repair_all
from profile_manager import list_profiles, activate_profile, create_profile, delete_profile, rename_profile, profile_help
from cleanup import list_disk_usage, delete_fork_branch, delete_old_backups, cleanup_help
from dry_run import dry_run
from config import load_config, get_config_value, set_config_value, config_help, LOGS_DIR
# Import updater functions
from updater import check_for_updates, self_update

def main():
    parser = argparse.ArgumentParser(
        description="Openpilot Fork Manager 2.0 - Manage, swap, and update Openpilot forks/branches safely."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Swap command
    swap_parser = subparsers.add_parser("swap", help="Swap to a different fork/branch")
    swap_parser.add_argument("fork", help="Fork name")
    swap_parser.add_argument("branch", help="Branch name")

    # Undo swap
    undo_parser = subparsers.add_parser("undo", help="Undo last fork/branch swap")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install a new fork/branch from GitHub")
    install_parser.add_argument("git_url", help="GitHub repo URL")
    install_parser.add_argument("branch", help="Branch name")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an installed fork/branch")
    update_parser.add_argument("fork", help="Fork name")
    update_parser.add_argument("branch", help="Branch name")

    # List forks/branches
    list_parser = subparsers.add_parser("list", help="List all installed forks/branches")

    # Backup settings
    backup_parser = subparsers.add_parser("backup", help="Backup settings for a fork/branch")
    backup_parser.add_argument("fork", help="Fork name")
    backup_parser.add_argument("branch", help="Branch name")

    # Restore settings
    restore_parser = subparsers.add_parser("restore", help="Restore settings for a fork/branch")
    restore_parser.add_argument("fork", help="Fork name")
    restore_parser.add_argument("branch", help="Branch name")
    restore_parser.add_argument("--timestamp", help="Timestamp of backup to restore (default: latest)", default="latest")

    # List backups
    list_backups_parser = subparsers.add_parser("list-backups", help="List settings backups for a fork/branch")
    list_backups_parser.add_argument("fork", help="Fork name")
    list_backups_parser.add_argument("branch", help="Branch name")

    # Health check
    health_parser = subparsers.add_parser("health", help="Run health check and self-healing")

    # Repair all
    repair_parser = subparsers.add_parser("repair", help="Attempt to auto-repair all issues")

    # Cleanup
    # Cleanup commands
    cleanup_parser = subparsers.add_parser("cleanup", help="Show cleanup help")
    disk_usage_parser = subparsers.add_parser("disk-usage", help="Show disk usage report")
    delete_fork_parser = subparsers.add_parser("delete-fork", help="Delete a specific fork/branch")
    delete_fork_parser.add_argument("fork", help="Fork name")
    delete_fork_parser.add_argument("branch", help="Branch name")
    delete_backups_parser = subparsers.add_parser("delete-old-backups", help="Delete backups older than <days>")
    delete_backups_parser.add_argument("fork", help="Fork name")
    delete_backups_parser.add_argument("branch", help="Branch name")
    delete_backups_parser.add_argument("days", type=int, help="Days old")

    # Profile commands
    profile_parser = subparsers.add_parser("profile", help="Show profile help")
    profiles_parser = subparsers.add_parser("profiles", help="List all profiles")
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
    dry_run_parser = subparsers.add_parser("dry-run", help="Simulate a destructive action (no changes made)")
    dry_run_parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to simulate")

    # Config commands
    config_parser = subparsers.add_parser("config", help="Show config help")
    config_show_parser = subparsers.add_parser("config-show", help="Show current configuration")
    config_get_parser = subparsers.add_parser("config-get", help="Get a specific config value")
    config_get_parser.add_argument("key", help="Configuration key")
    config_set_parser = subparsers.add_parser("config-set", help="Set a specific config value")
    config_set_parser.add_argument("key", help="Configuration key")
    config_set_parser.add_argument("value", help="Configuration value (true/false for booleans)")

    # Self-update command
    update_self_parser = subparsers.add_parser("self-update", help="Update the Fork Manager itself")


    args = parser.parse_args()

    # Load config early
    config = load_config()

    # Setup logging (now uses environment-variable-based path)
    import os
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
        dry_run(args.command)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    # Check for updates on startup if auto_update is enabled
    config = load_config()
    if config.get("auto_update"):
        check_for_updates() # Just check and notify, don't auto-install silently
    main()
