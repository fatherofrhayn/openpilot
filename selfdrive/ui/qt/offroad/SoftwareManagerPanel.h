#pragma once

#include "selfdrive/ui/qt/widgets/controls.h"
#include <QPushButton>
#include <QWidget>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QGridLayout>
#include "selfdrive/ui/qt/offroad/SoftwareManager.h"
#include <QComboBox>
#include <QTextEdit>
#include <QSpinBox>
#include <QLabel>
#include <QStringList>

class SoftwareManagerPanel : public ListWidget {
  Q_OBJECT

public:
  using UpdateType = SoftwareManager::UpdateType;

  explicit SoftwareManagerPanel(QWidget *parent = nullptr);

signals:
  void updateStarted(UpdateType type);
  void updateProgress(int progress);
  void updateFinished(UpdateType type, bool success);

private slots:
  void onTriggerClicked(UpdateType type, const QString &ref = QString());
  void onHelpClicked();
  void onAboutClicked();
  void onManagerCliOutput(const QString &output);
  // Manager callback slots (best practice)
  void onManagerUpdateStarted(UpdateType type);
  void onManagerUpdateProgress(int progress);
  void onManagerUpdateFinished(UpdateType type, bool success);
  void onManagerProfilesListed(const QStringList &profiles);
  void onManagerForksListed(const QStringList &forks);

private:
  SoftwareManager *manager_;
  // UI elements
  LabelControl *statusLabel;
  LabelControl *forkLabel;

  // Profile management
  QComboBox *profileCombo;
  ButtonControl *selectProfileBtn;
  ButtonControl *createProfileBtn;
  ButtonControl *editProfileBtn;
  ButtonControl *deleteProfileBtn;

  // Forks list container (dynamic height, no nested scroll)
  QWidget *forksListWidget;
  QVBoxLayout *forksListLayout;
  QStringList lastForkEntries;

  // New Fork action
  ButtonControl *newForkBtn;

  // Settings toggles
  ParamControl *selfUpdateToggle;
  ParamControl *autoBackupToggle;
  ParamControl *advancedLogsToggle;
  QSpinBox *historyLimitSpin;

  // Utility buttons for manual update check and disk usage
  ButtonControl *checkUpdateBtn;
  ButtonControl *diskUsageBtn;

  // Log area
  QTextEdit *logView;
  ButtonControl *clearLogBtn;

  // Footer
  ButtonControl *helpBtn;
  ButtonControl *aboutBtn;
};
