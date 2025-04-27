#!/usr/bin/env python3
"""
fork_swap.py - Atomic symlink swapper, validation, undo, and provenance logging

This module handles:
- Swapping the active Openpilot fork/branch by atomically updating the /data/openpilot symlink.
- Validating that the target fork/branch is complete and safe to use.
- Backing up the previous symlink target for undo.
- Writing and updating .forkmeta.json for provenance tracking.
- Logging all actions and errors in structured JSON format.

Best practices:
- Always use os.replace for atomic symlink updates.
- Confirm the presence of selfdrive/ in the target fork/branch.
- Use try/except for all file and symlink operations.
- Log all actions and errors for audit and recovery.
"""

import os
import sys
import json
import time

from .config import FORKS_DIR, LOGS_DIR, SETTINGS_DIR, OPENPILOT_SYMLINK
UNDO_FILE = os.path.join(SETTINGS_DIR, "last_swap.json")

def _log_action(action, details):
    """
    Log an action or error to fork_swap.log in structured JSON format.
    """
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "details": details
    }
    log_path = os.path.join(LOGS_DIR, "fork_swap.log")
    with open(log_path, "a", encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + "\n")

def _get_fork_path(fork, branch):
    """
    Return the absolute path to the given fork/branch directory.
    """
    return os.path.join(FORKS_DIR, f"{fork}__{branch}")

def _validate_fork_branch(fork, branch):
    """
    Ensure the target fork/branch directory exists and contains selfdrive/.
    Raise FileNotFoundError if invalid.
    """
    fork_path = _get_fork_path(fork, branch)
    if not os.path.isdir(fork_path):
        raise FileNotFoundError(f"Fork/branch directory not found: {fork_path}")
    if not os.path.isdir(os.path.join(fork_path, "selfdrive")):
        raise FileNotFoundError(f"Missing selfdrive/ in {fork_path}")
    return fork_path

def _write_forkmeta(fork_path, action, user="system"):
    """
    Update .forkmeta.json in the fork/branch directory with provenance info.
    """
    meta_path = os.path.join(fork_path, ".forkmeta.json")
    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError):
            meta = {}
    provenance = meta.get("provenance", [])
    provenance.append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "user": user
    })
    meta["last_action"] = action
    meta["last_action_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    meta["provenance"] = provenance
    with open(meta_path, "w", encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

def swap_fork(fork, branch, dry_run=False):
    """
    Atomically swap the active Openpilot fork/branch by updating the /data/openpilot symlink.
    - Validates the target fork/branch.
    - Backs up the previous symlink target for undo.
    - Updates .forkmeta.json and logs the action.
    - If dry_run=True, prints what would be done without making changes.
    """
    try:
        fork_path = _validate_fork_branch(fork, branch)
        print(f"Valid fork/branch found at: {fork_path}")

        # Backup current symlink target for undo
        if os.path.islink(OPENPILOT_SYMLINK):
            prev_target = os.readlink(OPENPILOT_SYMLINK)
        elif os.path.exists(OPENPILOT_SYMLINK):
            raise RuntimeError(
                f"{OPENPILOT_SYMLINK} exists but is not a symlink. Aborting for safety."
            )
        else:
            prev_target = None
        print(f"Previous symlink target: {prev_target}")

        if dry_run:
            print("DRY RUN: Would save undo info.")
            print(f"DRY RUN: Would update symlink {OPENPILOT_SYMLINK} -> {fork_path}")
            print("DRY RUN: Would update .forkmeta.json")
            print("DRY RUN: Would log swap action.")
            print(f"DRY RUN: Swapped to {fork} [{branch}] at {fork_path}")
            return

        # Save undo info for rollback
        undo_info = {
            "prev_target": prev_target,
            "swapped_to": fork_path,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        os.makedirs(os.path.dirname(UNDO_FILE), exist_ok=True)
        with open(UNDO_FILE, "w", encoding='utf-8') as f:
            json.dump(undo_info, f, indent=2)

        # Atomically update symlink
        tmp_link = OPENPILOT_SYMLINK + ".tmp"
        if os.path.islink(tmp_link) or os.path.exists(tmp_link):
            os.unlink(tmp_link)
        os.symlink(fork_path, tmp_link)
        os.replace(tmp_link, OPENPILOT_SYMLINK)

        # Write forkmeta
        _write_forkmeta(fork_path, "swap", user=os.getenv("USER", "system"))

        _log_action("swap", {
            "fork": fork,
            "branch": branch,
            "target": fork_path,
            "prev_target": prev_target
        })
        print(f"Successfully swapped to {fork} [{branch}] at {fork_path}")
    except (RuntimeError, FileNotFoundError, OSError) as e:
        _log_action("swap_error", {"fork": fork, "branch": branch, "error": str(e)})
        print(f"Error swapping fork: {e}", file=sys.stderr)
        # Don't exit in dry run mode
        if not dry_run:
            sys.exit(1)

def undo_swap(dry_run=False):
    """
    Undo the last fork/branch swap by restoring the previous symlink target.
    - Reads the last_swap.json backup.
    - Atomically updates the symlink.
    - Logs the action.
    - If dry_run=True, prints what would be done without making changes.
    """
    try:
        if not os.path.exists(UNDO_FILE):
            print("No previous swap to undo.")
            return
        with open(UNDO_FILE, encoding='utf-8') as f:
            undo_info = json.load(f)
        prev_target = undo_info.get("prev_target")
        if not prev_target:
            print("No previous symlink target recorded. Cannot undo.")
            return
        print(f"Previous target to restore: {prev_target}")

        if dry_run:
            print(f"DRY RUN: Would update symlink {OPENPILOT_SYMLINK} -> {prev_target}")
            print("DRY RUN: Would log undo_swap action.")
            print(f"DRY RUN: Restored previous fork: {prev_target}")
            return

        # Atomically update symlink back
        tmp_link = OPENPILOT_SYMLINK + ".tmp"
        if os.path.islink(tmp_link) or os.path.exists(tmp_link):
            os.unlink(tmp_link)
        os.symlink(prev_target, tmp_link)
        os.replace(tmp_link, OPENPILOT_SYMLINK)
        _log_action("undo_swap", {"restored_target": prev_target})
        print(f"Successfully restored previous fork: {prev_target}")
    except (RuntimeError, FileNotFoundError, OSError) as e:
        _log_action("undo_swap_error", {"error": str(e)})
        print(f"Error undoing swap: {e}", file=sys.stderr)
        # Don't exit in dry run mode
        if not dry_run:
            sys.exit(1)
