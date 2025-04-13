 #!/usr/bin/env python3
"""
profile_manager.py - Profile/favorites management for Fork Manager 2.0
"""

import os
import sys
import json
import time

FORK_MANAGER_ROOT = "/data/fork_manager"
SETTINGS_DIR = os.path.join(FORK_MANAGER_ROOT, "settings")
PROFILES_FILE = os.path.join(SETTINGS_DIR, "profiles.json")

def _load_profiles():
    if not os.path.exists(PROFILES_FILE):
        return {}
    with open(PROFILES_FILE, "r") as f:
        return json.load(f)

def _save_profiles(profiles):
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

def list_profiles():
    profiles = _load_profiles()
    if not profiles:
        print("No profiles found.")
        return
    print("Available profiles:")
    for name, data in profiles.items():
        print(f"  {name}: fork={data['fork']} branch={data['branch']} last_used={data.get('last_used', 'never')}")

def create_profile(name, fork, branch):
    profiles = _load_profiles()
    if name in profiles:
        print(f"Profile '{name}' already exists.")
        return
    profiles[name] = {
        "fork": fork,
        "branch": branch,
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "last_used": None
    }
    _save_profiles(profiles)
    print(f"Profile '{name}' created for fork={fork} branch={branch}.")

def delete_profile(name):
    profiles = _load_profiles()
    if name not in profiles:
        print(f"Profile '{name}' does not exist.")
        return
    del profiles[name]
    _save_profiles(profiles)
    print(f"Profile '{name}' deleted.")

def activate_profile(name):
    profiles = _load_profiles()
    if name not in profiles:
        print(f"Profile '{name}' does not exist.")
        return
    fork = profiles[name]["fork"]
    branch = profiles[name]["branch"]
    # Import swap and restore logic
    from fork_swap import swap_fork
    from settings_handler import restore_settings
    swap_fork(fork, branch)
    restore_settings(fork, branch)
    profiles[name]["last_used"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save_profiles(profiles)
    print(f"Profile '{name}' activated: fork={fork} branch={branch}")

def rename_profile(old_name, new_name):
    profiles = _load_profiles()
    if old_name not in profiles:
        print(f"Profile '{old_name}' does not exist.")
        return
    if new_name in profiles:
        print(f"Profile '{new_name}' already exists.")
        return
    profiles[new_name] = profiles.pop(old_name)
    _save_profiles(profiles)
    print(f"Profile '{old_name}' renamed to '{new_name}'.")

def profile_help():
    print("""
Profile management commands:
  create-profile <name> <fork> <branch>   Create a new profile
  delete-profile <name>                   Delete a profile
  rename-profile <old> <new>              Rename a profile
  profiles                               List all profiles
  activate-profile <name>                 Activate a profile (swap + restore settings)
""")
