#include "selfdrive/ui/qt/offroad/software_settings.h"

#include <QDir>
#include <QProcess>
#include <QComboBox> // Added for QComboBox
#include <QLabel> // Added for QLabel
#include <QPushButton> // Added for QPushButton
#include <QCheckBox> // Added for QCheckBox
#include <QLineEdit> // Added for QLineEdit
#include <QMessageBox> // Added for QMessageBox
#include <QTimer> // Added for QTimer
#include <QFileSystemWatcher> // Added for QFileSystemWatcher


#include "selfdrive/common/params.h"
#include "selfdrive/common/swaglog.h"
#include "selfdrive/common/util.h"
#include "selfdrive/ui/qt/widgets/controls.hpp"
#include "selfdrive/ui/qt/widgets/input.hpp"
#include "selfdrive/ui/qt/widgets/offroad_alerts.hpp"
#include "selfdrive/ui/qt/widgets/scrollview.hpp"
#include "selfdrive/ui/ui.hpp"


SoftwarePanel::SoftwarePanel(QWidget* parent) : ListWidget(parent), git_fetching(false) {
  git_process = new QProcess(this);
  git_process->setProcessChannelMode(QProcess::MergedChannels);
  connect(git_process, static_cast<void (QProcess::*)(int, QProcess::ExitStatus)>(&QProcess::finished), this, &SoftwarePanel::gitBranchesDone);

  // ===== Update layout and add controls =====
  updateBtn = new QPushButton(tr("CHECK"));
  connect(updateBtn, &QPushButton::released, this, &SoftwarePanel::checkForUpdates);
  addItem(updateBtn);

  // Current branch label
  branchLbl = new QLabel();
  branchLbl->setStyleSheet("QLabel { font-size: 50px; }");
  addItem(branchLbl);

  // Enable Manual Git Remote Checkbox
  enableManualRemote = new QCheckBox(tr("Use Manual Git Remote?"));
  addItem(enableManualRemote);
  connect(enableManualRemote, &QCheckBox::stateChanged, this, &SoftwarePanel::manualRemoteToggled);

  // Manual Git Remote Input
  manualRemoteInput = new QLineEdit();
  manualRemoteInput->setPlaceholderText(tr("Enter Git Remote URL"));
  manualRemoteInput->setVisible(false); // Initially hidden
  manualRemoteInput->setEnabled(false); // Initially disabled
  addItem(manualRemoteInput);
  // Fetch branches when text is manually edited and user presses Enter or focus changes
  connect(manualRemoteInput, &QLineEdit::editingFinished, this, &SoftwarePanel::manualRemoteEdited); // Use editingFinished

  // Git Remote selector
  gitRemoteCombo = new QComboBox();
  gitRemoteCombo->setStyleSheet("QComboBox { font-size: 50px; }");
  addItem(gitRemoteCombo);
  connect(gitRemoteCombo, SIGNAL(activated(int)), this, SLOT(remoteChanged(int)));

  // Branch selector
  gitBranchCombo = new QComboBox();
  gitBranchCombo->setStyleSheet("QComboBox { font-size: 50px; }");
  addItem(gitBranchCombo);

  // Target branch button
  targetBranchBtn = new QPushButton();
  connect(targetBranchBtn, &QPushButton::released, [=]() {
    QString targetBranch = gitBranchCombo->currentText();
    QString currentActiveBranch = QString::fromStdString(params.get("GitBranch"));
    if (!targetBranch.isEmpty() && !targetBranch.contains("...") && targetBranch != currentActiveBranch) {
        // Use onUpdatePressed logic to save and potentially trigger update
        onUpdatePressed();
    }
  });
  addItem(targetBranchBtn);


  // ===== Installation layout =====
  downloadBtn = new QPushButton(tr("DOWNLOAD"));
  downloadBtn->setVisible(false);
  connect(downloadBtn, &QPushButton::released, [=]() {
    if (downloadBtn->isEnabled()) {
      downloadBtn->setEnabled(false);
      if (ConfirmationDialog::confirm(tr("Download Software?"), this)) {
        emit UIScene::getInstance()->requestDownload();
      } else {
        downloadBtn->setEnabled(true);
      }
    }
  });
  addItem(downloadBtn);

  uninstallBtn = new QPushButton(tr("UNINSTALL") + " " + QString::fromStdString(params.get("Brand")));
  uninstallBtn->setVisible(false);
  connect(uninstallBtn, &QPushButton::released, [=]() {
    if (uninstallBtn->isEnabled()) {
      uninstallBtn->setEnabled(false);
      QString brand = QString::fromStdString(params.get("Brand"));
      if (ConfirmationDialog::confirm(tr("Uninstall ") + brand + "?", this)) {
        params.putBool("DoUninstall", true);
      } else {
        uninstallBtn->setEnabled(true);
      }
    }
  });
  addItem(uninstallBtn);

  // ===== Miscellaneous layout =====
  commitLbl = new QLabel();
  commitLbl->setStyleSheet("QLabel { font-size: 35px; }");
  addItem(commitLbl);

  statusLbl = new QLabel();
  statusLbl->setStyleSheet("QLabel { font-size: 35px; }");
  addItem(statusLbl);

  auto *showTrainingBtn = new ButtonControl(tr("Review Training Guide"), tr("REVIEW"),
                                           tr("Review the rules, features, and limitations of openpilot"));
  connect(showTrainingBtn, &ButtonControl::clicked, [=]() { emit reviewTrainingGuide(); });
  addItem(showTrainingBtn);

  auto *showDriverViewBtn = new ButtonControl(tr("Driver Camera View"), tr("VIEW"),
                                            tr("Preview the driver facing camera to help optimize device mounting position for best driver monitoring experience. (vehicle must be off)"));
  connect(showDriverViewBtn, &ButtonControl::clicked, [=]() { emit showDriverView(); });
  addItem(showDriverViewBtn);

  onroadLbl = new QLabel(tr("openpilot requires the device to be mounted within 4° left or right and within 5° up or 9° down. openpilot is continuously calibrating, resetting requires re-calibration."));
  onroadLbl->setWordWrap(true);
  onroadLbl->setVisible(false);
  onroadLbl->setStyleSheet("QLabel { font-size: 40px; }");
  addItem(onroadLbl);

  auto *resetCalibBtn = new ButtonControl(tr("Reset Calibration"), tr("RESET"), tr(" "));
  connect(resetCalibBtn, &ButtonControl::clicked, [=]() {
    if (ConfirmationDialog::confirm(tr("Reset calibration?"), this)) {
      params.remove("CalibrationParams");
      params.remove("LiveTorqueParameters");
    }
  });
  addItem(resetCalibBtn);

  fs_watch = new QFileSystemWatcher(this);
  QObject::connect(fs_watch, &QFileSystemWatcher::fileChanged, [=](const QString path) {
    checkForUpdates();
  });

  // Initialize state
  updateLabels();
  populateGitRemoteCombo(); // Populate remotes first

  // Set initial state based on params after populating combos
  bool manual_mode = params.getBool("UseManualGitRemote");
  enableManualRemote->setChecked(manual_mode);
  manualRemoteToggled(manual_mode ? Qt::Checked : Qt::Unchecked); // Call slot to set initial UI state

  if (manual_mode) {
    manualRemoteInput->setText(QString::fromStdString(params.get("GitRemote")));
  } else {
     // Find and set the index for the stored remote
     QString currentRemote = QString::fromStdString(params.get("GitRemote"));
     int index = gitRemoteCombo->findData(currentRemote);
     if (index != -1) {
       gitRemoteCombo->setCurrentIndex(index);
     }
  }

  fetchBranches(); // Fetch branches based on initial state
}


