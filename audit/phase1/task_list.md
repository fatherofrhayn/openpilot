# Phase 1 Task List

Priority | Task ID | Component(s)              | Rationale                                       | Effort
------   | ------- | --------------------------|------------------------------------------------ | -----
Critical | T1      | UI Dashboard              | No UI to tune or monitor configurations         | L
Critical | T2      | Test Suite                | No tests for manager functionality               | M
Critical | T3      | CI Integration            | CI broken; lacking baseline CI wiring            | M
Critical | T11     | Build Compatibility      | Resolve `fmemopen` errors in panda/opendbc tests on macOS | S | ✔️
Major    | T4      | API Endpoints             | Manager API incomplete for remote control        | S
Major    | T5      | Live Reconfiguration      | Partial; missing dynamic reload support in loop  | M
Major    | T6      | Documentation             | README_manager incomplete; modules undocumented  | S
Minor    | T7      | Performance Metrics       | Missing metrics collection and reporting         | M
Minor    | T8      | Backup Management         | No snapshot/rollback support                     | M
Minor    | T9      | Security Checks           | Incomplete security validation on configs       | S
Minor    | T10     | Metrics Visualization     | No graphs/dashboard for metrics                  | L
