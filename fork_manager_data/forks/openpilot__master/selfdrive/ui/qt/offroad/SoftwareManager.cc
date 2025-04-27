#include "selfdrive/ui/qt/offroad/SoftwareManager.h"
#include <QDebug>
#include "selfdrive/ui/qt/offroad/PathConfig.h"
#include <QCoreApplication>
#include <QMessageBox>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonValue>
#include <QJsonObject>
#include <QtGlobal>

SoftwareManager::SoftwareManager(QObject *parent)
  : QObject(parent), process_(new QProcess(this)) {
  // handle process completion
  connect(process_, static_cast<void(QProcess::*)(int, QProcess::ExitStatus)>(&QProcess::finished),
          this, [this](int exitCode, QProcess::ExitStatus exitStatus) {
    bool success = (exitStatus == QProcess::NormalExit && exitCode == 0);
    QByteArray out = process_->readAllStandardOutput();
    QByteArray err = process_->readAllStandardError();
    QStringList lines = QString::fromUtf8(out).split('\n', Qt::SkipEmptyParts);
    QStringList errLines = QString::fromUtf8(err).split('\n', Qt::SkipEmptyParts);
    qDebug() << "QProcess finished. Success:" << success << ", ExitCode:" << exitCode << ", ExitStatus:" << exitStatus;
    qDebug() << "STDOUT:" << lines;
    qDebug() << "STDERR:" << errLines;
    // Surface all output to UI log
    if (!lines.isEmpty()) emit cliOutput(lines.join("\n"));
    if (!errLines.isEmpty()) emit cliOutput(errLines.join("\n"));
    if (currentType_ == UpdateType::LIST_PROFILES) {
      emit profilesListed(lines);
    } else if (currentType_ == UpdateType::LIST_FORKS) {
      emit forksListed(lines);
    }
    if (currentType_ == UpdateType::INSTALL && !success) {
      QString errorMsg = tr("Fork installation failed.\n\nSTDOUT:\n%1\nSTDERR:\n%2").arg(lines.join("\n")).arg(errLines.join("\n"));
      emit cliOutput(errorMsg);
      QMessageBox::critical(nullptr, tr("Fork Install Error"), errorMsg);
    }
    emit updateFinished(currentType_, success);
  });
  // handle errors
  connect(process_, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
    qWarning() << "SoftwareManager process error:" << error;
    // On error, emit empty lists for profiles or forks to populate UI
    if (currentType_ == UpdateType::LIST_PROFILES) {
      emit profilesListed(QStringList());
    } else if (currentType_ == UpdateType::LIST_FORKS) {
      emit forksListed(QStringList());
    }
    emit updateFinished(currentType_, false);
  });
  // Stream CLI stdout/stderr to UI
  connect(process_, &QProcess::readyReadStandardOutput, this, [this]() {
    QString out = QString::fromUtf8(process_->readAllStandardOutput());
    emit cliOutput(out);
  });
  connect(process_, &QProcess::readyReadStandardError, this, [this]() {
    QString err = QString::fromUtf8(process_->readAllStandardError());
    emit cliOutput(err);
  });
}

void SoftwareManager::triggerUpdate(UpdateType type, const QString &ref) {
  qDebug() << "SoftwareManager::triggerUpdate (test log)";
  qDebug() << "SoftwareManager::triggerUpdate called with type:" << static_cast<int>(type) << ", ref:" << ref;
  if (process_->state() != QProcess::NotRunning) {
    qWarning() << "SoftwareManager: QProcess is already running, skipping triggerUpdate for type:" << static_cast<int>(type);
    return;
  }
  currentType_ = type;
  emit updateStarted(type);
  // Use PathConfig to locate CLI
  // Allow CLI override for testing via environment
  QByteArray overrideCli = qgetenv("OPENPILOT_FORK_CLI");
  QString program = overrideCli.isEmpty()
      ? PathConfig::instance().cliBinary()
      : QString::fromUtf8(overrideCli);
  QStringList args;
  switch (type) {
    case UpdateType::LIST_PROFILES:
      args << "profiles";
      break;
    case UpdateType::LIST_FORKS:
      args << "list";
      break;
    case UpdateType::CHECK:
      args << "self-update" << "--check";
      break;
    case UpdateType::DOWNLOAD:
      args << "self-update";
      break;
    case UpdateType::INSTALL: {
      QStringList parts = ref.split("::");
      if (parts.size() == 2) {
        args << "install" << parts[0] << parts[1];
      } else {
        args << "install" << ref;
      }
      break;
    }
    case UpdateType::UNINSTALL:
      args << "cleanup" << ref;
      break;
    case UpdateType::FORK_SWAP: {
      QStringList parts = ref.split("__");
      if (parts.size() == 2) {
        args << "swap" << parts[0] << parts[1];
      } else {
        args << "swap" << ref;
      }
      break;
    }
    case UpdateType::FORK_UPDATE: {
      QStringList parts = ref.split("__");
      if (parts.size() == 2) {
        args << "update" << parts[0] << parts[1];
      } else {
        args << "update" << ref;
      }
      break;
    }
    case UpdateType::FORK_CLEANUP: {
      QStringList parts = ref.split("__");
      if (parts.size() == 2) {
        args << "cleanup" << parts[0] << parts[1];
      } else {
        args << "cleanup" << ref;
      }
      break;
    }
    case UpdateType::FORK_UNDO: {
      QStringList parts = ref.split("__");
      if (parts.size() == 2) {
        args << "undo" << parts[0] << parts[1];
      } else {
        args << "undo" << ref;
      }
      break;
    }
    case UpdateType::SELF_UPDATE:
      args << "self-update";
      break;
    case UpdateType::PROFILE_ACTIVATE:
      args << "activate-profile" << ref;
      break;
    case UpdateType::BACKUP:
      args << "backup-profile" << ref;
      break;
    default:
      break;
  }
  // Fallback: if CLI wrapper not executable, invoke via python3
  QFileInfo cliFi(program);
  if (!cliFi.exists() || !cliFi.isExecutable()) {
    args.prepend(program);
    program = "python3";
    qWarning() << "SoftwareManager: CLI wrapper not executable, falling back to python3 with script:" << args.first();
  }
  qDebug() << "SoftwareManager: about to start process with program:" << program << ", args:" << args;
  qInfo() << "SoftwareManager: starting" << program << args;
  process_->start(program, args);
}
