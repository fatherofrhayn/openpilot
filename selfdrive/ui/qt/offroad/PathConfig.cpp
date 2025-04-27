#include "PathConfig.h"
#include <QCoreApplication>
#include <QDir>
#include <QStandardPaths>
#include <QFileInfo>
#include <QDebug>
#include <QProcessEnvironment>

PathConfig &PathConfig::instance() {
  static PathConfig cfg;
  return cfg;
}

PathConfig::PathConfig() {
  // 1) Environment override (FORK_MANAGER_ROOT)
  QByteArray envRoot = QProcessEnvironment::systemEnvironment().value("FORK_MANAGER_ROOT").toUtf8();
  if (!envRoot.isEmpty()) {
    root_ = QString::fromUtf8(envRoot);
  } else {
    // 2) Repo-root sibling to this binary: <repo>/fork_manager_data
    QString binDir = QCoreApplication::applicationDirPath();
    QString repoRoot = QDir(binDir).filePath("../../");
    root_ = QDir(repoRoot).filePath("fork_manager_data");
  }

  // Ensure subdirectories exist
  QDir rootDir(root_);
  rootDir.mkpath("forks");
  rootDir.mkpath("logs");
  rootDir.mkpath("settings");

  // Determine CLI path, prefer env override if valid
  QByteArray envCli = QProcessEnvironment::systemEnvironment().value("FORK_MANAGER_CLI_PATH").toUtf8();
  QString rawCli = QString::fromUtf8(envCli);
  if (!rawCli.isEmpty()) {
    QFileInfo envFi(rawCli);
    if (envFi.exists() && envFi.isExecutable()) {
      cliPath_ = envFi.canonicalFilePath();
    } else {
      qWarning() << "PathConfig: FORK_MANAGER_CLI_PATH set but invalid or not executable:" << rawCli;
      rawCli.clear();
    }
  }
  if (rawCli.isEmpty()) {
    // Derive from repo sibling of UI binary
    QString binDir = QCoreApplication::applicationDirPath();
    rawCli = QDir(binDir).filePath("../../fork_manager/fork_manager");
    QFileInfo fi(rawCli);
    if (!fi.exists() || !fi.isExecutable()) {
      qWarning() << "PathConfig: derived CLI wrapper missing or not executable at:" << rawCli;
    }
    cliPath_ = fi.canonicalFilePath();
  }
  qWarning() << "PathConfig: using CLI binary at:" << cliPath_;
  if (cliPath_.isEmpty()) {
    qWarning() << "PathConfig: no valid fork_manager CLI binary found";
  }
}

QString PathConfig::dataRoot() const {
  return root_;
}

QString PathConfig::forksDir() const {
  return QDir(root_).filePath("forks");
}

QString PathConfig::logsDir() const {
  return QDir(root_).filePath("logs");
}

QString PathConfig::settingsDir() const {
  return QDir(root_).filePath("settings");
}

QString PathConfig::cliBinary() const {
  return cliPath_;
}
