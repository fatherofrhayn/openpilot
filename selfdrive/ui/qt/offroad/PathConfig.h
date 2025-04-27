#ifndef SELFDRIVE_UI_QT_OFFROAD_PATHCONFIG_H
#define SELFDRIVE_UI_QT_OFFROAD_PATHCONFIG_H

#include <QString>

// Centralized paths for Fork Manager UI and CLI
class PathConfig {
public:
  static PathConfig &instance();

  // Base data directory (forks/, logs/, settings/)
  QString dataRoot() const;
  QString forksDir() const;
  QString logsDir() const;
  QString settingsDir() const;

  // Path to fork_manager CLI binary
  QString cliBinary() const;

private:
  PathConfig();
  QString root_;
  QString cliPath_;
};

#endif // SELFDRIVE_UI_QT_OFFROAD_PATHCONFIG_H
