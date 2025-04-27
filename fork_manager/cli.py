#!/usr/bin/env python3
"""
Openpilot Fork Manager 2.0 CLI

Main entry point for all fork/branch management operations.
"""

import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import subprocess
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

# Module-level logging: rotating file + console
os.makedirs(LOGS_DIR, exist_ok=True)
log_file = os.path.join(LOGS_DIR, "cli.log")
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
file_handler.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
file_handler.setFormatter(fmt)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
# Console handler for warnings/errors
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(fmt)
root_logger.addHandler(console_handler)

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
        description=f"Openpilot Fork Manager 2.0 - Manage, swap, and update Openpilot forks/branches safely. Logs at {LOGS_DIR}/cli.log (rotated at 5MB, 3 backups)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Swap command
    swap_parser = subparsers.add_parser("swap", help="Swap to a different fork/branch")
    swap_parser.add_argument("fork", help="Fork name")
    swap_parser.add_argument("branch", help="Branch name")
    swap_parser.add_argument("-d", "--dry-run", action="store_true", help="Simulate swap without making changes")
    swap_parser.set_defaults(func=lambda args: swap_fork(args.fork, args.branch, dry_run=args.dry_run))

    # Undo swap
    undo_parser = subparsers.add_parser("undo", help="Undo last fork/branch swap")
    undo_parser.add_argument("-d", "--dry-run", action="store_true", help="Simulate undo without making changes")
    undo_parser.set_defaults(func=lambda args: undo_swap(dry_run=args.dry_run))

    # Install command
    install_parser = subparsers.add_parser("install", help="Install a new fork/branch from GitHub")
    install_parser.add_argument("git_url", help="GitHub repo URL")
    install_parser.add_argument("branch", help="Branch name")
    install_parser.add_argument("-n", "--name", help="Local fork name (optional)", default=None)
    install_parser.add_argument("-f", "--force", help="Overwrite existing fork without prompt", action="store_true")
    install_parser.add_argument("-d", "--dry-run", action="store_true", help="Simulate install without making changes")
    install_parser.set_defaults(func=lambda args: install_fork(
    args.git_url, args.branch, args.name, dry_run=args.dry_run, force=args.force,
    prompt_handler=lambda prompt: input(prompt + " [Y/n]: ").strip().lower() in ("y", "yes", "")
))

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an installed fork/branch")
    update_parser.add_argument("fork", help="Fork name")
    update_parser.add_argument("branch", help="Branch name")
    update_parser.add_argument("-d", "--dry-run", action="store_true", help="Simulate update without making changes")
    update_parser.set_defaults(func=lambda args: update_fork(
    args.fork, args.branch, dry_run=args.dry_run,
    prompt_handler=lambda prompt: input(prompt + " [Y/n]: ").strip().lower() in ("y", "yes", "")
))

    # List forks/branches
    list_parser = subparsers.add_parser("list", help="List all installed forks/branches")
    list_parser.set_defaults(func=lambda args: list_forks())

    # Backup settings
    backup_parser = subparsers.add_parser("backup", help="Backup settings for a fork/branch")
    backup_parser.add_argument("fork", help="Fork name")
    backup_parser.add_argument("branch", help="Branch name")
    backup_parser.add_argument("-d", "--dry-run", action="store_true", help="Simulate backup without making changes")
    backup_parser.set_defaults(func=lambda args: backup_settings(args.fork, args.branch, dry_run=args.dry_run))

    # Restore settings
    restore_parser = subparsers.add_parser("restore", help="Restore settings for a fork/branch")
    restore_parser.add_argument("fork", help="Fork name")
    restore_parser.add_argument("branch", help="Branch name")
    restore_parser.add_argument(
        "--timestamp",
        help="Timestamp of backup to restore (default: latest)",
        default="latest"
    )
    restore_parser.add_argument("-d", "--dry-run", action="store_true", help="Simulate restore without making changes")
    restore_parser.set_defaults(func=lambda args: restore_settings(args.fork, args.branch, args.timestamp, dry_run=args.dry_run))

    # List backups
    list_backups_parser = subparsers.add_parser(
        "list-backups",
        help="List settings backups for a fork/branch"
    )
    list_backups_parser.add_argument("fork", help="Fork name")
    list_backups_parser.add_argument("branch", help="Branch name")
    list_backups_parser.set_defaults(func=lambda args: list_backups(args.fork, args.branch))

    # Health check
    health_parser = subparsers.add_parser("health", help="Run health check and self-healing")
    health_parser.set_defaults(func=lambda args: run_health_check())

    # Repair all
    repair_parser = subparsers.add_parser("repair", help="Attempt to auto-repair all issues")
    repair_parser.set_defaults(func=lambda args: repair_all())

    # Cleanup
    # Cleanup commands
    cleanup_parser = subparsers.add_parser("cleanup", help="Show cleanup help")
    cleanup_parser.set_defaults(func=lambda args: cleanup_help())
    disk_usage_parser = subparsers.add_parser("disk-usage", help="Show disk usage report")
    disk_usage_parser.set_defaults(func=lambda args: list_disk_usage())
    delete_fork_parser = subparsers.add_parser("delete-fork", help="Delete a specific fork/branch")
    delete_fork_parser.add_argument("fork", help="Fork name")
    delete_fork_parser.add_argument("branch", help="Branch name")
    delete_fork_parser.set_defaults(func=lambda args: delete_fork_branch(
    args.fork, args.branch,
    prompt_handler=lambda prompt: input(prompt + " [Y/n]: ").strip().lower() in ("y", "yes", "")
))
    delete_backups_parser = subparsers.add_parser(
        "delete-old-backups",
        help="Delete backups older than <days>"
    )
    delete_backups_parser.add_argument("fork", help="Fork name")
    delete_backups_parser.add_argument("branch", help="Branch name")
    delete_backups_parser.add_argument("days", type=int, help="Days old")
    delete_backups_parser.set_defaults(func=lambda args: delete_old_backups(args.fork, args.branch, args.days))

    # Profile commands
    profile_parser = subparsers.add_parser("profile", help="Show profile help")
    profile_parser.set_defaults(func=lambda args: profile_help())
    profiles_parser = subparsers.add_parser("profiles", help="List all profiles")
    profiles_parser.set_defaults(func=lambda args: list_profiles())
    create_profile_parser = subparsers.add_parser("create-profile", help="Create a new profile")
    create_profile_parser.add_argument("name", help="Profile name")
    create_profile_parser.add_argument("fork", help="Fork name")
    create_profile_parser.add_argument("branch", help="Branch name")
    create_profile_parser.set_defaults(func=lambda args: create_profile(args.name, args.fork, args.branch))
    delete_profile_parser = subparsers.add_parser("delete-profile", help="Delete a profile")
    delete_profile_parser.add_argument("name", help="Profile name")
    delete_profile_parser.set_defaults(func=lambda args: delete_profile(args.name))
    rename_profile_parser = subparsers.add_parser("rename-profile", help="Rename a profile")
    rename_profile_parser.add_argument("old_name", help="Old profile name")
    rename_profile_parser.add_argument("new_name", help="New profile name")
    rename_profile_parser.set_defaults(func=lambda args: rename_profile(args.old_name, args.new_name))
    activate_profile_parser = subparsers.add_parser("activate-profile", help="Activate a profile")
    activate_profile_parser.add_argument("profile", help="Profile name")
    activate_profile_parser.set_defaults(func=lambda args: activate_profile(args.profile))

    # Dry run
    dry_run_parser = subparsers.add_parser(
        "dry-run",
        help="Simulate a destructive action (no changes made)"
    )
    dry_run_parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to simulate")
    dry_run_parser.set_defaults(func=lambda args: dry_run(args.command))

    # Config commands
    config_parser = subparsers.add_parser("config", help="Show config help")
    config_parser.set_defaults(func=lambda args: config_help())
    config_show_parser = subparsers.add_parser("config-show", help="Show current configuration")
    config_show_parser.set_defaults(func=lambda args: print(json.dumps(load_config(), indent=2)))
    config_get_parser = subparsers.add_parser("config-get", help="Get a specific config value")
    config_get_parser.add_argument("key", help="Configuration key")
    config_get_parser.set_defaults(func=lambda args: print(get_config_value(args.key)))
    config_set_parser = subparsers.add_parser("config-set", help="Set a specific config value")
    config_set_parser.add_argument("key", help="Configuration key")
    config_set_parser.add_argument("value", help="Configuration value (true/false for booleans)")
    config_set_parser.set_defaults(
        func=lambda args: set_config_value(
            args.key,
            True if args.value.lower() == "true" else False if args.value.lower() == "false" else args.value,
        )
    )

    # Self-update command
    self_update_parser = subparsers.add_parser("self-update", help="Update the Fork Manager itself")
    self_update_parser.set_defaults(func=lambda args: self_update())

    args = parser.parse_args()

    # migration guard: ensure active symlink under managed forks
    if os.path.islink(OPENPILOT_SYMLINK):
        real = os.readlink(OPENPILOT_SYMLINK)
        # If target is outside the managed forks directory and looks like an Openpilot repo, migrate it
        if not real.startswith(os.path.abspath(FORKS_DIR) + os.sep):
            # --- Detect repo name from .git/config ---
            repo_name = os.path.basename(os.path.abspath(real))
            branch = "master"
            git_head = os.path.join(real, ".git", "HEAD")
            if os.path.isfile(git_head):
                with open(git_head) as f:
                    head_ref = f.read().strip()
                if head_ref.startswith("ref:"):
                    branch = head_ref.split("/")[-1]
            # Only migrate if selfdrive/ exists
            if os.path.isdir(os.path.join(real, "selfdrive")):
                # Clone existing repo into managed forks directory (keep working copy intact)
                dest = os.path.join(FORKS_DIR, f"{repo_name}__{branch}")
                if not os.path.exists(dest):
                    print(f"Cloning local Openpilot repo from {real} to {dest}...")
                    subprocess.run(["git", "clone", "--branch", branch, "--single-branch", real, dest], check=True)
                # Update symlink
                print(f"Updating symlink {OPENPILOT_SYMLINK} -> {dest}")
                os.unlink(OPENPILOT_SYMLINK)
                os.symlink(dest, OPENPILOT_SYMLINK)
                print(f"Migrated active fork from {real} to managed forks dir as {repo_name} [{branch}]")
                print("Reboot recommended to complete migration.")
            else:
                print(f"WARNING: {real} does not look like a valid Openpilot repo (missing selfdrive/). Not migrating.")
        else:
            # If the symlink points to a managed fork but that directory is missing or incomplete, warn
            if not os.path.isdir(real) or not os.path.isdir(os.path.join(real, "selfdrive")):
                print(f"WARNING: Managed fork at {real} is missing or incomplete. Please repair or reinstall.")

    # Dispatch to the chosen command handler
    args.func(args)

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