void SoftwarePanel::showEvent(QShowEvent *event) {
  // Fetch updates on show
  checkForUpdates();

  // Update labels based on onroad status
  is_onroad = params.getBool("IsOnroad");
  onroadLbl->setVisible(is_onroad);
  updateBtn->setVisible(!is_onroad);
  uninstallBtn->setVisible(!is_onroad && params.getBool("IsInstalled"));
  downloadBtn->setVisible(!is_onroad && !params.getBool("IsInstalled"));

  ListWidget::showEvent(event);
}

void SoftwarePanel::checkForUpdates() {
  if (!this->isVisible()) {
    return;
  }

  updateLabels(); // Update labels before checking git status

  if (git_process->state() == QProcess::NotRunning) {
    fs_watch->addPath(QString::fromStdString(params.getParamPath("LastUpdateTime")));
    fs_watch->addPath(QString::fromStdString(params.getParamPath("UpdateAvailable")));
    git_process->start("git", {"fetch"}); // Simple fetch first to check for updates
  }
}

void SoftwarePanel::updateLabels() {
  // Current Branch
  currentBranch = QString::fromStdString(params.get("GitBranch"));
  branchLbl->setText(tr("Current Branch: ") + currentBranch);

  // Target Branch button text
  QString targetBranch = gitBranchCombo->currentText();
  QString currentActiveBranch = QString::fromStdString(params.get("GitBranch"));
  if (!targetBranch.isEmpty() && !targetBranch.contains("...") && targetBranch != currentActiveBranch) {
    targetBranchBtn->setText(tr("Switch to ") + targetBranch);
    targetBranchBtn->setEnabled(true);
  } else {
    targetBranchBtn->setText(targetBranch + tr(" (current)"));
    targetBranchBtn->setEnabled(false);
  }

  // Commit Label
  localSHA = QString::fromStdString(params.get("GitCommit").substr(0, 10));
  upstreamSHA = QString::fromStdString(params.get("GitCommitRemote").substr(0, 10));
  commitLbl->setText(tr("Local: ") + localSHA + " | " + tr("Remote: ") + upstreamSHA);


  // Update button text and status label
  QString lastUpdate = QString::fromStdString(params.get("LastUpdateTime"));
  bool updateAvailable = params.getBool("UpdateAvailable");

  if (git_process->state() == QProcess::Running && !git_fetching) { // Don't show checking if only fetching branches
    updateBtn->setText(tr("CHECKING"));
    updateBtn->setEnabled(false);
    statusLbl->setText(tr("Checking for updates..."));
  } else if (updateAvailable) {
    updateBtn->setText(tr("UPDATE"));
    updateBtn->setEnabled(true);
    statusLbl->setText(tr("Update available") + " (" + lastUpdate + ")");
  } else {
    updateBtn->setText(tr("CHECK"));
    updateBtn->setEnabled(true);
    statusLbl->setText(tr("Software up to date") + " (" + lastUpdate + ")");
  }
  updateBtn->setStyleSheet(updateAvailable ? "background-color: #465BEA;" : "");
}


