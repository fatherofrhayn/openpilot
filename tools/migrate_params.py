#!/usr/bin/env python3
"""
Migration script for SoftwareManager params.
Runs once on first launch to map legacy SoftwarePanel and ForkManager keys
into the namespaced SoftwareManager.* keys.
"""
from common.params import Params

# Map old legacy keys to new SoftwareManager.* keys
MAPPING = {
  "UpdaterState":               "SoftwareManager.State",
  "UpdateFailedCount":          "SoftwareManager.FailedCount",
  "UpdaterFetchAvailable":      "SoftwareManager.FetchAvailable",
  "UpdaterCurrentDescription":  "SoftwareManager.CurrentDesc",
  "UpdaterCurrentReleaseNotes": "SoftwareManager.CurrentNotes",
  "UpdaterNewDescription":      "SoftwareManager.NewDesc",
  "UpdaterNewReleaseNotes":     "SoftwareManager.NewNotes",
  "UpdaterAvailableBranches":   "SoftwareManager.AvailableBranches",
  "UpdaterTargetBranch":        "SoftwareManager.TargetBranch",
  "GitBranch":                  "SoftwareManager.CurrentBranch",
  # Preserve existing toggles
  "EnableSelfUpdate":           "SoftwareManager.EnableSelfUpdate",
  "AutoBackup":                 "SoftwareManager.AutoBackup",
  "ShowAdvancedLogs":           "SoftwareManager.ShowAdvancedLogs",
  "BackupHistoryLimit":         "SoftwareManager.BackupHistoryLimit",
}


def run_migration():
  p = Params()
  # Only run once
  if p.getBool("SMigrationDone"):
    return

  # Copy legacy values
  for old_key, new_key in MAPPING.items():
    val = p.get(old_key)
    if val and not p.get(new_key):
      p.put(new_key, val)

  # Initialize new backup timestamp if missing
  if not p.get("SoftwareManager.LastBackupTime"):
    p.put("SoftwareManager.LastBackupTime", "0")

  # Mark migration as done
  p.putBool("SMigrationDone", True)


if __name__ == "__main__":
  run_migration()
