# integration/inventory.md

## 1. Overview
This document inventories the legacy **SoftwarePanel** and the new **ForkManagerPanel**. It lists UI elements, signals/slots, param keys, and backend calls.

---

## 2. SoftwarePanel (legacy)
**Files**  
- `selfdrive/ui/qt/offroad/software_settings.cc`  
- `selfdrive/ui/qt/offroad/settings.h` (declaration)

**Class**  
- `SoftwarePanel : ListWidget`

### 2.1 UI Elements
- QLabel *onroadLbl*  
- LabelControl *versionLbl*  
- ButtonControl *downloadBtn* (“CHECK” / “DOWNLOAD” / state)  
- ButtonControl *installBtn* (“INSTALL”)  
- ButtonControl *targetBranchBtn* (“SELECT”)  
- ButtonControl *uninstallBtn* (“UNINSTALL”)

### 2.2 Layout & Styling
- Vertical `ListWidget`  
- `onroadLbl` styled large font, padding  
- Items added in order: onroadLbl, versionLbl, downloadBtn, installBtn, targetBranchBtn (conditional), uninstallBtn

### 2.3 Signals & Slots
- `downloadBtn.clicked` → lambda toggles between `CHECK` / `DOWNLOAD` or sends `pkill -SIGUSR1` / `-SIGHUP`  
- `installBtn.clicked` → `params.putBool("DoReboot", true)`  
- `targetBranchBtn.clicked` → branch selection dialog (`MultiOptionDialog::getSelection`)  
- ParamWatcher `fs_watch` watches `LastUpdateTime`, `UpdateFailedCount`, `UpdaterState`, `UpdateAvailable`  
- UIState `offroadTransition` → updateLabels()

### 2.4 Backend Calls
- `std::system("pkill -SIGUSR1 -f system.updated.updated")` (check)  
- `std::system("pkill -SIGHUP -f system.updated.updated")` (download)  
- `params.putBool("DoReboot", true)`  
- `params.put("UpdaterTargetBranch", …)`

### 2.5 Params & Keys
- UpdaterState  
- UpdateFailedCount  
- UpdaterFetchAvailable  
- UpdaterCurrentDescription  
- UpdaterCurrentReleaseNotes  
- UpdaterNewDescription  
- UpdaterNewReleaseNotes  
- UpdaterAvailableBranches  
- GitBranch  
- UpdaterTargetBranch  
- DoReboot  
- IsTestedBranch

---

## 3. ForkManagerPanel (new)
**Files**  
- `selfdrive/ui/qt/offroad/ForkManagerPanel.cc`  
- `selfdrive/ui/qt/offroad/ForkManagerPanel.h`

**Class**  
- `ForkManagerPanel : ListWidget`

### 3.1 UI Elements
1. **Status Row**  
   - LabelControl *statusLabel*  
   - LabelControl *diskUsageLabel*  
2. **Profile Management**  
   - QComboBox *profileCombo*  
   - ButtonControl *selectProfileBtn*  
   - ButtonControl *backupProfileBtn*  
   - ButtonControl *restoreProfileBtn*  
3. **Installed Forks**  
   - QComboBox *forkCombo*  
   - QComboBox *branchCombo*  
   - ButtonControl *driveForkBtn*  
   - ButtonControl *updateForkBtn*  
   - ButtonControl *deleteForkBtn*  
   - ButtonControl *undoForkBtn*  
   - ButtonControl *selfUpdateBtn*  
4. **Install New Fork**  
   - ButtonControl *installForkBtn*  
5. **Settings Toggles**  
   - ParamControl *selfUpdateToggle*  
   - ParamControl *autoBackupToggle*  
   - ParamControl *advancedLogsToggle*  
   - QSpinBox *historyLimitSpin*  
6. **Log Area**  
   - QTextEdit *logView*  
   - ButtonControl *clearLogBtn*  
7. **Footer**  
   - ButtonControl *helpBtn*  
   - ButtonControl *aboutBtn*

### 3.2 Layout & Styling
- `ListWidget` with 0 margins, spacing 25  
- Sections wrapped in `LayoutWidget` + `ScrollView`  
- Grid layouts used for buttons & toggles to constrain width  
- `ScrollView::resizeEvent` now clamps content width

### 3.3 Signals & Slots
- `cliProcess` (`QProcess`)  
  - `refreshProfiles()` → `fork_manager list profiles`  
  - `refreshForks()` → `fork_manager list forks`  
  - `onSwapClicked()` → `fork_manager swap <fork> <branch>`  
  - `onInstallClicked()` → `fork_manager install <url> <branch>`  
  - `onUpdateClicked()` → `fork_manager update <fork> <branch>`  
  - `onCleanupClicked()` → `fork_manager cleanup <fork> <branch>`  
  - `onUndoClicked()` → `fork_manager undo <fork>`  
  - `onSelfUpdateClicked()` → `fork_manager self-update`  
- `connect(cliProcess, readyRead…)` → append to *logView*  
- `clearLogBtn.clicked` → `logView->clear()`  
- QSpinBox `valueChanged` → `params.put("BackupHistoryLimit", …)`  
- Profile dialog `ProfileSelectDialog` → `fork_manager activate_profile`

### 3.4 Backend Calls
- All actions routed through the `fork_manager` CLI  
- Params read/written for `BackupHistoryLimit`, toggles keys

### 3.5 Params & Keys
- EnableSelfUpdate  
- AutoBackup  
- ShowAdvancedLogs  
- BackupHistoryLimit  
- *Plus any `fork_manager`–driven params*

---

## 4. Dependencies & Overlaps

| Feature               | SoftwarePanel     | ForkManagerPanel     | Notes                       |
|-----------------------|-------------------|----------------------|-----------------------------|
| Check for updates     | system("pkill…")  | fork_manager list…   | Merge under façade          |
| Install update        | `downloadBtn`     | selfUpdateBtn        | One “Install” button        |
| Branch selection      | targetBranchBtn   | branchCombo          | Consolidate dialog          |
| Uninstall             | uninstallBtn      | cleanupBtn           | Map to `fork_manager undo`  |
| Logs                  | none              | logView              | Keep advanced logs          |
| Settings backup       | none              | autoBackupToggle     | Promote to unified UI       |
| Profiles (new)        | none              | profileCombo         | Addition                     |

---

## 5. Confirmed Decisions
1. **Backend façade** via `SoftwareManager.triggerUpdate(UpdateType, ref)`
2. **Param migration** with `tools/migrate_params.py` + one-time flag
3. **Off-road gating** unchanged
4. **Rename tab** to `SoftwareManagerPanel.{h,cc}` under `offroad/`
5. **Feature flag** `SoftwareManagerUnified` for beta rollout
