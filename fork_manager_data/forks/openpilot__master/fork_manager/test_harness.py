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

CLI_PATH = os.path.join("fork_manager", "cli.py")

def run(cmd):
    """Execute a shell command and print its output.

    Args:
        cmd (str): The command to execute. If it starts with 'python3 cli.py',
                  it will be automatically converted to use the correct CLI_PATH.

    Returns:
        None: Results are printed to console
    """
    # Always use the correct path to the CLI
    if cmd.startswith("python3 cli.py"):
        cmd = cmd.replace("python3 cli.py", f"python3 {CLI_PATH}")
    print(f"=== Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=False)
    print(f"=== Exit code: {result.returncode}\n")

def main():
    """Execute comprehensive integration tests for Fork Manager.

    Tests include:
    - Fork installation and swapping
    - Settings backup/restore
    - Profile management
    - Error handling scenarios
    - Dry-run simulations
    - Self-update functionality
    """
    git_url = "https://github.com/commaai/openpilot.git"
    branch = "master"
    fork = "openpilot"

    # Install fork/branch
    run(f"python3 -m fork_manager.cli install {git_url} {branch}")

    # List forks
    run("python3 -m fork_manager.cli list")

    # Swap to fork/branch
    run(f"python3 -m fork_manager.cli swap {fork} {branch}")

    # Backup settings
    run(f"python3 -m fork_manager.cli backup {fork} {branch}")

    # List backups
    run(f"python3 -m fork_manager.cli list-backups {fork} {branch}")

    # Restore settings
    run(f"python3 -m fork_manager.cli restore {fork} {branch}")

    # Health check
    run("python3 -m fork_manager.cli health")

    # Undo swap
    run("python3 -m fork_manager.cli undo")

    # Update fork/branch
    run(f"python3 -m fork_manager.cli update {fork} {branch}")

    # Cleanup (real)
    run("python3 -m fork_manager.cli disk-usage")
    # run(f"python3 {CLI_PATH} delete-fork {fork} {branch}") # Example delete
    # run(f"python3 {CLI_PATH} delete-old-backups {fork} {branch} 30") # Example delete

    # Profiles (real)
    run("python3 -m fork_manager.cli profiles")
    run(f"python3 -m fork_manager.cli create-profile test_profile {fork} {branch}")
    run("python3 -m fork_manager.cli profiles")
    run("python3 -m fork_manager.cli activate-profile test_profile")
    run("python3 -m fork_manager.cli rename-profile test_profile test_profile_renamed")
    run(f"python3 {CLI_PATH} profiles")
    run("python3 -m fork_manager.cli delete-profile test_profile_renamed")
    run("python3 -m fork_manager.cli profiles")

    # Dry run (real)
    run(f"python3 -m fork_manager.cli dry-run swap {fork} {branch}")
    run(f"python3 -m fork_manager.cli dry-run delete-fork {fork} {branch}")

    # Error scenarios
    run("python3 -m fork_manager.cli swap nonexistfork nonexistbranch")
    run("python3 -m fork_manager.cli install https://github.com/invalid/repo.git master")
    run("python3 -m fork_manager.cli update nonexistfork nonexistbranch")
    run("python3 -m fork_manager.cli restore nonexistfork nonexistbranch")
    run("python3 -m fork_manager.cli backup nonexistfork nonexistbranch")

    # Self-update (dry run)
    run("python3 -m fork_manager.cli dry-run self-update")

def run_tests():
    """Wrapper function to execute the test suite.

    This provides a clean interface for running tests both programmatically
    and when executed directly from the command line.
    """
    main()

if __name__ == "__main__":
    # When run directly, ensure package root is in path
    import sys
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    run_tests()
