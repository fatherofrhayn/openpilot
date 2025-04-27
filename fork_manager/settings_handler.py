#!/usr/bin/env python3
"""
settings_handler.py - Manage Openpilot settings per fork/branch

Features:
- Backup settings with rolling history
- Restore from timestamped backups
- Integrity checking via checksums
- Logging of all actions

Best practices:
- Always validate integrity before restoring settings.
- Use try/except for all file operations.
- Log all actions and errors for audit and recovery.
"""

import json
import time
import shutil
import hashlib
import logging
from pathlib import Path
from .config import FORKS_DIR, LOGS_DIR, get_config_value # import config utility

SETTINGS_FILES = [
    "/data/openpilot/params",                # Main Openpilot params directory
    "/data/openpilot/calibration_params",    # Calibration data (if present)
    "/data/openpilot/tuning",                # Tuning parameters (if present)
    "/data/openpilot/profiles",              # Custom profiles (if present)
    # Add any other files/directories as needed for full settings backup
]
#BACKUP_HISTORY_LIMIT = 5  # replaced by config 'backup_history_limit'

class SettingsError(Exception):
    """Raised for settings backup/restore errors."""

def _get_settings_dir(fork: str, branch: str) -> str:
    """
    Return the absolute path to the settings backup directory for a fork/branch.
    """
    return str(Path(FORKS_DIR) / f"{fork}__{branch}" / "settings")

def _log_action(action: str, details: dict) -> None:
    """
    Log an action or error to settings_handler.log in structured JSON format.
    """
    log_dir = Path(LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "settings_handler.log"
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "details": details
    }
    with log_path.open("a", encoding='utf-8') as f:
        f.write(json.dumps(entry) + "\n")

def _get_backup_path(settings_dir: str, timestamp: str) -> str:
    """
    Return the absolute path to a specific backup directory.
    """
    return str(Path(settings_dir) / f"backup_{timestamp}")

def _hash_file(path: str) -> str:
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

def _hash_dir(path: str) -> dict:
    """
    Compute a dictionary of SHA-256 hashes for all files in a directory (relative paths as keys).
    """
    hashes = {}
    # Compute hashes for all files under the directory
    for file in Path(path).rglob('*'):
        if file.is_file():
            rel = file.relative_to(path)
            hashes[str(rel)] = _hash_file(str(file))
    return hashes

def backup_settings(fork: str, branch: str, dry_run: bool = False) -> None:
    """
    Backup Openpilot settings for a fork/branch.
    - Copies all files/dirs in SETTINGS_FILES to a timestamped backup directory.
    - Computes and saves integrity hashes.
    - Enforces rolling history (deletes oldest backups if over limit).
    - Logs the action.
    - If dry_run=True, prints what would be done without making changes.
    """
    settings_dir = Path(_get_settings_dir(fork, branch))
    settings_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    backup_path = _get_backup_path(str(settings_dir), timestamp)
    try:
        Path(backup_path).mkdir()
        # Dry-run: report what would happen without making changes
        if dry_run:
            print(f"DRY RUN: Would create backup directory at {backup_path}")
            count = sum(1 for src in SETTINGS_FILES if Path(src).exists())
            print(f"DRY RUN: Would copy {count} settings files/dirs.")
            return
        # Perform actual copy and hashing
        hashes = {}
        for src in SETTINGS_FILES:
            if Path(src).exists():
                dst = str(Path(backup_path) / Path(src).name)
                if Path(src).is_dir():
                    shutil.copytree(src, dst)
                    hashes[Path(src).name] = _hash_dir(dst)
                else:
                    shutil.copy2(src, dst)
                    hashes[Path(src).name] = _hash_file(dst)
        # Write integrity file
        with open(str(Path(backup_path) / "integrity.json"), "w", encoding='utf-8') as f:
            json.dump(hashes, f, indent=2)
        _log_action("backup", {"fork": fork, "branch": branch, "backup_path": backup_path})
        print(f"Successfully backed up settings for {fork} [{branch}] at {backup_path}")
        # Enforce rolling history
        backups = sorted(
            [d for d in settings_dir.iterdir() if d.name.startswith("backup_")],
            reverse=True
        )
        limit = get_config_value("backup_history_limit")
        for old in backups[limit:]:
            shutil.rmtree(str(old))
    except (OSError, ValueError, shutil.Error) as e:
        _log_action("backup_error", {"fork": fork, "branch": branch, "error": str(e)})
        logging.exception("Error backing up settings")
        if not dry_run:
            raise SettingsError(f"Error backing up settings: {e}") from e

def restore_settings(fork: str, branch: str, timestamp: str = "latest", dry_run: bool = False) -> None:
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
            [d for d in Path(settings_dir).iterdir() if d.name.startswith("backup_")],
            reverse=True
        )
        if not backups:
            print("No backups found.")
            return
        if timestamp == "latest":
            backup_dir = str(backups[0])
        else:
            backup_dir = _get_backup_path(settings_dir, timestamp)
            if not Path(backup_dir).is_dir():
                print(f"Backup {timestamp} not found.")
                return
        # Integrity check
        with open(str(Path(backup_dir) / "integrity.json"), encoding='utf-8') as f:
            expected_hashes = json.load(f)
        for name, expected in expected_hashes.items():
            path = str(Path(backup_dir) / name)
            if Path(path).is_dir():
                actual = _hash_dir(path)
            else:
                actual = _hash_file(path)
            if actual != expected:
                raise ValueError(f"Integrity check failed for {name}")
        print(f"Integrity check passed for {backup_dir}")

        if dry_run:
            print(f"DRY RUN: Would restore settings for {fork} [{branch}] from {backup_dir}")
            return

        # Restore files/directories
        for name in expected_hashes:
            src = str(Path(backup_dir) / name)
            dst = str(Path("/data/openpilot") / name) # Restore to the standard Openpilot path
            if Path(src).is_dir():
                if Path(dst).exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        _log_action("restore", {"fork": fork, "branch": branch, "backup_dir": backup_dir})
        print(f"Successfully restored settings for {fork} [{branch}] from {backup_dir}")
    except (OSError, ValueError, shutil.Error) as e:
        _log_action("restore_error", {"fork": fork, "branch": branch, "error": str(e)})
        logging.exception("Error restoring settings")
        if not dry_run:
            raise SettingsError(f"Error restoring settings: {e}") from e

def list_backups(fork: str, branch: str) -> None:
    """
    List all available settings backups for a fork/branch.
    """
    settings_dir = _get_settings_dir(fork, branch)
    try:
        backups = sorted(
            [d for d in Path(settings_dir).iterdir() if d.name.startswith("backup_")],
            reverse=True
        )
        print(f"Backups for {fork} [{branch}]:")
        for b in backups:
            print(f"  {b.name}")
    except (OSError, ValueError) as e:
        _log_action("list_backups_error", {"fork": fork, "branch": branch, "error": str(e)})
        logging.exception("Error listing backups")
        raise SettingsError(f"Error listing backups: {e}") from e
