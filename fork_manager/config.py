#!/usr/bin/env python3
"""
config.py - Configuration management for Fork Manager 2.0

This module centralizes all persistent paths and config logic.
- FORK_MANAGER_ROOT is set by the FORK_MANAGER_ROOT environment variable, or defaults to ./fork_manager_data for development.
- OPENPILOT_SYMLINK is set by the OPENPILOT_SYMLINK environment variable, or defaults to /data/openpilot on device and ./openpilot_symlink for development.
- All other paths (forks, logs, settings) are derived from this root.
"""

import os
import json

# Centralized base directory for all persistent data
FORK_MANAGER_ROOT = os.environ.get("FORK_MANAGER_ROOT", "./fork_manager_data")
FORKS_DIR = os.path.join(FORK_MANAGER_ROOT, "forks")
LOGS_DIR = os.path.join(FORK_MANAGER_ROOT, "logs")
SETTINGS_DIR = os.path.join(FORK_MANAGER_ROOT, "settings")
CONFIG_FILE = os.path.join(SETTINGS_DIR, "config.json")

# Parameterized Openpilot symlink path
OPENPILOT_SYMLINK = os.environ.get("OPENPILOT_SYMLINK", "./openpilot_symlink")

DEFAULT_CONFIG = {
    "auto_update": True,
    "update_repo": "https://github.com/fatherofrhayn/openpilot.git",
    "update_branch": "manager",
    "backup_history_limit": 5,
    # Add other configurable settings here
}

def load_config():
    """Loads the configuration from file, applying defaults if needed."""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG) # Create with defaults if missing
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        # Ensure all default keys exist
        updated = False
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
                updated = True
        if updated:
            save_config(config) # Save back with defaults added
        return config
    except Exception as e:
        print(f"Error loading config file {CONFIG_FILE}: {e}. Using defaults.")
        return DEFAULT_CONFIG

def save_config(config):
    """Saves the configuration to file."""
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config file {CONFIG_FILE}: {e}")

def get_config_value(key):
    """Gets a specific configuration value."""
    config = load_config()
    return config.get(key, DEFAULT_CONFIG.get(key))

def set_config_value(key, value):
    """Sets a specific configuration value."""
    config = load_config()
    if key not in DEFAULT_CONFIG:
        print(f"Warning: Setting unknown configuration key '{key}'")
    config[key] = value
    save_config(config)
    print(f"Set config '{key}' = {value}")

def config_help():
     print("""
Config management commands:
  config show                           Show current configuration
  config get <key>                      Get a specific config value
  config set <key> <value>              Set a specific config value (e.g., set auto_update true)
""")
