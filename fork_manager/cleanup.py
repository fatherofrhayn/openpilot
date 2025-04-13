#!/usr/bin/env python3
"""
cleanup.py - Disk space management and cleanup tools for Fork Manager 2.0
"""

import os
import sys
import shutil
import time
import json

FORK_MANAGER_ROOT = "/data/fork_manager"
FORKS_DIR = os.path.join(FORK_MANAGER_ROOT, "forks")
LOGS_DIR = os.path.join(FORK_MANAGER_ROOT, "logs")

def _log_action(action, details):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "details": details
    }
    log_path = os.path.join(LOGS_DIR, "cleanup.log")
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def _get_dir_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
    return total

def _confirm_action(prompt):
    response = input(f"{prompt} [y/N]: ").lower().strip()
    return response == 'y'

def list_disk_usage():
    print("Disk Usage Report:")
    total_usage = 0
    if os.path.isdir(FORKS_DIR):
        print("  Installed Forks/Branches:")
        for entry in sorted(os.listdir(FORKS_DIR)):
            path = os.path.join(FORKS_DIR, entry)
            if os.path.isdir(path):
                size = _get_dir_size(path)
                total_usage += size
                print(f"    - {entry}: {size / (1024*1024):.2f} MB")
                # Check settings backups within the fork dir
                settings_dir = os.path.join(path, "settings")
                if os.path.isdir(settings_dir):
                    print(f"      Settings Backups:")
                    for backup in sorted(os.listdir(settings_dir)):
                        backup_path = os.path.join(settings_dir, backup)
                        if os.path.isdir(backup_path):
                            backup_size = _get_dir_size(backup_path)
                            total_usage += backup_size
                            print(f"        - {backup}: {backup_size / (1024*1024):.2f} MB")
    print(f"\nTotal Fork Manager Usage: {total_usage / (1024*1024):.2f} MB")

def delete_fork_branch(fork, branch, dry_run=False):
    fork_path = os.path.join(FORKS_DIR, f"{fork}__{branch}")
    if not os.path.isdir(fork_path):
        print(f"Error: Fork/branch {fork}__{branch} not found.")
        return
    size_mb = _get_dir_size(fork_path) / (1024*1024)
    print(f"Found fork {fork} [{branch}] ({size_mb:.2f} MB) at {fork_path}")

    if dry_run:
        print(f"DRY RUN: Would delete directory {fork_path}")
        print("DRY RUN: Would log delete_fork action.")
        print(f"DRY RUN: Deleted {fork}__{branch}.")
        return

    if _confirm_action(f"Delete fork {fork} [{branch}] ({size_mb:.2f} MB)?"):
        try:
            shutil.rmtree(fork_path)
            _log_action("delete_fork", {"fork": fork, "branch": branch, "path": fork_path})
            print(f"Successfully deleted {fork}__{branch}.")
        except Exception as e:
            _log_action("delete_fork_error", {"fork": fork, "branch": branch, "error": str(e)})
            print(f"Error deleting fork: {e}", file=sys.stderr)

def delete_old_backups(fork, branch, days_old, dry_run=False):
    settings_dir = os.path.join(FORKS_DIR, f"{fork}__{branch}", "settings")
    if not os.path.isdir(settings_dir):
        print(f"Error: Settings directory for {fork}__{branch} not found.")
        return
    cutoff_time = time.time() - (days_old * 86400)
    deleted_count = 0
    deleted_size = 0
    print(f"Checking backups older than {days_old} days...")
    for backup in sorted(os.listdir(settings_dir)):
        backup_path = os.path.join(settings_dir, backup)
        if os.path.isdir(backup_path) and backup.startswith("backup_"):
            try:
                backup_time_str = backup.split("_")[1] + "_" + backup.split("_")[2]
                backup_timestamp = time.mktime(time.strptime(backup_time_str, "%Y%m%d_%H%M%S"))
                if backup_timestamp < cutoff_time:
                    size = _get_dir_size(backup_path)
                    if dry_run:
                        print(f"DRY RUN: Would delete backup {backup} ({size / (1024*1024):.2f} MB)")
                        deleted_count += 1
                        deleted_size += size
                        continue # Skip actual deletion in dry run

                    if _confirm_action(f"Delete backup {backup} ({size / (1024*1024):.2f} MB)?"):
                        shutil.rmtree(backup_path)
                        deleted_count += 1
                        deleted_size += size
                        _log_action("delete_backup", {"fork": fork, "branch": branch, "backup": backup})
            except Exception as e:
                print(f"Error processing backup {backup}: {e}")
    if dry_run:
        print(f"DRY RUN: Would have deleted {deleted_count} backups, freeing {deleted_size / (1024*1024):.2f} MB.")
    else:
        print(f"Deleted {deleted_count} backups, freeing {deleted_size / (1024*1024):.2f} MB.")

def cleanup_help():
    print("""
Cleanup commands:
  disk-usage                            Show disk usage report
  delete-fork <fork> <branch>           Delete a specific fork/branch
  delete-old-backups <fork> <branch> <days> Delete backups older than <days>
""")
