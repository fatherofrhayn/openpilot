#!/usr/bin/env python3
"""
health.py - Health monitoring, self-healing, and corruption detection for Fork Manager 2.0
"""

import os
import json
import time
import hashlib

from .config import FORKS_DIR, LOGS_DIR, OPENPILOT_SYMLINK  # Use relative import

def _log_action(action, details):
    os.makedirs(LOGS_DIR, exist_ok=True) # Ensure log dir exists
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "details": details
    }
    log_path = os.path.join(LOGS_DIR, "health.log")
    with open(log_path, "a", encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + "\n")

def _hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def _hash_dir(path):
    hashes = {}
    for root, _, files in os.walk(path):  # dirs unused - replaced with _
        for name in files:
            file_path = os.path.join(root, name)
            rel_path = os.path.relpath(file_path, path)
            hashes[rel_path] = _hash_file(file_path)
    return hashes

def _check_symlink():
    if not os.path.islink(OPENPILOT_SYMLINK):
        return False, f"{OPENPILOT_SYMLINK} is not a symlink"
    target = os.readlink(OPENPILOT_SYMLINK)
    if not os.path.isdir(target):
        return False, f"Symlink target {target} does not exist or is not a directory"
    if not os.path.isdir(os.path.join(target, "selfdrive")):
        return False, f"Symlink target {target} missing selfdrive/"
    return True, f"Symlink is valid and points to {target}"

def _check_fork_dirs():
    issues = []
    if not os.path.isdir(FORKS_DIR):
        issues.append("Forks directory missing")
        return issues
    for entry in os.listdir(FORKS_DIR):
        path = os.path.join(FORKS_DIR, entry)
        if not os.path.isdir(path):
            issues.append(f"{entry} is not a directory")
            continue
        if not os.path.isdir(os.path.join(path, "selfdrive")):
            issues.append(f"{entry} missing selfdrive/")
        settings_dir = os.path.join(path, "settings")
        if not os.path.isdir(settings_dir):
            issues.append(f"{entry} missing settings/ directory")
    return issues

def _check_settings_integrity():
    issues = []
    if not os.path.isdir(FORKS_DIR):
        return issues
    for entry in os.listdir(FORKS_DIR):
        path = os.path.join(FORKS_DIR, entry)
        settings_dir = os.path.join(path, "settings")
        if not os.path.isdir(settings_dir):
            continue
        for backup in os.listdir(settings_dir):
            backup_dir = os.path.join(settings_dir, backup)
            integrity_file = os.path.join(backup_dir, "integrity.json")
            if not os.path.isfile(integrity_file):
                issues.append(f"{entry} {backup} missing integrity.json")
                continue
            try:
                with open(integrity_file, encoding='utf-8') as f:
                    expected_hashes = json.load(f)
                for name, expected in expected_hashes.items():
                    file_path = os.path.join(backup_dir, name)
                    if os.path.isdir(file_path):
                        actual = _hash_dir(file_path)
                    else:
                        actual = _hash_file(file_path)
                    if actual != expected:
                        issues.append(f"{entry} {backup} integrity check failed for {name}")
            except (json.JSONDecodeError, OSError) as e:
                issues.append(f"{entry} {backup} integrity check error: {e}")
    return issues

def run_health_check():
    """Run comprehensive health checks on the Fork Manager system.

    Checks include:
    - Symlink validity
    - Fork directory structure
    - Settings backup integrity

    Returns:
        None: Results are printed to console and logged
    """
    print("Running Fork Manager health check...")
    issues = []
    # Check symlink
    ok, msg = _check_symlink()
    if not ok:
        issues.append(msg)
    print(f"Symlink: {msg}")
    # Check fork dirs
    fork_issues = _check_fork_dirs()
    if fork_issues:
        issues.extend(fork_issues)
    for i in fork_issues:
        print(f"Fork dir: {i}")
    # Check settings integrity
    settings_issues = _check_settings_integrity()
    if settings_issues:
        issues.extend(settings_issues)
    for i in settings_issues:
        print(f"Settings: {i}")
    if not issues:
        print("Health check passed: all systems OK.")
        _log_action("health_check", {"result": "ok"})
    else:
        print("Health check found issues:")
        for i in issues:
            print(f"  - {i}")
        _log_action("health_check", {"result": "issues", "issues": issues})

def _repair_symlink(repaired):
    """Attempt to repair the openpilot symlink."""
    ok, _ = _check_symlink()
    if ok:
        return

    if not os.path.isdir(FORKS_DIR):
        return

    for entry in os.listdir(FORKS_DIR):
        path = os.path.join(FORKS_DIR, entry)
        if not os.path.isdir(os.path.join(path, "selfdrive")):
            continue

        try:
            tmp_link = OPENPILOT_SYMLINK + ".tmp"
            if os.path.islink(tmp_link) or os.path.exists(tmp_link):
                os.unlink(tmp_link)
            os.symlink(path, tmp_link)
            os.replace(tmp_link, OPENPILOT_SYMLINK)
            repaired.append(f"Symlink repaired to {path}")
            return
        except OSError as e:
            repaired.append(f"Failed to repair symlink: {e}")

def repair_all():
    """Attempt automatic repair of common Fork Manager issues.

    Repairs include:
    - Recreating broken/missing symlink
    - Creating missing directories
    """
    print("Attempting auto-repair of common issues...")
    repaired = []

    # Symlink repair
    _repair_symlink(repaired)
    # Settings/dirs repair (just recreate missing dirs)
    if not os.path.isdir(FORKS_DIR):
        os.makedirs(FORKS_DIR, exist_ok=True)
        repaired.append("Created missing forks/ directory")
    for entry in os.listdir(FORKS_DIR):
        path = os.path.join(FORKS_DIR, entry)
        settings_dir = os.path.join(path, "settings")
        if not os.path.isdir(settings_dir):
            os.makedirs(settings_dir, exist_ok=True)
            repaired.append(f"Created missing settings/ for {entry}")
    if repaired:
        print("Auto-repair actions taken:")
        for r in repaired:
            print(f"  - {r}")
        _log_action("repair", {"actions": repaired})
    else:
        print("No repairs needed or possible.")
        _log_action("repair", {"actions": []})
