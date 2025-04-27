#!/usr/bin/env python3
"""
fork_installer.py - Install and update Openpilot forks/branches from GitHub

This module handles:
- Installing new forks/branches from GitHub
- Updating existing forks/branches
- Validating installations (must contain selfdrive/)
- Writing/updating .forkmeta.json for provenance
- Logging all actions in structured JSON
- Updating an existing fork/branch via git pull
- Validating the install (must contain selfdrive/)
- Writing/updating .forkmeta.json for provenance
- Logging all actions in structured JSON

Best practices:
- Always validate the presence of selfdrive/ after install/update.
- Use try/except for all subprocess and file operations.
- Log all actions and errors for audit and recovery.
"""

import os
from pathlib import Path
import sys
import json
import time
import subprocess
import shutil
from typing import Any
import re
from .retry import retryable

from .config import FORKS_DIR, LOGS_DIR # Only import what's needed

class InstallError(Exception):
    """Raised for errors during fork installation."""

def _log_action(action, details):
    """
    Log an action or error to fork_installer.log in structured JSON format.
    """
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "details": details
    }
    log_path = os.path.join(LOGS_DIR, "fork_installer.log")
    with open(log_path, "a", encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + "\n")

def _get_fork_path(fork: str, branch: str) -> Path:
    """
    Return a Path for the given fork/branch directory.
    """
    return Path(FORKS_DIR) / f"{fork}__{branch}"