void SoftwarePanel::populateGitRemoteCombo() {
    gitRemoteCombo->clear();
    // Add default comma remote
    gitRemoteCombo->addItem("commaai/openpilot", "https://github.com/commaai/openpilot.git");

    // Add user-defined remotes from params (if any)
    // Example: Reading from a param "GitRemotesList" which is a JSON string or similar
    // This part is kept simple as per requirements, not adding complex remote management
    // For now, only commaai remote is shown unless manual mode overrides.
}

void SoftwarePanel::remoteChanged(int index) {
    if (enableManualRemote->isChecked()) return; // Ignore if manual mode is on

    if (index >= 0) { // Ensure index is valid
        remoteName = gitRemoteCombo->itemData(index).toString();
        fetchBranches();
    }
}

void SoftwarePanel::manualRemoteToggled(int state) {
    bool manual_enabled = (state == Qt::Checked);
    manualRemoteInput->setVisible(manual_enabled);
    manualRemoteInput->setEnabled(manual_enabled);
    gitRemoteCombo->setEnabled(!manual_enabled);

    params.putBool("UseManualGitRemote", manual_enabled);

    if (manual_enabled) {
        // Clear combo selection visually
        gitRemoteCombo->setCurrentIndex(-1); // Visually deselect
        // Trigger branch fetch based on manual input field
        manualRemoteEdited();
    } else {
        // Restore remote selection from combo using the currently stored param
        QString currentRemoteUrl = QString::fromStdString(params.get("GitRemote", false)); // Don't block
        int index = gitRemoteCombo->findData(currentRemoteUrl);
         if (index != -1) {
             gitRemoteCombo->setCurrentIndex(index);
         } else {
             gitRemoteCombo->setCurrentIndex(0); // Default to commaai if previous not found
         }
        // Ensure remoteChanged is called to fetch branches for the selected combo item
        remoteChanged(gitRemoteCombo->currentIndex());
    }
    updateLabels(); // Update UI state
}

void SoftwarePanel::manualRemoteEdited() {
    if (enableManualRemote->isChecked()) {
        // Fetch branches based on the content of manualRemoteInput after user finishes editing
        fetchBranches();
    }
}


void SoftwarePanel::fetchBranches() {
  if (git_fetching || (git_process->state() == QProcess::Running && !git_fetching)) { // Allow fetch if another git process (not ls-remote) is running?
    return;
  }

  QString remote_url;
  if (enableManualRemote->isChecked()) {
    remote_url = manualRemoteInput->text().trimmed();
    if (remote_url.isEmpty() || !remote_url.startsWith("http")) { // Basic validation
        // Clear branches if URL is invalid/empty
        gitBranchCombo->clear();
        gitBranchCombo->addItem(tr("Invalid Remote URL"));
        gitBranchCombo->setEnabled(false);
        updateLabels(); // Update target branch button state
        return; // Don't run git command
    }
     // Use the URL directly for ls-remote
     remoteName = remote_url;
  } else {
    if (gitRemoteCombo->currentIndex() < 0) { // No remote selected
        gitBranchCombo->clear();
        gitBranchCombo->addItem(tr("Select Remote"));
        gitBranchCombo->setEnabled(false);
        updateLabels();
        return;
    }
    remoteName = gitRemoteCombo->currentData().toString();
    remote_url = remoteName; // Use the URL stored in itemData
  }


  LOGD("Fetching branches for remote: %s", remote_url.toStdString().c_str());

  git_fetching = true;
  gitBranchCombo->clear();
  gitBranchCombo->addItem(tr("Fetching branches..."));
  gitBranchCombo->setEnabled(false);
  updateLabels(); // Update target branch button state

  // Use ls-remote to get branches without adding a remote locally
  git_process->start("git", {"ls-remote", "--heads", remote_url});
}

