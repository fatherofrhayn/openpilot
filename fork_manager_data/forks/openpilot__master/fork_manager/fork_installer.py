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
import sys
import json
import time
import subprocess
import shutil

from .config import FORKS_DIR, LOGS_DIR # Only import what's needed

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

def _get_fork_path(fork, branch):
    """
    Return the absolute path to the given fork/branch directory.
    """
    return os.path.join(FORKS_DIR, f"{fork}__{branch}")

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

def install_fork(git_url, branch, dry_run=False):
    """
    Install a new fork/branch from GitHub.
    - Clones the repo to the correct directory.
    - Validates the install (must contain selfdrive/).
    - Creates settings/ subdir for per-fork/branch settings backups.
    - Updates .forkmeta.json and logs the action.
    - If dry_run=True, prints what would be done without making changes.
    """
    fork = git_url.rstrip("/").split("/")[-1].replace(".git", "")
    fork_path = _get_fork_path(fork, branch)
    try:
        if os.path.exists(fork_path):
            raise FileExistsError(f"Fork/branch already exists: {fork_path}")
        print(f"Target install path: {fork_path}")

        if dry_run:
            print(f"DRY RUN: Would create directory {FORKS_DIR} if needed.")
            print(f"DRY RUN: Would run git clone --branch {branch} \\")
            print(f"  --single-branch {git_url} {fork_path}")
            print("DRY RUN: Would validate install (check for selfdrive/).")
            print(f"DRY RUN: Would create settings/ subdir in {fork_path}.")
            print("DRY RUN: Would write .forkmeta.json.")
            print("DRY RUN: Would log install action.")
            print(f"DRY RUN: Installed fork {fork} [{branch}] at {fork_path}")
            return

        os.makedirs(FORKS_DIR, exist_ok=True)
        # Clone the repo
        cmd = ["git", "clone", "--branch", branch, "--single-branch", git_url, fork_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr.strip()}")
        # Validate install
        if not os.path.isdir(os.path.join(fork_path, "selfdrive")):
            raise FileNotFoundError(f"Missing selfdrive/ in {fork_path}")
        # Create settings/ subdir for per-fork/branch settings backups
        os.makedirs(os.path.join(fork_path, "settings"), exist_ok=True)
        # Write forkmeta
        _write_forkmeta(fork_path, "install", git_url, branch, user=os.getenv("USER", "system"))
        _log_action("install", {
            "fork": fork,
            "branch": branch,
            "git_url": git_url,
            "target": fork_path
        })
        print(f"Successfully installed fork {fork} [{branch}] at {fork_path}")
    except (RuntimeError, FileExistsError, FileNotFoundError) as e:
        _log_action("install_error", {"git_url": git_url, "branch": branch, "error": str(e)})
        print(f"Error installing fork: {e}", file=sys.stderr)
        # Don't exit in dry run mode
        if not dry_run:
            sys.exit(1)

def update_fork(fork, branch, dry_run=False):
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

        if dry_run:
            print(f"DRY RUN: Would run git -C {fork_path} pull")
            print("DRY RUN: Would validate update (check for selfdrive/).")
            print("DRY RUN: Would update .forkmeta.json.")
            print("DRY RUN: Would log update action.")
            print(f"DRY RUN: Updated fork {fork} [{branch}] at {fork_path}")
            return

        # Pull latest changes
        cmd = ["git", "-C", fork_path, "pull"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Git pull failed: {result.stderr.strip()}")
        # Validate
        if not os.path.isdir(os.path.join(fork_path, "selfdrive")):
            raise FileNotFoundError(f"Missing selfdrive/ in {fork_path} after update")
        # Update forkmeta
        meta_path = os.path.join(fork_path, ".forkmeta.json")
        git_url = None
        if os.path.exists(meta_path):
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
                git_url = meta.get("git_url")
        _write_forkmeta(
            fork_path,
            "update",
            git_url or "unknown",
            branch,
            user=os.getenv("USER", "system")
        )
        _log_action("update", {"fork": fork, "branch": branch, "target": fork_path})
        print(f"Successfully updated fork {fork} [{branch}] at {fork_path}")
    except (RuntimeError, FileNotFoundError) as e:
        _log_action("update_error", {"fork": fork, "branch": branch, "error": str(e)})
        print(f"Error updating fork: {e}", file=sys.stderr)
        # Don't exit in dry run mode
        if not dry_run:
            sys.exit(1)

def list_forks():
    """
    List installed fork clones by scanning FORKS_DIR.
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
        if not forks:
            print("No installed forks/branches.")
            return
        # print each fork entry
        for fork, branch, path in forks:
            if branch:
                print(f"{fork} [{branch}] at {path}")
            else:
                print(f"{fork} at {path}")
    except Exception as e:
        _log_action("list_error", {"error": str(e)})
        print(f"Error listing forks: {e}", file=sys.stderr)
        sys.exit(1)

def delete_fork_branch(fork, branch, dry_run=False):
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

        if _confirm_action(f"Delete fork {fork} [{branch}]"):
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

def _confirm_action(prompt):
    """Prompt the yes/no question to confirm an action."""
    from distutils.util import strtobool
    while True:
        user_input = input(prompt + " [Y/n]: ").lower()
        try:
            result = strtobool(user_input)
            return result
        except ValueError:
            print("Please use y/n or yes/no\n")
