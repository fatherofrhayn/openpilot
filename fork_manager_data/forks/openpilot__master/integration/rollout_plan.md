# integration/rollout_plan.md

## Two‑Release Roll‑out Strategy

### Release 1: Beta Feature Flag
- **Feature Flag**: `SoftwareManagerUnified` (bool, default `false`).
- **Behavior**:
  - When `false`: legacy **Software** tab visible, unified **Software Manager** hidden.
  - When `true`: show unified **Software Manager** panel with **BETA** badge, hide legacy **Software** tab.
- **Deployment**:
  1. Merge unified panel code guarded by flag.
  2. Add UI indicator ("BETA").
  3. Roll out on `manager` branch. QA and early adopters enable flag via CLI or param.
  4. Monitor bug reports, usage metrics, and CI test coverage.

### Release 2: Legacy Removal
- **Prerequisite**: stable 1 release cycle with flag enabled, zero critical bugs.
- **Steps**:
  1. Remove flag checks and `SoftwareManagerUnified` param.
  2. Delete legacy **SoftwarePanel** files (`software_settings.{cc,h}`).
  3. Rename `SoftwareManagerPanel` to drop BETA badge.
  4. Remove any fallback to legacy `system()` calls.
  5. Update docs to remove legacy references.

## Roll‑out Timeline
| Phase         | Tasks                              | Timeline  |
|---------------|------------------------------------|-----------|
| Beta Launch   | Step 1–4 (Release 1)               | Sprint C  |
| Stabilization | Bug fixes, usage analysis         | 2 weeks   |
| Cleanup       | Legacy removal (Release 2)         | Sprint C end |

## OPEN‑QUESTIONS
- Metrics sources for adoption and error tracking?  
- Should we auto-enable flag for internal builds?  
- Post‑release deprecation warnings for `SoftwarePanel` API?  
