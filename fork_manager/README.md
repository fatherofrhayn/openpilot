# Openpilot Fork Manager 2.0

## Overview

Openpilot Fork Manager 2.0 is a robust, modular, and Openpilot-native system for managing multiple Openpilot forks and branches on-device. It enables instant, atomic swapping between forks/branches, per-fork settings backup/restore, safe updates, and full auditability—all with maximum reliability and safety.

## User Guide

### Main UI Layout

```
+------------------------------------------------------+
|                    Fork Manager                      |
|   Status: Offroad | Current: kisapilot [release2]    |
+------------------------------------------------------+
| Current Profile: Daily Driver   [Select Profile]     |
| [Create] [Edit] [Delete]                             |
+------------------------------------------------------+
| Installed Forks:                                     |
| ---------------------------------------------------  |
| [kisapilot][release2]   [Drive] [Update] [Delete]    |
| [commaai][master]        [Drive] [Update] [Delete]   |
| [frogpilot][dev]         [Drive] [Update] [Delete]   |
| ---------------------------------------------------  |
| [Install New Fork]                                   |
+------------------------------------------------------+
| Settings:                                            |
| [ ] Enable Self-Update [?]                           |
|     (Allows Fork Manager to update itself from GitHub)
| [ ] Auto-Backup [?]                                  |
|     (Back up settings before every swap)             |
| [ ] Show Advanced Logs [?]                           |
|     (Show detailed logs for troubleshooting)         |
| Backup History Limit: [ 5 ] [?]                      |
|     (Number of backups to keep per fork/branch)      |
+| [Check Updates] [Disk Usage]                         |
|     (Verify manager version & inspect storage usage) |
+------------------------------------------------------+
| Log/Status: [scrollable area] [Clear Log]            |
+------------------------------------------------------+
| [Help] [About]                                       |
+------------------------------------------------------+
```

### Key Workflows

#### Profile Management
- **Current Profile** is always shown at the top.
- **[Select Profile]** opens a modal dialog listing all profiles. Selecting a profile immediately activates it.
- **[Create] [Edit] [Delete]** allow full profile management.

#### Fork Management
- **Installed Forks** are listed with [Drive], [Update], and [Delete] for each.
- **[Install New Fork]** opens a modal dialog for Git URL and branch input.

#### Settings
- All settings are grouped, each with a tooltip or short description.
- **Enable Self-Update** installs requirements if needed.
- **Auto-Backup** and **Show Advanced Logs** are toggles.
- **Backup History Limit** is configurable.

#### Logs and Help
- All actions and errors are shown in the log/status area.
- **[Help]** and **[About]** are always accessible.

#### Manager Maintenance
- **[Check Updates]** checks if a new manager version is available.
- **[Disk Usage]** displays current storage usage of forks and backups.

### Safety and Error Handling
- All destructive actions require confirmation.
- All actions are disabled when not offroad.
- Errors and status messages are clear and actionable.

---

## Simulated User Journey

1. **Startup:**
   - User sees Fork Manager panel with current fork/branch and profile at the top.
2. **Switch Profile:**
   - User taps [Select Profile], modal opens, selects a profile, which is immediately activated.
3. **Install New Fork:**
   - User taps [Install New Fork], modal opens, enters Git URL and branch, confirms install.
4. **Swap Fork:**
   - User taps [Drive] on a fork/branch row, confirms, and Fork Manager swaps to that fork/branch.
5. **Update Fork:**
   - User taps [Update] to pull latest changes for a fork/branch.
6. **Delete Fork:**
   - User taps [Delete], confirms, and the fork/branch is removed.
7. **Settings:**
   - User toggles self-update, auto-backup, or advanced logs as needed.
8. **Logs:**
   - User reviews log/status area for feedback and troubleshooting.
9. **Help/About:**
   - User taps [Help] or [About] for guidance or version info.

---

## Troubleshooting

- **Cannot install fork:** Check Git URL and branch, ensure device has internet.
- **Self-update fails:** Ensure “Enable Self-Update” is toggled on and requirements are installed.
- **Action disabled:** Make sure the vehicle is offroad.
- **Error in log:** Review error message, check settings, and retry.

---

## Developer Notes

- All backend and UI code is modular, well-commented, and follows best practices.
- Modal dialogs are used for all multi-step or complex actions.
- All features are accessible from both CLI and GUI.
- Added utility buttons for manual update check and disk usage.

---

**For further details, see in-app help or contact the project maintainers.**
