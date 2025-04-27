# integration/settings_diff.md

## 1. Existing Param Keys

### 1.1 SoftwarePanel (legacy)
- `UpdaterState`
- `UpdateFailedCount`
- `UpdaterFetchAvailable`
- `UpdaterCurrentDescription`
- `UpdaterCurrentReleaseNotes`
- `UpdaterNewDescription`
- `UpdaterNewReleaseNotes`
- `UpdaterAvailableBranches`
- `UpdaterTargetBranch`
- `GitBranch`
- `DoReboot`
- `IsTestedBranch`

### 1.2 ForkManagerPanel (new)
- `EnableSelfUpdate`
- `AutoBackup`
- `ShowAdvancedLogs`
- `BackupHistoryLimit`
- *(fork_manager CLI–driven settings)*

---

## 2. Overlaps & Clashes

No name collisions. Legacy `Updater*` keys coexist with new `SoftwareManager.*` keys.

---

## 3. Proposed Migration Mapping

| Legacy Key                  | New Key                             | Notes                                    |
|-----------------------------|-------------------------------------|------------------------------------------|
| `UpdaterState`              | `SoftwareManager.State`             | UI state machine                         |
| `UpdateFailedCount`         | `SoftwareManager.FailedCount`       | retry logic                              |
| `UpdaterFetchAvailable`     | `SoftwareManager.FetchAvailable`    | download‑ready flag                      |
| `UpdaterCurrentDescription` | `SoftwareManager.CurrentDesc`       | release notes                            |
| `UpdaterCurrentReleaseNotes`| `SoftwareManager.CurrentNotes`      | detailed notes                           |
| `UpdaterNewDescription`     | `SoftwareManager.NewDesc`           | upcoming version                         |
| `UpdaterNewReleaseNotes`    | `SoftwareManager.NewNotes`          | upcoming release notes                   |
| `UpdaterAvailableBranches`  | `SoftwareManager.AvailableBranches` | branch list                              |
| `UpdaterTargetBranch`       | `SoftwareManager.TargetBranch`      | selected branch                          |
| `GitBranch`                 | `SoftwareManager.CurrentBranch`     | current Git branch                       |
| —                           | `SoftwareManager.EnableSelfUpdate`  | preserve toggle key                      |
| —                           | `SoftwareManager.AutoBackup`        | preserve toggle key                      |
| —                           | `SoftwareManager.ShowAdvancedLogs`  | preserve toggle key                      |
| —                           | `SoftwareManager.BackupHistoryLimit`| preserve numeric history limit           |
| —                           | **SoftwareManager.LastBackupTime**  | new key for backup timestamp             |

> **Note:** Keep `DoReboot` and `IsTestedBranch` untouched—they remain authoritative for reboot/uninstall logic.

---

## 4. Migration Script Spec (`tools/migrate_params.py`)

**Behavior**  
On first unified‑panel startup, if `Params().getBool("SMigrationDone")` is false, run `run_migration()` and then set `SMigrationDone = true`.

```python
#!/usr/bin/env python3
from common.params import Params

# Map old → new
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
  # Legacy toggles
  "EnableSelfUpdate":           "SoftwareManager.AutoBackup",
  "AutoBackup":                 "SoftwareManager.AutoBackup",
  "ShowAdvancedLogs":           "SoftwareManager.ShowAdvancedLogs",
  "BackupHistoryLimit":         "SoftwareManager.BackupHistoryLimit",
}


def run_migration():
  p = Params()
  # copy existing values
  for old_key, new_key in MAPPING.items():
    val = p.get(old_key)
    if val and not p.get(new_key):
      p.put(new_key, val)

  # initialize the new backup‑time key if missing
  if not p.get("SoftwareManager.LastBackupTime"):
    p.put("SoftwareManager.LastBackupTime", "0")

  # mark as done
  p.putBool("SMigrationDone", True)


if __name__ == "__main__":
  run_migration()
```

---

## 5. Resolved Questions
1. `DoReboot` & `IsTestedBranch` kept as-is.  
2. Added `SoftwareManager.LastBackupTime`.  
3. Namespacing under `SoftwareManager.`.  
4. Script runs once via `SMigrationDone` flag.
