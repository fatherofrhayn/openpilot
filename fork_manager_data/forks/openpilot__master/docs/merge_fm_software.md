# docs/merge_fm_software.md

## Overview
This guide describes how to migrate from the legacy **SoftwarePanel** and **ForkManagerPanel** to the unified **Software Manager**. It covers the new UI, backend facade, param migration, and feature-flag rollout.

### Unified UI
- `SoftwareManagerPanel` under `selfdrive/ui/qt/offroad/` combines all controls:
  - Update checks (CHECK/DOWNLOAD/INSTALL/UNINSTALL)
  - Fork operations (Swap, Update, Delete, Undo)
  - Profile management (Select, Backup, Restore)
  - Settings toggles and history limit
  - Log view and Help/About buttons

### Backend Facade
- `SoftwareManager` QObject with slot:
  ```cpp
  enum class UpdateType { CHECK, DOWNLOAD, INSTALL, UNINSTALL, FORK_SWAP, FORK_UPDATE,
                            FORK_CLEANUP, FORK_UNDO, SELF, PROFILE_ACTIVATE, BACKUP };
  Q_SLOT void triggerUpdate(UpdateType type, const QString &ref = "");
  ```
- Internally dispatches to `fork_manager` CLI or legacy `system()` calls as fallback.
- Emits signals: `updateStarted()`, `updateProgress(int)`, `updateFinished(bool)`.

### Parameter Migration
- On first unified-panel launch, `tools/migrate_params.py` runs once (guarded by `SMigrationDone` flag).
- Copies legacy `Updater*` keys to `SoftwareManager.*` namespace, plus initializes:
  - `SoftwareManager.EnableSelfUpdate`
  - `SoftwareManager.AutoBackup`
  - `SoftwareManager.ShowAdvancedLogs`
  - `SoftwareManager.BackupHistoryLimit`
  - `SoftwareManager.LastBackupTime`

### Feature Flag
- `SoftwareManagerUnified` (bool):
  - `false` (default): show legacy Software tab, hide unified panel.
  - `true` : show unified Software Manager panel (with "BETA" badge), hide legacy tab.

### Build & Integration
1. Apply files under `integration/` as per artifacts.
2. Update `.github/workflows/selfdrive_tests.yaml` to include `ui_qtest` job.
3. Ensure `SoftwareManagerPanel.pro` and tests compile.
4. Verify UI flows via QTest and CLI facade tests.

### Roll‑out
See `integration/rollout_plan.md` for multi-stage deployment strategy.
