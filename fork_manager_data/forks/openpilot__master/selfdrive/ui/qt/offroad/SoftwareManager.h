#pragma once

#include <QObject>
#include <QString>
#include <QStringList>
#include <QProcess>

class SoftwareManager : public QObject {
  Q_OBJECT

public:
  enum class UpdateType {
    CHECK,
    DOWNLOAD,
    INSTALL,
    UNINSTALL,
    FORK_SWAP,
    FORK_UPDATE,
    FORK_CLEANUP,
    FORK_UNDO,
    SELF_UPDATE,
    PROFILE_ACTIVATE,
    BACKUP,
    LIST_PROFILES,
    LIST_FORKS
  };

  explicit SoftwareManager(QObject *parent = nullptr);

public slots:
  void triggerUpdate(UpdateType type, const QString &ref = QString());

signals:
  void updateStarted(UpdateType type);
  void updateProgress(int progress);
  void updateFinished(UpdateType type, bool success);
  void profilesListed(const QStringList &profiles);
  void forksListed(const QStringList &forks);
  // Raw output from fork_manager CLI for logging
  void cliOutput(const QString &output);

private:
  QProcess *process_;
  UpdateType currentType_;
};
