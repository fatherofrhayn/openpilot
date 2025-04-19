# integration/test_plan.md

## 1. Unit Tests
- **SoftwareManager Tests** (`tests/test_software_manager.cpp`)
  - Verify `triggerUpdate()` dispatches correct CLI calls or `system()` fallback for each `UpdateType`.
  - Mock `QProcess` to simulate exit statuses and stdout, test signal emissions (`updateStarted`, `updateProgress`, `updateFinished`).
- **Param Migration Script** (`tests/test_migrate_params.py`)
  - Create temporary `Params` store, seed legacy keys, run `migrate_params.py`, assert new keys populated and `SMigrationDone` flag set.

## 2. Qt QTest UI Flows
- **SoftwareManagerPanel UI** (`selfdrive/ui/tests/test_software_manager_panel.cpp`)
  - Launch panel in offscreen mode.
  - Simulate clicks: CHECK → assert `SoftwareManager.triggerUpdate(UpdateType::CHECK)` called.
  - Simulate branch selection dialog; mock selection; assert UI label update.
  - Toggle `EnableSelfUpdate` and `AutoBackup`, verify params updated.
  - Click Install, Uninstall, Fork Swap, Profile Swap; verify CLI calls recorded.
  - Verify layout: controls visible and no horizontal overflow.

## 3. Integration Tests
- **CLI Facade End-to-End** (`tests/test_cli_facade.sh`)
  - Stub `fork_manager` binary in PATH to record calls.
  - Execute `SoftwareManager::triggerUpdate` for each type; assert correct invocation arguments.
- **Param Migration End-to-End** (`tests/test_migrate_params.sh`)
  - Use real `Params()` pointing to temp directory; insert legacy values; source script; confirm new store.

## 4. Replay & Safety Tests
- Reuse existing `process_replay` harness to ensure no regressions in off-road gating.
- Add scenarios triggering update calls during on-road → UI buttons disabled.

## 5. Coverage Targets
- Aim ≥ 90% line coverage for `SoftwareManager` and `SoftwareManagerPanel`.
- Add badges to README to show test coverage.

## 6. CI Integration
- Integrate these tests into `ci_update.patch` workflows: unit, ui_qtest, integration.
