#!/usr/bin/env python3
"""
test_harness.py - Comprehensive integration test for Fork Manager 2.0

This script exercises all major CLI commands, including:
- Swap, install, update, backup, restore, undo, cleanup, self-update, profiles
- Dry-run simulation for destructive actions
- Error scenarios (invalid repo, missing branch, etc.)
- Profile management (create, activate, delete, rename)
- Self-update and rollback

Best practices:
- Run this script after any major change to the backend.
- Review all outputs for errors or unexpected behavior.
"""

import subprocess
import os
from dry_run import dry_run

CLI_PATH = os.path.join("fork_manager", "cli.py")

def run(cmd):
    # Always use the correct path to the CLI
    if cmd.startswith("python3 cli.py"):
        cmd = cmd.replace("python3 cli.py", f"python3 {CLI_PATH}")
    print(f"=== Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    print(f"=== Exit code: {result.returncode}\n")

def main():
    GIT_URL = "https://github.com/commaai/openpilot.git"
    BRANCH = "master"
    FORK = "openpilot"

    # Install fork/branch
    run(f"python3 {CLI_PATH} install {GIT_URL} {BRANCH}")

    # List forks
    run(f"python3 {CLI_PATH} list")

    # Swap to fork/branch
    run(f"python3 {CLI_PATH} swap {FORK} {BRANCH}")

    # Backup settings
    run(f"python3 {CLI_PATH} backup {FORK} {BRANCH}")

    # List backups
    run(f"python3 {CLI_PATH} list-backups {FORK} {BRANCH}")

    # Restore settings
    run(f"python3 {CLI_PATH} restore {FORK} {BRANCH}")

    # Health check
    run(f"python3 {CLI_PATH} health")

    # Undo swap
    run(f"python3 {CLI_PATH} undo")

    # Update fork/branch
    run(f"python3 {CLI_PATH} update {FORK} {BRANCH}")

    # Cleanup (real)
    run(f"python3 {CLI_PATH} disk-usage")
    # run(f"python3 {CLI_PATH} delete-fork {FORK} {BRANCH}") # Example delete
    # run(f"python3 {CLI_PATH} delete-old-backups {FORK} {BRANCH} 30") # Example delete

    # Profiles (real)
    run(f"python3 {CLI_PATH} profiles")
    run(f"python3 {CLI_PATH} create-profile test_profile {FORK} {BRANCH}")
    run(f"python3 {CLI_PATH} profiles")
    run(f"python3 {CLI_PATH} activate-profile test_profile")
    run(f"python3 {CLI_PATH} rename-profile test_profile test_profile_renamed")
    run(f"python3 {CLI_PATH} profiles")
    run(f"python3 {CLI_PATH} delete-profile test_profile_renamed")
    run(f"python3 {CLI_PATH} profiles")

    # Dry run (real)
    run(f"python3 {CLI_PATH} dry-run swap {FORK} {BRANCH}")
    run(f"python3 {CLI_PATH} dry-run delete-fork {FORK} {BRANCH}")

    # Error scenarios
    run(f"python3 {CLI_PATH} swap nonexistfork nonexistbranch")
    run(f"python3 {CLI_PATH} install https://github.com/invalid/repo.git master")
    run(f"python3 {CLI_PATH} update nonexistfork nonexistbranch")
    run(f"python3 {CLI_PATH} restore nonexistfork nonexistbranch")
    run(f"python3 {CLI_PATH} backup nonexistfork nonexistbranch")

    # Self-update (dry run)
    run(f"python3 {CLI_PATH} dry-run self-update")

if __name__ == "__main__":
    main()
