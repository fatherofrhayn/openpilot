#!/usr/bin/env python3
"""
fork_installer.py - Install and update Openpilot forks/branches from GitHub, with validation and provenance logging

This module handles:
- Installing a new fork/branch from a GitHub URL into /data/fork_manager/forks/[fork]__[branch]/
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

from .config import FORK_MANAGER_ROOT, FORKS_DIR, LOGS_DIR # Relative import

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
    with open(log_path, "a") as f:
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
            with open(meta_path, "r") as f:
                meta = json.load(f)
        except Exception:
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
    with open(meta_path, "w") as f:
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
            print(f"DRY RUN: Would run git clone --branch {branch} --single-branch {git_url} {fork_path}")
            print("DRY RUN: Would validate install (check for selfdrive/).")
            print(f"DRY RUN: Would create settings/ subdir in {fork_path}.")
            print("DRY RUN: Would write .forkmeta.json.")
            print("DRY RUN: Would log install action.")
            print(f"DRY RUN: Installed fork {fork} [{branch}] at {fork_path}")
            return

        os.makedirs(FORKS_DIR, exist_ok=True)
        # Clone the repo
        cmd = ["git", "clone", "--branch", branch, "--single-branch", git_url, fork_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr.strip()}")
        # Validate install
        if not os.path.isdir(os.path.join(fork_path, "selfdrive")):
            raise FileNotFoundError(f"Missing selfdrive/ in {fork_path}")
        # Create settings/ subdir for per-fork/branch settings backups
        os.makedirs(os.path.join(fork_path, "settings"), exist_ok=True)
        # Write forkmeta
        _write_forkmeta(fork_path, "install", git_url, branch, user=os.getenv("USER", "system"))
        _log_action("install", {"fork": fork, "branch": branch, "git_url": git_url, "target": fork_path})
        print(f"Successfully installed fork {fork} [{branch}] at {fork_path}")
    except Exception as e:
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
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git pull failed: {result.stderr.strip()}")
        # Validate
        if not os.path.isdir(os.path.join(fork_path, "selfdrive")):
            raise FileNotFoundError(f"Missing selfdrive/ in {fork_path} after update")
        # Update forkmeta
        meta_path = os.path.join(fork_path, ".forkmeta.json")
        git_url = None
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
                git_url = meta.get("git_url")
        _write_forkmeta(fork_path, "update", git_url or "unknown", branch, user=os.getenv("USER", "system"))
        _log_action("update", {"fork": fork, "branch": branch, "target": fork_path})
        print(f"Successfully updated fork {fork} [{branch}] at {fork_path}")
    except Exception as e:
        _log_action("update_error", {"fork": fork, "branch": branch, "error": str(e)})
        print(f"Error updating fork: {e}", file=sys.stderr)
        # Don't exit in dry run mode
        if not dry_run:
            sys.exit(1)

def list_forks():
    """
    List all installed forks/branches and their paths.
    """
    try:
        forks = []
        if os.path.isdir(FORKS_DIR):
            for entry in os.listdir(FORKS_DIR):
                path = os.path.join(FORKS_DIR, entry)
                if os.path.isdir(path):
                    fork, branch = entry.split("__", 1) if "__" in entry else (entry, "")
                    forks.append({"fork": fork, "branch": branch, "path": path})
        print("Installed forks/branches:")
        for f in forks:
            print(f"  {f['fork']} [{f['branch']}] at {f['path']}")
    except Exception as e:
        _log_action("list_error", {"error": str(e)})
        print(f"Error listing forks: {e}", file=sys.stderr)
        sys.exit(1)
