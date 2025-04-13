#pragma once

#include <QWidget>
#include <QProcess>
#include <QComboBox>
#include <QPushButton>
#include <QTextEdit>
#include <QListWidget>
#include <QLineEdit>
#include <QLabel>
#include <QVBoxLayout>
#include <QHBoxLayout>

class ForkManagerPanel : public QWidget {
  Q_OBJECT

public:
  explicit ForkManagerPanel(QWidget *parent = nullptr);

private slots:
  void refreshForks();
  void refreshProfiles();
  void onSwapClicked();
  void onInstallClicked();
  void onUpdateClicked();
  void onBackupClicked();
  void onRestoreClicked();
  void onUndoClicked();
  void onCleanupClicked();
  void onSelfUpdateClicked();
  void onProfileActivated();
  void onProcessFinished(int exitCode, QProcess::ExitStatus exitStatus);
  void onProcessError(QProcess::ProcessError error);

private:
  void runCliCommand(const QString &args);
  void showConfirmation(const QString &message, std::function<void()> onConfirm);

  QComboBox *forkCombo;
  QComboBox *branchCombo;
  QComboBox *profileCombo;
  QPushButton *swapBtn;
  QPushButton *installBtn;
  QPushButton *updateBtn;
  QPushButton *backupBtn;
  QPushButton *restoreBtn;
  QPushButton *undoBtn;
  QPushButton *cleanupBtn;
  QPushButton *selfUpdateBtn;
  QTextEdit *logView;
  QLineEdit *installUrlEdit;
  QLineEdit *installBranchEdit;
  QLabel *diskUsageLabel;
  QLabel *statusLabel;
  QProcess *cliProcess;
};