void SoftwarePanel::gitBranchesDone() {
  if (!git_fetching) {
    // This was likely the initial 'git fetch' for checking updates, not ls-remote
    updateLabels(); // Refresh status labels after fetch completes
    return;
  }

  git_fetching = false;
  gitBranchCombo->clear();

  QString output = git_process->readAllStandardOutput();
  int exitCode = git_process->exitCode();

  LOGD("ls-remote exit code: %d", exitCode);
  // LOGD("ls-remote output: %s", output.toStdString().c_str()); // Output can be long


  if (exitCode == 0) {
      QStringList branches;
      for (QString line : output.split('
')) {
          QStringList parts = line.split("refs/heads/");
          if (parts.size() == 2 && !parts[1].isEmpty()) {
              branches << parts[1];
          }
      }
      std::sort(branches.begin(), branches.end());

      if (branches.isEmpty()) {
          gitBranchCombo->addItem(tr("No branches found"));
          gitBranchCombo->setEnabled(false);
          if (enableManualRemote->isChecked()) {
              QMessageBox::warning(this, tr("Fetch Error"), tr("Could not fetch branches for the entered remote URL. Check the URL and network connection."));
          }
      } else {
          gitBranchCombo->addItems(branches);
          gitBranchCombo->setEnabled(true);

          // Try to set the current branch as active in the combo
          QString currentActiveBranch = QString::fromStdString(params.get("GitBranch"));
          int index = gitBranchCombo->findText(currentActiveBranch);
          if (index != -1) {
              gitBranchCombo->setCurrentIndex(index);
          }
      }
  } else {
      gitBranchCombo->addItem(tr("Error fetching branches"));
      gitBranchCombo->setEnabled(false);
       if (enableManualRemote->isChecked()) {
           QMessageBox::warning(this, tr("Fetch Error"), tr("Failed to fetch branches from manual remote. Check URL and network. Error: %1").arg(output.left(100))); // Show partial error
       }
  }

  updateLabels(); // Update commit labels and button states
}

void SoftwarePanel::onUpdatePressed() {
  // Get remote and branch to save based on mode
  QString targetRemote;
  if (enableManualRemote->isChecked()) {
      targetRemote = manualRemoteInput->text().trimmed();
      if (targetRemote.isEmpty() || !targetRemote.startsWith("http")) { // Basic validation
            QMessageBox::warning(this, tr("Update Error"), tr("Manual remote URL is invalid. Cannot update."));
            return;
      }
  } else {
      if (gitRemoteCombo->currentIndex() < 0) {
           QMessageBox::warning(this, tr("Update Error"), tr("No Git remote selected. Cannot update."));
           return;
      }
      targetRemote = gitRemoteCombo->currentData().toString();
  }

  QString targetBranch = gitBranchCombo->currentText();
   if (targetBranch.isEmpty() || targetBranch.contains("...")) {
        QMessageBox::warning(this, tr("Update Error"), tr("No Git branch selected or still fetching. Cannot update."));
        return;
   }


  // Save the selected/manual remote and branch to params
  params.put("GitRemote", targetRemote.toStdString());
  params.put("GitBranch", targetBranch.toStdString());
  LOGD("Set GitRemote=%s, GitBranch=%s", targetRemote.toStdString().c_str(), targetBranch.toStdString().c_str());


  // Trigger the existing update mechanism
  // Check if an update is actually available or if this is just a branch switch
  bool updateIsAvailable = params.getBool("UpdateAvailable");
  QString currentActiveBranch = QString::fromStdString(params.get("GitBranch", false)); // Read param back just in case

  if (updateIsAvailable || targetBranch != currentActiveBranch) {
      if (ConfirmationDialog::confirm(tr("Confirm Update/Switch"), this)) {
          // Initiate download/update via existing mechanism
          statusLbl->setText(tr("Update initiated..."));
          updateBtn->setEnabled(false);
          emit UIScene::getInstance()->requestUpdate();
      } else {
          // User cancelled, maybe revert params? Or just leave them for next time?
          // For now, leave params set, user can change again.
      }
  } else {
      // Branch is the same and no update available, treat as "CHECK"
      checkForUpdates();
  }
}

