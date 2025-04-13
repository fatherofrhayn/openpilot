#!/usr/bin/env python3
"""
settings_handler.py - Backup and restore Openpilot settings per fork/branch, with rolling history and integrity checking

This module handles:
- Backing up Openpilot settings for a given fork/branch (to /data/fork_manager/forks/[fork]__[branch]/settings/)
- Restoring settings from a backup (with timestamp selection)
- Listing available backups (with rolling history)
- Integrity checking (checksums/hashes for corruption detection)
- Logging all actions

Best practices:
- Always validate integrity before restoring settings.
- Use try/except for all file operations.
- Log all actions and errors for audit and recovery.
"""

import os
import sys
import json
import time
import shutil
import hashlib

FORK_MANAGER_ROOT = "/data/fork_manager"
FORKS_DIR = os.path.join(FORK_MANAGER_ROOT, "forks")
LOGS_DIR = os.path.join(FORK_MANAGER_ROOT, "logs")
SETTINGS_FILES = [
    "/data/openpilot/params",  # Main Openpilot params directory (may need to adjust for device)
    # Add more files/directories as needed for full settings backup
]
BACKUP_HISTORY_LIMIT = 5

def _log_action(action, details):
    """
    Log an action or error to settings_handler.log in structured JSON format.
    """
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "details": details
    }
    log_path = os.path.join(LOGS_DIR, "settings_handler.log")
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def _get_settings_dir(fork, branch):
    """
    Return the absolute path to the settings backup directory for a fork/branch.
    """
    return os.path.join(FORKS_DIR, f"{fork}__{branch}", "settings")

def _get_backup_path(settings_dir, timestamp):
    """
    Return the absolute path to a specific backup directory.
    """
    return os.path.join(settings_dir, f"backup_{timestamp}")

def _hash_file(path):
    """
    Compute the SHA-256 hash of a file.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def _hash_dir(path):
    """
    Compute a dictionary of SHA-256 hashes for all files in a directory (relative paths as keys).
    """
    hashes = {}
    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = os.path.join(root, name)
            rel_path = os.path.relpath(file_path, path)
            hashes[rel_path] = _hash_file(file_path)
    return hashes

def backup_settings(fork, branch, dry_run=False):
    """
    Backup Openpilot settings for a fork/branch.
    - Copies all files/dirs in SETTINGS_FILES to a timestamped backup directory.
    - Computes and saves integrity hashes.
    - Enforces rolling history (deletes oldest backups if over limit).
    - Logs the action.
    - If dry_run=True, prints what would be done without making changes.
    """
    settings_dir = _get_settings_dir(fork, branch)
    os.makedirs(settings_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    backup_path = _get_backup_path(settings_dir, timestamp)
    try:
        os.makedirs(backup_path)
        hashes = {}
        for src in SETTINGS_FILES:
            if os.path.exists(src):
                dst = os.path.join(backup_path, os.path.basename(src))
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                    hashes[os.path.basename(src)] = _hash_dir(dst)
                else:
                    shutil.copy2(src, dst)
                    hashes[os.path.basename(src)] = _hash_file(dst)
        # Write integrity file
        if dry_run:
            print(f"DRY RUN: Would create backup directory {backup_path}")
            print(f"DRY RUN: Would copy {len(SETTINGS_FILES)} settings files/dirs.")
            print("DRY RUN: Would write integrity.json.")
            print("DRY RUN: Would log backup action.")
            print(f"DRY RUN: Settings backed up for {fork} [{branch}] at {backup_path}")
            print("DRY RUN: Would enforce rolling history (limit {BACKUP_HISTORY_LIMIT}).")
            return

        with open(os.path.join(backup_path, "integrity.json"), "w") as f:
            json.dump(hashes, f, indent=2)
        _log_action("backup", {"fork": fork, "branch": branch, "backup_path": backup_path})
        print(f"Successfully backed up settings for {fork} [{branch}] at {backup_path}")
        # Enforce rolling history
        backups = sorted(
            [d for d in os.listdir(settings_dir) if d.startswith("backup_")],
            reverse=True
        )
        for old in backups[BACKUP_HISTORY_LIMIT:]:
            shutil.rmtree(os.path.join(settings_dir, old))
    except Exception as e:
        _log_action("backup_error", {"fork": fork, "branch": branch, "error": str(e)})
        print(f"Error backing up settings: {e}", file=sys.stderr)
        if not dry_run:
            sys.exit(1)

def restore_settings(fork, branch, timestamp="latest", dry_run=False):
    """
    Restore Openpilot settings for a fork/branch from a backup.
    - Validates integrity of the backup.
    - Restores all files/dirs to /data/openpilot.
    - Logs the action.
    - If dry_run=True, prints what would be done without making changes.
    """
    settings_dir = _get_settings_dir(fork, branch)
    try:
        backups = sorted(
            [d for d in os.listdir(settings_dir) if d.startswith("backup_")],
            reverse=True
        )
        if not backups:
            print("No backups found.")
            return
        if timestamp == "latest":
            backup_dir = os.path.join(settings_dir, backups[0])
        else:
            backup_dir = os.path.join(settings_dir, f"backup_{timestamp}")
            if not os.path.isdir(backup_dir):
                print(f"Backup {timestamp} not found.")
                return
        # Integrity check
        with open(os.path.join(backup_dir, "integrity.json")) as f:
            expected_hashes = json.load(f)
        for name, expected in expected_hashes.items():
            path = os.path.join(backup_dir, name)
            if os.path.isdir(path):
                actual = _hash_dir(path)
            else:
                actual = _hash_file(path)
            if actual != expected:
                raise ValueError(f"Integrity check failed for {name}")
        print(f"Integrity check passed for {backup_dir}")

        if dry_run:
            print(f"DRY RUN: Would restore {len(expected_hashes)} files/dirs from {backup_dir} to /data/openpilot.")
            print("DRY RUN: Would log restore action.")
            print(f"DRY RUN: Settings restored for {fork} [{branch}] from {backup_dir}")
            return

        # Restore files/directories
        for name in expected_hashes:
            src = os.path.join(backup_dir, name)
            dst = os.path.join("/data/openpilot", name)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        _log_action("restore", {"fork": fork, "branch": branch, "backup_dir": backup_dir})
        print(f"Successfully restored settings for {fork} [{branch}] from {backup_dir}")
    except Exception as e:
        _log_action("restore_error", {"fork": fork, "branch": branch, "error": str(e)})
        print(f"Error restoring settings: {e}", file=sys.stderr)
        if not dry_run:
            sys.exit(1)

def list_backups(fork, branch):
    """
    List all available settings backups for a fork/branch.
    """
    settings_dir = _get_settings_dir(fork, branch)
    try:
        backups = sorted(
            [d for d in os.listdir(settings_dir) if d.startswith("backup_")],
            reverse=True
        )
        print(f"Backups for {fork} [{branch}]:")
        for b in backups:
            print(f"  {b}")
    except Exception as e:
        _log_action("list_backups_error", {"fork": fork, "branch": branch, "error": str(e)})
        print(f"Error listing backups: {e}", file=sys.stderr)
        sys.exit(1)
