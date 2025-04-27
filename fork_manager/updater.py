#!/usr/bin/env python3
"""
updater.py - Self-update functionality for Fork Manager 2.0
"""

import os
import json
import shutil
import subprocess
import tempfile
import time
import logging
from logging.handlers import RotatingFileHandler

try:
    import requests
except ImportError:
    requests = None

from .config import load_config, FORK_MANAGER_ROOT, LOGS_DIR  # Relative import

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(os.path.join(LOGS_DIR, "updater.log"), maxBytes=5*1024*1024, backupCount=3)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

def _log_action(action, details):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "details": details
    }
    # Log structured JSON to rotating log
    logger.info(json.dumps(log_entry))

def get_local_version():
    """Gets the current local commit hash of the Fork Manager."""
    try:
        cmd = ["git", "-C", FORK_MANAGER_ROOT, "rev-parse", "HEAD"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        _log_action("get_local_version_error", {"error": str(e)})
        return None

def get_remote_version():
    """Gets the latest commit hash from the canonical remote branch."""
    if requests is None:
        _log_action("get_remote_version_error", {"error": "requests module not available"})
        return None
    config = load_config()
    repo_url = config.get("update_repo", "").replace(".git", "") # Ensure base URL
    branch = config.get("update_branch", "manager")
    api_url = f"{repo_url.replace('github.com', 'api.github.com/repos')}/commits/{branch}"
    try:
        headers = {'Accept': 'application/vnd.github.sha'}
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        _log_action("get_remote_version_error", {"url": api_url, "error": str(e)})
        return None

def check_for_updates():
    """Checks if a newer version is available remotely."""
    local_ver = get_local_version()
    remote_ver = get_remote_version()
    logger.info(f"Local version: {local_ver}")
    logger.info(f"Remote version: {remote_ver}")
    if local_ver and remote_ver and local_ver != remote_ver:
        # Further check if remote is actually ahead (simple check here)
        # A more robust check might involve comparing commit dates or using git directly
        logger.info("Update available.")
        return True, remote_ver
    if not remote_ver:
        logger.info("Could not check for updates (remote fetch failed).")
        return False, None
    if not local_ver:
        logger.info("Could not determine local version (not a git repo?).")
        return False, None

    logger.info("Fork Manager is up to date.")
    return False, remote_ver

def self_update(target_version=None):
    """Downloads and installs the latest version."""
    logger.info("Attempting self-update...")
    config = load_config()
    repo_url = config.get("update_repo")
    branch = config.get("update_branch", "manager")
    if not repo_url:
        logger.error("Error: Update repository URL not configured.")
        return

    if target_version is None:
        available, target_version = check_for_updates()
        if not available:
            logger.info("No update needed or check failed.")
            return

    tmpdir = tempfile.mkdtemp()
    try:
        logger.info(f"Cloning {branch} from {repo_url} to {tmpdir}...")
        cmd_clone = ["git", "clone", "--branch", branch, "--single-branch", repo_url, tmpdir]
        subprocess.run(cmd_clone, check=True, capture_output=True)

        # Basic validation (e.g., check if cli.py exists)
        if not os.path.exists(os.path.join(tmpdir, "fork_manager", "cli.py")):
            raise FileNotFoundError("Downloaded update appears incomplete (missing cli.py).")

        logger.info("Update downloaded and validated.")

        # Prepare for atomic replace: move current install to backup
        backup_dir = FORK_MANAGER_ROOT + "_bak"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        logger.info(f"Backing up current installation to {backup_dir}...")
        os.rename(FORK_MANAGER_ROOT, backup_dir)

        # Move new version into place
        logger.info(f"Moving updated version to {FORK_MANAGER_ROOT}...")
        # We need to move the contents of the 'fork_manager' subdir from the clone
        update_source_dir = os.path.join(tmpdir, "fork_manager")
        shutil.move(update_source_dir, FORK_MANAGER_ROOT)

        logger.info("Update successful!")
        _log_action("self_update_success", {"new_version": target_version})

        # Clean up backup
        logger.info("Removing backup...")
        shutil.rmtree(backup_dir)

        # Optional: Restart the CLI? Or notify user to restart.
        logger.info("Please restart the Fork Manager CLI for changes to take effect.")

    except (OSError, subprocess.CalledProcessError, requests.RequestException) as e:
        _log_action("self_update_error", {"error": str(e)})
        logger.exception("Self-update failed")
        # Attempt rollback
        if os.path.exists(backup_dir) and not os.path.exists(FORK_MANAGER_ROOT):
            logger.warning("Attempting rollback...")
            try:
                os.rename(backup_dir, FORK_MANAGER_ROOT)
                logger.info("Rollback successful.")
            except OSError:
                logger.exception("Rollback failed")
        elif os.path.exists(FORK_MANAGER_ROOT) and not os.path.exists(backup_dir):
            logger.info("Original installation seems intact, no rollback needed.")
        else:
            logger.error("Cannot automatically rollback. Manual intervention may be required.")
    finally:
        # Cleanup temp dir
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
