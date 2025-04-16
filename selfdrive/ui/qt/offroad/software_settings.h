#ifndef SELFDRIVE_UI_QT_OFFROAD_SOFTWARE_SETTINGS_H
#define SELFDRIVE_UI_QT_OFFROAD_SOFTWARE_SETTINGS_H

#include <QString>
#include <QWidget>
#include <QProcess> // Include QProcess for git commands

class QComboBox;
class QLabel;
class QPushButton;
// Forward declare new elements
class QCheckBox;
class QLineEdit;

#include "selfdrive/ui/qt/widgets/controls.hpp"
#include "selfdrive/ui/ui.hpp"

class SoftwarePanel : public ListWidget {
  Q_OBJECT
public:
  explicit SoftwarePanel(QWidget* parent = 0);

signals:
  void reviewTrainingGuide();
  void showDriverView();

private slots:
  void fetchBranches();
  void gitBranchesDone();
  void remoteChanged(int index);
  void onUpdatePressed();
  void updateLabels();
  void checkForUpdates();
  // New slots
  void manualRemoteToggled(int state);
  void manualRemoteEdited();


private:
  void showEvent(QShowEvent *event) override;
  void populateGitRemoteCombo();
  void populateGitBranches(); // Keep this, might need adjustment
  void get_branches(); // Existing helper for QProcess

  Params params;
  QLabel *onroadLbl;
  QComboBox *gitRemoteCombo;
  QComboBox *gitBranchCombo;
  QLabel *branchLbl;

  // New UI Elements
  QCheckBox *enableManualRemote;
  QLineEdit *manualRemoteInput;

  QPushButton *updateBtn;
  QPushButton *uninstallBtn;
  QPushButton *downloadBtn;
  QPushButton *targetBranchBtn;
  QLabel *commitLbl;
  QLabel *statusLbl;
  QString currentBranch;
  QString remoteName;
  QString trackingBranch;
  bool isTracking;
  QString localSHA;
  QString upstreamSHA;

  // Git process handling
  QProcess *git_process;
  bool git_fetching;
  bool is_onroad = false;
};

#endif // SELFDRIVE_UI_QT_OFFROAD_SOFTWARE_SETTINGS_H
