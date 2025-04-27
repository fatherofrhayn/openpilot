# integration/backend_merge.md

## 1. Overview  
This document catalogs overlapping backend logic in **SoftwarePanel** and **ForkManagerPanel**, then assigns authoritative implementations and outlines how to unify them under a single facade (`SoftwareManager.triggerUpdate`).

---

## 2. Update Check & Download

| Concern             | SoftwarePanel                           | ForkManagerPanel                          | Authoritative         |
|---------------------|-----------------------------------------|-------------------------------------------|-----------------------|
| Trigger “check”     | `std::system("pkill -SIGUSR1 …")`     | `fork_manager list forks` (indirect)      | Fork Manager CLI       |
| Trigger “download”  | `std::system("pkill -SIGHUP …")`      | `fork_manager self-update`                | Fork Manager CLI       |
| Polling status      | ParamWatcher on `UpdaterState` etc.     | QProcess readyRead + logView append       | ParamWatcher + CLI logs|

**Merge Plan**  
– Deprecate `system("pkill …")` calls.  
– Route both “check” and “download” via `SoftwareManager.triggerUpdate(UpdateType::LEGACY)` or directly to CLI:
```cpp
void SoftwareManager::triggerUpdate(UpdateType t, QString ref="") {
  switch(t) {
    case UpdateType::CHECK:    runCli("update --check");    break;
    case UpdateType::DOWNLOAD: runCli("update --download"); break;
    //…
  }
}
```
– Keep ParamWatcher for UI state, but read CLI exit codes and stdout for finer-grained progress.

---

## 3. Branch Selection & Activation

| Concern          | SoftwarePanel                           | ForkManagerPanel                          | Authoritative   |
|------------------|-----------------------------------------|-------------------------------------------|-----------------|
| List branches    | `params.get("UpdaterAvailableBranches")`| `fork_manager list forks` + branch combo | Fork Manager CLI|
| Select target    | `MultiOptionDialog::getSelection()`     | `branchCombo` with simple dialog          | UI common       |
| Apply branch     | `params.put("UpdaterTargetBranch",…)` | `fork_manager swap <fork> <branch>`       | Fork Manager CLI|

**Merge Plan**  
– Use CLI to fetch branches: `fork_manager list branches <repo>`.  
– Preserve SoftwarePanel’s branch‑chooser dialog UI.  
– Behind the scenes, call `SoftwareManager.triggerUpdate(UpdateType::FORK, selectedBranch)`.

---

## 4. Uninstall / Cleanup

| Concern      | SoftwarePanel                  | ForkManagerPanel             | Authoritative |
|--------------|--------------------------------|------------------------------|---------------|
| Uninstall SW | `pkill -f system…; DoUninstall`| `fork_manager cleanup`       | CLI           |
| Undo fork    | N/A                            | `fork_manager undo`          | CLI           |

**Merge Plan**  
– Map “Uninstall” action to `SoftwareManager.triggerUpdate(UpdateType::LEGACY_UNINSTALL)`.  
– Map “Undo Fork” to `SoftwareManager.triggerUpdate(UpdateType::FORK_UNDO)`.

---

## 5. Profile & Backup Logic

| Concern         | SoftwarePanel | ForkManagerPanel                          | Authoritative |
|-----------------|---------------|-------------------------------------------|---------------|
| Profile swap    | N/A           | `fork_manager activate_profile <name>`    | CLI           |
| Backup settings | N/A           | `fork_manager backup-profile <name>`      | CLI           |
| Auto‑backup     | N/A           | ParamControl + spinbox for history limit  | UI            |

**Merge Plan**  
– Retain CLI‑driven profile operations as-is.  
– Expose via new `UpdateType::PROFILE_SWAP` and `UpdateType::PERSIST_BACKUP`.

---

## 6. Self‑Update Logic

| Concern      | SoftwarePanel | ForkManagerPanel                          | Authoritative |
|--------------|---------------|-------------------------------------------|---------------|
| Self‑update  | N/A           | `fork_manager self-update`                | CLI           |
| Enable toggle| N/A           | ParamControl `EnableSelfUpdate`           | UI + CLI      |

**Merge Plan**  
– Preserve `EnableSelfUpdate` key.  
– CLI always handles the actual binary upgrade.  
– Use facade `SoftwareManager.triggerUpdate(UpdateType::SELF)`.

---

## 7. CLI vs. Legacy System Calls

- **Decision**: Consolidate on `fork_manager` CLI for all update/swap operations.  
- **Fallback**: For backward compatibility during beta, allow legacy `system()` calls when CLI is unavailable.

---

## 8. Unified Facade Definition

```cpp
// SoftwareManager.h
class SoftwareManager : public QObject {
  Q_OBJECT
public slots:
  enum class UpdateType { CHECK, DOWNLOAD, INSTALL, UNINSTALL, FORK_SWAP, FORK_UPDATE,
                          FORK_CLEANUP, FORK_UNDO, SELF, PROFILE_ACTIVATE, BACKUP };
  void triggerUpdate(UpdateType type, const QString &ref = "");
};
```

- Internally dispatches to `fork_manager` with appropriate flags or to legacy system calls.  
- Emits signals (`updateStarted()`, `updateProgress(int)`, `updateFinished(bool)`) for UI binding.

---

## 9. Next Steps

1. Define `SoftwareManager` API and integrate into `ForkManagerPanel.h`.  
2. Remove direct `system()` calls and ParamWatcher hooks in legacy code.  
3. Write regression tests for each `UpdateType`.  
4. Document CLI commands in `docs/merge_fm_software.md`.

_No code changes yet—this file purely guides the upcoming merge sprint._
