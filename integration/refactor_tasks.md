# integration/refactor_tasks.md

## Refactor Plan for Software Manager Merge (Sprint B)
Each task is prefixed `SM-`.

### UI & Code Organization
- SM-001: Create `SoftwareManagerPanel.{h,cc}` in `selfdrive/ui/qt/offroad/`.
- SM-002: Move `ForkManagerPanel` UI code into `SoftwareManagerPanel` section.
- SM-003: Integrate `SoftwarePanel` controls (version labels, CHECK/DOWNLOAD buttons) into the unified panel.
- SM-004: Remove legacy `SoftwarePanel.{h,cc}` after migration.
- SM-005: Refactor sidebar registration: replace `SoftwarePanel` with `SoftwareManagerPanel` in `settings.cc`.

### Backend Facade & API Surface
- SM-010: Define `SoftwareManager` facade class and `UpdateType` enum.
- SM-011: Implement `triggerUpdate()` slot dispatching to CLI or legacy system calls.
- SM-012: Emit Qt signals (`updateStarted`, `updateProgress`, `updateFinished`) for UI binding.
- SM-013: Stub legacy `system()` calls behind facade for beta fallback.

### Parameter Migration & Settings
- SM-020: Implement `migrate_params.py` script under `tools/`.
- SM-021: Invoke migration at first panel show (`SMigrationDone` guard).
- SM-022: Rename param keys to `SoftwareManager.*` in code references.

### CI & Build Configuration
- SM-030: Update `ci.yml` to add build/test steps for `SoftwareManagerPanel`.
- SM-031: Add new test labels and fixtures for QTest.

### Cleanup & Deprecation
- SM-040: Remove `fork_manager/ui/` directory after merge.
- SM-041: Deprecate legacy CLI flags in `fork_manager` only after removal.

### Documentation & Release
- SM-050: Document migration guide (`docs/merge_fm_software.md`).
- SM-051: Update README to reference `SoftwareManager`.
- SM-052: Add feature flag handling for beta toggle.