def _write_forkmeta(fork_path, action, git_url, branch, user="system"):
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
        "user": user,
        "git_url": git_url,
        "branch": branch
    })
    meta["last_action"] = action
    meta["last_action_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    meta["git_url"] = git_url
    meta["branch"] = branch
    meta["provenance"] = provenance
    with open(meta_path, "w", encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

def write_fork_info(fork_path: str, git_url: str, branch: str) -> None:
    """Write basic fork metadata: url, branch, installed_at."""
    info = {
        "git_url": git_url,
        "branch": branch,
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    info_path = os.path.join(fork_path, "fork_info.json")
    try:
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2)
    except Exception as e:
        _log_action("fork_info_write_error", {"path": info_path, "error": str(e)})

def get_fork_info(fork_path: str) -> dict[str, Any]:
    """Return dict of metadata from fork_info.json or empty dict."""
    info_path = os.path.join(fork_path, "fork_info.json")
    if not os.path.exists(info_path):
        return {}
    try:
        with open(info_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def get_saved_url(fork_path: str) -> str:
    """Get git_url from fork_info.json or fallback to .forkmeta.json, else 'unknown'."""
    info = get_fork_info(fork_path)
    if info.get("git_url"):
        return info["git_url"]
    meta_path = os.path.join(fork_path, ".forkmeta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            return meta.get("git_url", "unknown")
        except (json.JSONDecodeError, OSError):
            return "unknown"
    return "unknown"

def check_update_available(fork_path: str, branch: str) -> bool:
    """Returns True if origin/<branch> has new commits compared to local HEAD."""
    try:
        subprocess.run(
            ["git", "-C", fork_path, "fetch", "--quiet", "origin"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        local = subprocess.check_output(
            ["git", "-C", fork_path, "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).strip()
        remote = subprocess.check_output(
            ["git", "-C", fork_path, "rev-parse", f"origin/{branch}"],
            stderr=subprocess.DEVNULL
        ).strip()
        return local != remote
    except subprocess.CalledProcessError:
        return False

def _rollback_install(git_url: str, branch: str, name: str | None = None, dry_run: bool = False, force: bool = False):
    """Cleanup partial install on failure."""
    # Determine fork path
    fork = name if name else git_url.rstrip("/").split("/")[-1].replace(".git", "")
    fork_path = _get_fork_path(fork, branch)
    if os.path.exists(fork_path):
        shutil.rmtree(fork_path)

@retryable(retries=3, delay=1, rollback_fn=_rollback_install)
def install_fork(git_url: str, branch: str, name: str | None = None, dry_run: bool = False, force: bool = False, prompt_handler=None) -> None:
    """
    Install a new fork/branch from GitHub.
    - Clones the repo to the specified directory with submodules.
    - Validates the install (must contain selfdrive/).
    - Creates settings/ subdir for per-fork/branch backups.
    - Writes .forkmeta.json and fork_info.json (URL, branch, timestamp).
    - Logs the action.
    - Supports dry_run (preview) and force (overwrite) modes.
    
    Optional parameters:
      name: override local fork name (alphanumeric, dashes, underscores).
      force: skip prompts and overwrite existing directory.
    """
    # Determine local fork name
    if name:
        if not re.match(r'^[A-Za-z0-9_-]+$', name):
            raise InstallError(f"Invalid fork name: {name}")
        fork = name
    else:
        fork = git_url.rstrip("/").split("/")[-1].replace(".git", "")
    target_path = _get_fork_path(fork, branch)
    try:
        if os.path.exists(target_path):
            if not force:
                ans = _confirm_action(f"Fork directory {target_path} already exists. Overwrite?", prompt_handler=prompt_handler)
                if not ans:
                    print(f"Aborting install: directory exists and user declined overwrite.")
                    _log_action("install_abort_exists", {"target": str(target_path)})
                    return
                # else: continue to overwrite
            # Remove existing directory
            shutil.rmtree(target_path)
            _log_action("install_overwrite", {"target": str(target_path)})
        print(f"Target install path: {target_path}")

        if dry_run:
            print(f"DRY RUN: Would create directory {FORKS_DIR} if needed.")
            print(f"DRY RUN: Would run git clone --branch {branch} --single-branch --recurse-submodules {git_url} {target_path}")
            print("DRY RUN: Would validate install (check for selfdrive/).")
            print(f"DRY RUN: Would create settings/ subdir in {target_path}.")
            print("DRY RUN: Would write .forkmeta.json.")
            print("DRY RUN: Would log install action.")
            print(f"DRY RUN: Installed fork {fork} [{branch}] at {target_path}")
            return

        os.makedirs(FORKS_DIR, exist_ok=True)
        _log_action("install_create_dir", {"dir": str(FORKS_DIR)})
        # Clone the repo
        print(f"Cloning {git_url}@{branch} into {target_path}...")
        _log_action("install_clone_start", {"git_url": git_url, "branch": branch, "target": str(target_path)})
        cmd = ["git", "clone", "--branch", branch, "--single-branch", git_url, str(target_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        _log_action("install_clone_result", {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr.strip()}")
        _log_action("install_clone_success", {"target": str(target_path)})
        # Validate
        if not os.path.isdir(os.path.join(target_path, "selfdrive")):
            _log_action("install_validate_failed", {"target": str(target_path)})
            raise FileNotFoundError(f"Missing selfdrive/ in {target_path} after clone")
        _log_action("install_validate_success", {"target": str(target_path)})
        # Create settings/ subdir for per-fork/branch backups
        os.makedirs(os.path.join(target_path, "settings"), exist_ok=True)
        _log_action("install_create_settings", {"target": str(target_path)})
        # Write provenance and metadata
        _write_forkmeta(
            target_path,
            "install",
            git_url,
            branch,
            user=os.getenv("USER", "system")
        )
        write_fork_info(target_path, git_url, branch)
        _log_action("install", {"git_url": git_url, "branch": branch, "target": str(target_path)})
        print(f"Successfully installed fork {name or git_url} [{branch}] at {target_path}")
    except (RuntimeError, FileNotFoundError) as e:
        _log_action("install_error", {"git_url": git_url, "branch": branch, "error": str(e)})
        print(f"Error installing fork: {e}", file=sys.stderr)
        if not dry_run:
            raise InstallError(f"Error installing fork: {e}") from e

def list_forks() -> None:
    """
    List installed fork clones by scanning FORKS_DIR.
    Also ensures the currently active fork (from symlink) is always shown and marked as [active].
    """
    try:
        forks = []  # only managed forks
        # scan managed forks directory
        if os.path.isdir(FORKS_DIR):
            for entry in os.listdir(FORKS_DIR):
                path = os.path.join(FORKS_DIR, entry)
                if not os.path.isdir(path):
                    continue
                # parse name__branch
                fork, branch = entry.split("__", 1) if "__" in entry else (entry, "")
                # validate openpilot layout
                if os.path.isdir(os.path.join(path, "selfdrive")):
                    forks.append((fork, branch, path))
        # Always try to show the currently active fork as [active]
        from .config import OPENPILOT_SYMLINK
        active_path = None
        if os.path.islink(OPENPILOT_SYMLINK):
            active_path = os.path.realpath(OPENPILOT_SYMLINK)
        elif os.path.exists(OPENPILOT_SYMLINK):
            active_path = os.path.abspath(OPENPILOT_SYMLINK)
        active_entry = None
        for fork, branch, path in forks:
            if os.path.abspath(path) == active_path:
                active_entry = (fork, branch, path)
                break
        if not forks and not active_entry:
            print("No installed forks/branches.")
            return
        # Print forks, mark active
        for fork, branch, path in forks:
            # read metadata and update availability
            url = get_saved_url(path)
            update_flag = " (update available)" if check_update_available(path, branch) else ""
            label = (
                f"{fork} [{branch}] ({url}){update_flag} at {path}" if branch
                else f"{fork} ({url}){update_flag} at {path}"
            )
            if os.path.abspath(path) == active_path:
                label += " [active]"
            print(label)
        # If active fork is not in forks, show it anyway
        if active_path and (not active_entry or all(os.path.abspath(p) != active_path for _,_,p in forks)):
            # Try to parse its name and metadata from the path
            base = os.path.basename(active_path)
            if "__" in base:
                fork, branch = base.split("__", 1)
            else:
                fork, branch = base, ""
            url = get_saved_url(active_path)
            update_flag = " (update available)" if check_update_available(active_path, branch) else ""
            label = (
                f"{fork} [{branch}] ({url}){update_flag} at {active_path} [active]" if branch
                else f"{fork} ({url}){update_flag} at {active_path} [active]"
            )
            print(label)
    except Exception as e:
        _log_action("list_error", {"error": str(e)})
        print(f"Error listing forks: {e}", file=sys.stderr)
        sys.exit(1)

def _rollback_update(fork: str, branch: str, dry_run: bool = False) -> None:
    """Reset local changes on update failure."""
    fork_path = _get_fork_path(fork, branch)
    subprocess.run(["git", "-C", fork_path, "reset", "--hard"], check=False)

@retryable(retries=3, delay=1, rollback_fn=_rollback_update)
def update_fork(fork: str, branch: str, dry_run: bool = False, prompt_handler=None) -> None:
    """
    Update an existing fork/branch by running git pull.
    - Validates the update (must contain selfdrive/).
    - Updates .forkmeta.json and logs the action.
    - If dry_run=True, prints what would be done without making changes.
    """
    fork_path = _get_fork_path(fork, branch)
    try:
        if not os.path.isdir(fork_path):
            raise FileNotFoundError(f"Fork/branch directory not found: {fork_path}")
        print(f"Target update path: {fork_path}")

        if not dry_run:
            # Check for uncommitted local changes and prompt before rebase
            status = subprocess.run(["git", "-C", fork_path, "status", "--porcelain"], capture_output=True, text=True)
            if status.stdout.strip():
                print("Local uncommitted changes detected:")
                print(status.stdout)
                ans = _confirm_action("Proceed with rebase update?", prompt_handler=prompt_handler)
                if not ans:
                    print("Update aborted due to local changes.")
                    return

        if dry_run:
            print(f"DRY RUN: Would run git -C {fork_path} pull")
            print("DRY RUN: Would validate update (check for selfdrive/).")
            print("DRY RUN: Would update .forkmeta.json.")
            print("DRY RUN: Would log update action.")
            print(f"DRY RUN: Updated fork {fork} [{branch}] at {fork_path}")
            return

        # Pull latest changes
        cmd = ["git", "-C", fork_path, "pull", "--rebase"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Git pull failed: {result.stderr.strip()}")
        # Validate
        if not os.path.isdir(os.path.join(fork_path, "selfdrive")):
            raise FileNotFoundError(f"Missing selfdrive/ in {fork_path} after update")
        # Retrieve git_url from existing fork_info metadata
        git_url = get_saved_url(fork_path)
        # Update provenance and metadata
        _write_forkmeta(
            fork_path,
            "update",
            git_url or "unknown",
            branch,
            user=os.getenv("USER", "system")
        )
        write_fork_info(fork_path, git_url or "unknown", branch)
        _log_action("update", {"fork": fork, "branch": branch, "target": fork_path})
        print(f"Successfully updated fork {fork} [{branch}] at {fork_path}")
    except (RuntimeError, FileNotFoundError) as e:
        _log_action("update_error", {"fork": fork, "branch": branch, "error": str(e)})
        print(f"Error updating fork: {e}", file=sys.stderr)
        # Don't exit in dry run mode
        if not dry_run:
            sys.exit(1)


def delete_fork_branch(fork, branch, dry_run=False, prompt_handler=None):
    """
    Delete a fork/branch.
    """
    fork_path = _get_fork_path(fork, branch)
    try:
        if not os.path.isdir(fork_path):
            raise FileNotFoundError(f"Fork/branch directory not found: {fork_path}")
        print(f"Target delete path: {fork_path}")

        if dry_run:
            print(f"DRY RUN: Would delete {fork_path}")
            print("DRY RUN: Would log delete action.")
            print(f"DRY RUN: Deleted fork {fork} [{branch}] at {fork_path}")
            return

        if _confirm_action(f"Delete fork {fork} [{branch}]", prompt_handler=prompt_handler):
            try:
                shutil.rmtree(fork_path)
                _log_action("delete_fork", {"fork": fork, "branch": branch, "path": fork_path})
                print(f"Successfully deleted {fork}__{branch}.")
            except (OSError, shutil.Error) as e:
                _log_action("delete_fork_error", {"fork": fork, "branch": branch, "error": str(e)})
                print(f"Error deleting fork: {e}", file=sys.stderr)
    except (RuntimeError, FileNotFoundError) as e:
        _log_action("delete_fork_error", {"fork": fork, "branch": branch, "error": str(e)})
        print(f"Error deleting fork: {e}", file=sys.stderr)
        # Don't exit in dry run mode
        if not dry_run:
            sys.exit(1)

def _confirm_action(prompt: str, prompt_handler=None) -> bool:
    """Prompt the yes/no question to confirm an action, using a handler if provided."""
    from distutils.util import strtobool
    if prompt_handler is not None:
        # Handler should return True/False
        return prompt_handler(prompt)
    while True:
        user_input = input(prompt + " [Y/n]: ").lower()
        try:
            result = strtobool(user_input)
            return result
        except ValueError:
            print("Please use y/n or yes/no\n")
