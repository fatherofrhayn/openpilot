// SoftwareManagerPanel.cc
// Implements the UI panel for software updates, profile management, forks list, settings, and logs.

#include "selfdrive/ui/qt/offroad/SoftwareManagerPanel.h"
#include "selfdrive/ui/qt/offroad/SoftwareManager.h"
#include "selfdrive/ui/qt/widgets/controls.h"
#include "common/params.h"
#include <QVBoxLayout>
#include <QCoreApplication>
#include <QHBoxLayout>
#include <QGridLayout>
#include <QMessageBox>
#include <QDesktopServices>
#include <QUrl>
#include <QLayoutItem>
#include <QLabel>
#include <QProcess>
#include <QDebug>
#include <QSizePolicy>
#include <QInputDialog>
#include <QLineEdit>
#include <QSize>
#include <QDir>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonValue>
#include <QJsonObject>
#include "selfdrive/ui/qt/offroad/PathConfig.h"
#include "selfdrive/ui/qt/offroad/InstallForkDialog.h"
#include "selfdrive/ui/qt/offroad/SoftwareManagerUtils.h"
#include <QFrame>
#include <QCoreApplication>

/**
 * Constructor: initialize UI elements, layouts, and connect SoftwareManager signals.
 * Triggers initial listing of profiles.
 */
SoftwareManagerPanel::SoftwareManagerPanel(QWidget *parent) : ListWidget(parent) {
  qDebug() << "SoftwareManagerPanel constructor entered";
  qDebug() << "SoftwareManagerPanel ctor start";
  // Debug: show CLI binary path and error if missing
  QString cliPath = PathConfig::instance().cliBinary();
  qDebug() << "SoftwareManagerPanel: using CLI binary at:" << cliPath;
  if (cliPath.isEmpty()) {
    QMessageBox::critical(this, tr("Error"), tr("Fork Manager CLI not found. Please build or set FORK_MANAGER_CLI_PATH.\nExpected at: %1").arg(cliPath));
  }
  this->setContentsMargins(16, 16, 16, 16);
  // Initialize UI elements
  profileCombo = new QComboBox(this);
  const int profileBtnWidth = 155;
  selectProfileBtn = new ButtonControl(QString(), tr("Select"), "", this, profileBtnWidth);
  createProfileBtn = new ButtonControl(QString(), tr("Create"), "", this, profileBtnWidth);
  editProfileBtn = new ButtonControl(QString(), tr("Edit"), "", this, profileBtnWidth);
  deleteProfileBtn = new ButtonControl(QString(), tr("Delete"), "", this, profileBtnWidth);
  selfUpdateToggle = new ParamControl("SoftwareManager.SelfUpdateEnabled", tr("Self Update"), tr(""), "");
  autoBackupToggle = new ParamControl("SoftwareManager.AutoBackupEnabled", tr("Auto Backup"), tr(""), "");
  advancedLogsToggle = new ParamControl("SoftwareManager.ShowAdvancedLogs", tr("Advanced Logs"), tr(""), "");
  historyLimitSpin = new QSpinBox(this);
  historyLimitSpin->setRange(0, 100);
  historyLimitSpin->setValue(QString::fromStdString(Params().get("SoftwareManager.BackupHistoryLimit")).toInt());
  logView = new QTextEdit(this);
  logView->setReadOnly(true);
  // Ensure log area shows at least thirty lines
  logView->setMinimumHeight(logView->fontMetrics().lineSpacing() * 30);
  logView->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
  clearLogBtn = new ButtonControl(tr("Clear Log"), tr("Clear"));
  helpBtn = new ButtonControl(tr("Help"), tr("Help"));
  aboutBtn = new ButtonControl(tr("About"), tr("About"));
  // Utility buttons: manual update check and disk usage
  checkUpdateBtn = new ButtonControl(tr("Check Updates"), tr("Check Updates"));
  diskUsageBtn = new ButtonControl(tr("Disk Usage"), tr("Disk Usage"));

  manager_ = new SoftwareManager(this);
  // Manager signal connections (best-practice slots)
  connect(manager_, &SoftwareManager::updateStarted, this, &SoftwareManagerPanel::onManagerUpdateStarted);
  connect(manager_, &SoftwareManager::updateProgress, this, &SoftwareManagerPanel::onManagerUpdateProgress);
  connect(manager_, &SoftwareManager::updateFinished, this, &SoftwareManagerPanel::onManagerUpdateFinished);
  connect(manager_, &SoftwareManager::profilesListed, this, &SoftwareManagerPanel::onManagerProfilesListed);
  connect(manager_, &SoftwareManager::forksListed, this, &SoftwareManagerPanel::onManagerForksListed);
  connect(manager_, &SoftwareManager::cliOutput, this, &SoftwareManagerPanel::onManagerCliOutput);

  // Title
  QLabel *headerLbl = new QLabel(tr("Fork Manager"), this);
  headerLbl->setAlignment(Qt::AlignHCenter);
  addItem(headerLbl);

  // 1. Status row
  statusLabel = new LabelControl(tr("Status:"), tr("Offroad"));
  forkLabel = new LabelControl(tr("Current Fork:"), tr("N/A"));
  QHBoxLayout *statusLayout = new QHBoxLayout();
  statusLayout->addWidget(statusLabel);
  statusLayout->addStretch(1);
  statusLayout->addWidget(forkLabel);
  {
    QWidget *statusContainer = new QWidget(this);
    statusContainer->setLayout(statusLayout);
    statusContainer->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Preferred);
    addItem(statusContainer);
  }

  // 2. (Removed update controls)

  // 3. Profile management row: active profile label and Select/Create/Edit/Delete buttons
  QHBoxLayout *profileLayout = new QHBoxLayout();
  profileLayout->setContentsMargins(0, 0, 0, 0);
  profileLayout->setSpacing(1);
  QLabel *profileLabel = new QLabel(tr("Active Profile:"), this);
  profileLayout->addWidget(profileLabel);
  profileLayout->addWidget(profileCombo, 1);
  profileLayout->addWidget(selectProfileBtn);
  profileLayout->addWidget(createProfileBtn);
  profileLayout->addWidget(editProfileBtn);
  profileLayout->addWidget(deleteProfileBtn);
  {
    QWidget *profileContainer = new QWidget(this);
    profileContainer->setLayout(profileLayout);
    addItem(profileContainer);
  }
  QFrame *sepProfile = new QFrame(this);
  sepProfile->setFrameShape(QFrame::HLine);
  sepProfile->setFrameShadow(QFrame::Sunken);
  addItem(sepProfile);
  // Select button handler: activate the chosen profile
  connect(selectProfileBtn, &ButtonControl::clicked, [=]() { onTriggerClicked(UpdateType::PROFILE_ACTIVATE, profileCombo->currentText()); });
  // Handler: create new profile via external CLI tool
  connect(createProfileBtn, &ButtonControl::clicked, [=]() {
    bool ok;
    // Prompt for profile name
    QString name = QInputDialog::getText(this, tr("Create Profile"), tr("Profile name:"), QLineEdit::Normal, QString(), &ok);
    if (!ok || name.trimmed().isEmpty()) return;
    // Prompt to select one of the installed forks
    if (lastForkEntries.isEmpty()) {
      QMessageBox::warning(this, tr("Error"), tr("No installed forks available"));
      return;
    }
    QString selected = QInputDialog::getItem(this, tr("Create Profile"), tr("Select fork:"), lastForkEntries, 0, false, &ok);
    if (!ok || selected.isEmpty()) return;
    // Parse fork and branch
    QString fork;
    QString branch;
    int idx = selected.indexOf("__");
    if (idx != -1) {
      fork = selected.left(idx);
      branch = selected.mid(idx + 2);
    } else {
      int sp = selected.indexOf(' ');
      if (sp != -1) {
        fork = selected.left(sp);
        branch = selected.mid(sp + 1);
      } else {
        fork = selected;
      }
    }
    // Start external process to create profile
    auto *p = new QProcess(this);
    p->start(cliPath, {"create-profile", name, fork, branch});
    connect(p, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished), this, [=](int exitCode, QProcess::ExitStatus status) {
      // Refresh profiles on success, warn on failure
      if (status == QProcess::NormalExit && exitCode == 0) {
        manager_->triggerUpdate(UpdateType::LIST_PROFILES);
      } else {
        QMessageBox::warning(this, tr("Error"), tr("Failed to create profile"));
      }
      p->deleteLater();
    });
  });
  // Handler: rename selected profile via CLI tool
  connect(editProfileBtn, &ButtonControl::clicked, [=]() {
    // Get currently selected profile
    QString oldName = profileCombo->currentText();
    if (oldName.isEmpty()) return;
    // Prompt for a new profile name
    bool ok;
    QString newName = QInputDialog::getText(this, tr("Rename Profile"), tr("New profile name:"), QLineEdit::Normal, oldName, &ok);
    if (!ok || newName.isEmpty() || newName == oldName) return;
    // Start external process to rename profile
    auto *p = new QProcess(this);
    p->start(cliPath, {"rename-profile", oldName, newName});
    connect(p, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished), this, [=](int exitCode, QProcess::ExitStatus status) {
      // Refresh profiles on success, warn on failure
      if (status == QProcess::NormalExit && exitCode == 0) {
        manager_->triggerUpdate(UpdateType::LIST_PROFILES);
      } else {
        QMessageBox::warning(this, tr("Error"), tr("Failed to rename profile"));
      }
      p->deleteLater();
    });
  });
  // Handler: delete selected profile via CLI tool
  connect(deleteProfileBtn, &ButtonControl::clicked, [=]() {
    // Confirm deletion of the selected profile
    QString name = profileCombo->currentText();
    if (name.isEmpty()) return;
    if (QMessageBox::question(this, tr("Delete Profile"), tr("Delete profile '%1'?").arg(name), QMessageBox::Yes | QMessageBox::No) != QMessageBox::Yes) return;
    // Start external process to delete profile
    auto *p = new QProcess(this);
    p->start(cliPath, {"delete-profile", name});
    connect(p, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished), this, [=](int exitCode, QProcess::ExitStatus status) {
      // Refresh profiles on success, warn on failure
      if (status == QProcess::NormalExit && exitCode == 0) {
        manager_->triggerUpdate(UpdateType::LIST_PROFILES);
      } else {
        QMessageBox::warning(this, tr("Error"), tr("Failed to delete profile"));
      }
      p->deleteLater();
    });
  });

  // 4. Installed forks header: display title and 'Install New Fork' button
  newForkBtn = new ButtonControl(QString(), tr("Install New Fork"), "", this, 300);
  connect(newForkBtn, &ButtonControl::clicked, [=]() {
    if (PathConfig::instance().cliBinary().isEmpty()) {
      QMessageBox::critical(this, tr("Error"), tr("The fork_manager CLI is missing. Please place it next to the UI binary or set FORK_MANAGER_CLI_PATH."));
      return;
    }
    InstallForkDialog dlg(this);
    if (dlg.exec() == QDialog::Accepted) {
      QString url = dlg.gitUrl();
      QString branch = dlg.branch();
      // Prevent duplicate installs
      QUrl gitUrlObj(url);
      QString repoName = QFileInfo(gitUrlObj.path()).baseName();
      QString entry = repoName + "__" + branch;
      QString forkDir = PathConfig::instance().forksDir() + "/" + entry;
      if (QDir(forkDir).exists()) {
        QMessageBox::warning(this, tr("Error"), tr("Fork '%1' already exists.").arg(entry));
        return;
      }
      onTriggerClicked(UpdateType::INSTALL, url + "::" + branch);
    }
  });
  QHBoxLayout *forksHeaderLayout = new QHBoxLayout();
  forksHeaderLayout->addWidget(new QLabel(tr("Installed Forks:")));
  forksHeaderLayout->addStretch(1);
  forksHeaderLayout->addWidget(newForkBtn);
  // Add Refresh Forks button
  ButtonControl *refreshForksBtn = new ButtonControl(QString(), tr("Refresh Forks"), "", this, 140);
  forksHeaderLayout->addWidget(refreshForksBtn);
  connect(refreshForksBtn, &ButtonControl::clicked, [=]() {
    logView->append(tr("Refreshing forks list..."));
    manager_->triggerUpdate(UpdateType::LIST_FORKS);
  });
  QWidget *forksHeaderContainer = new QWidget(this);
  forksHeaderContainer->setLayout(forksHeaderLayout);
  forksHeaderContainer->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Preferred);
  addItem(forksHeaderContainer);
  QFrame *sepHeader = new QFrame(this);
  sepHeader->setFrameShape(QFrame::HLine);
  sepHeader->setFrameShadow(QFrame::Sunken);
  addItem(sepHeader);

  // 5. Installed forks list container: dynamic height, no nested scroll
  forksListWidget = new QWidget(this);
  forksListLayout = new QVBoxLayout(forksListWidget);
  forksListLayout->setContentsMargins(8, 8, 8, 8);
  forksListLayout->setSpacing(8);
  forksListWidget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::MinimumExpanding);
  // Ensure forks area shows at least six lines
  forksListWidget->setMinimumHeight(forksListWidget->fontMetrics().lineSpacing() * 6);
  addItem(forksListWidget);

  // 6. Settings toggles: self-update, auto-backup, advanced logs, and backup history limit
  QGridLayout *settingsLayout = new QGridLayout();
  settingsLayout->addWidget(selfUpdateToggle, 0, 0);
  settingsLayout->addWidget(autoBackupToggle, 0, 1);
  settingsLayout->addWidget(advancedLogsToggle, 1, 0);
  settingsLayout->addWidget(historyLimitSpin, 1, 1);
  settingsLayout->addWidget(checkUpdateBtn, 2, 0);
  settingsLayout->addWidget(diskUsageBtn, 2, 1);
  {
    QWidget *settingsContainer = new QWidget(this);
    settingsContainer->setLayout(settingsLayout);
    addItem(settingsContainer);
  }
  connect(historyLimitSpin, QOverload<int>::of(&QSpinBox::valueChanged), [=](int v) { Params().put("SoftwareManager.BackupHistoryLimit", std::to_string(v)); });
  connect(checkUpdateBtn, &ButtonControl::clicked, [=]() { logView->append(tr("Checking for updates...")); manager_->triggerUpdate(UpdateType::CHECK); });
  connect(diskUsageBtn, &ButtonControl::clicked, [=]() { logView->append(tr("Retrieving disk usage...")); manager_->triggerUpdate(UpdateType::DISK_USAGE); });

  // 7. Log area: clear log button and log display widget
  QHBoxLayout *logHeaderLayout = new QHBoxLayout();
  logHeaderLayout->addWidget(clearLogBtn);
  {
    QWidget *logHeaderContainer = new QWidget(this);
    logHeaderContainer->setLayout(logHeaderLayout);
    addItem(logHeaderContainer);
  }
  addItem(logView);
  connect(clearLogBtn, &ButtonControl::clicked, [=]() { logView->clear(); });

  // 8. Footer: Help and About buttons
  QHBoxLayout *footerLayout = new QHBoxLayout();
  footerLayout->addWidget(helpBtn);
  footerLayout->addWidget(aboutBtn);
  {
    QWidget *footerContainer = new QWidget(this);
    footerContainer->setLayout(footerLayout);
    addItem(footerContainer);
  }

  // Initial listings
  manager_->triggerUpdate(UpdateType::LIST_PROFILES);
  qDebug() << "SoftwareManagerPanel ctor end";
  // End of UI setup


}

/**
 * Slot invoked by UI controls to initiate a SoftwareManager operation.
 * @param type Operation type to perform.
 * @param ref  Optional reference string (profile name or fork entry).
 */
void SoftwareManagerPanel::onTriggerClicked(UpdateType type, const QString &ref) {
  manager_->triggerUpdate(type, ref);
}

/**
 * Open the help documentation in the default browser.
 */
void SoftwareManagerPanel::onHelpClicked() {
  QDesktopServices::openUrl(QUrl("https://docs.comma.ai/openpilot-software-manager", QUrl::TolerantMode));
}

/**
 * Display the About dialog with software version information.
 */
void SoftwareManagerPanel::onAboutClicked() {
  QMessageBox::about(this, tr("About"), tr("Software Manager v1.0"));
}

/**
 * Slot to receive CLI output and append to log
 */
void SoftwareManagerPanel::onManagerCliOutput(const QString &output) {
  logView->append(output);
}

/**
 * Slot called when a SoftwareManager update starts.
 * Updates the status label based on the operation type.
 */
void SoftwareManagerPanel::onManagerUpdateStarted(UpdateType type) {
  // Update status text based on operation
  switch (type) {
    case UpdateType::CHECK:           statusLabel->setText(tr("Checking…")); break;
    case UpdateType::DOWNLOAD:        statusLabel->setText(tr("Downloading…")); break;
    case UpdateType::INSTALL:         statusLabel->setText(tr("Installing…")); break;
    case UpdateType::UNINSTALL:       statusLabel->setText(tr("Uninstalling…")); break;
    case UpdateType::FORK_SWAP:       statusLabel->setText(tr("Switching Fork…")); break;
    case UpdateType::FORK_UPDATE:     statusLabel->setText(tr("Updating Fork…")); break;
    case UpdateType::FORK_CLEANUP:    statusLabel->setText(tr("Deleting Fork…")); break;
    case UpdateType::FORK_UNDO:       statusLabel->setText(tr("Undoing Fork…")); break;
    case UpdateType::SELF_UPDATE:     statusLabel->setText(tr("Self Updating…")); break;
    case UpdateType::PROFILE_ACTIVATE:statusLabel->setText(tr("Activating Profile…")); break;
    case UpdateType::BACKUP:          statusLabel->setText(tr("Backup…")); break;
    default: break;
  }
  emit updateStarted(type);
}

/**
 * Slot called when a SoftwareManager update finishes.
 * Resets the status label or shows an error.
 * @param type    Operation type that completed.
 * @param success Whether the operation succeeded.
 */
void SoftwareManagerPanel::onManagerUpdateFinished(UpdateType type, bool success) {
  // Revert to Idle or show error
  if (success) {
    statusLabel->setText(tr("Offroad"));
    // Auto-refresh lists after operations
    if (type == UpdateType::INSTALL || type == UpdateType::FORK_UPDATE || type == UpdateType::FORK_CLEANUP) {
      manager_->triggerUpdate(UpdateType::LIST_FORKS);
    } else if (type == UpdateType::PROFILE_ACTIVATE) {
      // Refresh profiles after activation
      manager_->triggerUpdate(UpdateType::LIST_PROFILES);
    }
  } else {
    statusLabel->setText(tr("Error"));
  }
  emit updateFinished(type, success);
}

/**
 * Slot called on progress updates.
 * @param progress Completion percentage (0-100).
 */
void SoftwareManagerPanel::onManagerUpdateProgress(int progress) {
  emit updateProgress(progress);
}

/**
 * Slot called when profiles have been listed by SoftwareManager.
 * Populates the profile combo box and triggers forks listing.
 * @param profiles List of available profile names.
 */
void SoftwareManagerPanel::onManagerProfilesListed(const QStringList &profiles) {
  qDebug() << "onManagerProfilesListed:" << profiles;
  profileCombo->clear();
  profileCombo->addItems(profiles);
  // Enable/disable profile buttons
  bool hasProfiles = !profiles.isEmpty();
  selectProfileBtn->setEnabled(hasProfiles);
  editProfileBtn->setEnabled(hasProfiles);
  deleteProfileBtn->setEnabled(hasProfiles);
  // After loading profiles, list forks
  manager_->triggerUpdate(UpdateType::LIST_FORKS);
}

/**
 * Slot invoked when SoftwareManager has listed installed forks.
 * Clears existing entries and populates the forksListLayout with Drive/Update/Delete controls.
 */
void SoftwareManagerPanel::onManagerForksListed(const QStringList &forks) {
  qDebug() << "onManagerForksListed slot entered";
  qDebug() << "Forks from CLI:" << forks;
  qDebug() << "Forks from CLI:" << forks;
  // Parse raw CLI output lines into normalized entries
  QStringList entries = SoftwareManagerUtils::parseForkLines(forks);
  // Update last fork entries for profile creation
  lastForkEntries = entries;
  // Enable/disable Create Profile based on installed forks
  createProfileBtn->setEnabled(!entries.isEmpty());
  qDebug() << "Parsed fork entries:" << entries;
  // Clear existing fork entries before repopulating the list
  // clear previous items
  QLayoutItem *child;
  while ((child = forksListLayout->takeAt(0)) != nullptr) {
    delete child->widget();
    delete child;
  }
  // Show placeholder when no forks installed
  if (entries.isEmpty()) {
    QLabel *noneLbl = new QLabel(tr("No installed forks"), this);
    noneLbl->setAlignment(Qt::AlignCenter);
    forksListLayout->addWidget(noneLbl);
  }
  // Determine the currently active fork from openpilot_symlink
  QString activeForkPath = QString::fromStdString(QFileInfo("openpilot_symlink").symLinkTarget().toStdString());
  QString activeForkEntry;
  if (activeForkPath.startsWith(PathConfig::instance().forksDir())) {
    QString baseName = QFileInfo(activeForkPath).baseName();
    activeForkEntry = baseName;
    // If not already in the entries, prepend it
    if (!entries.contains(activeForkEntry)) {
      entries.prepend(activeForkEntry);
    }
  }
  // Iterate through fork entries and create UI rows
  for (const QString &f : entries) {
    // Parse entry string into fork name and branch
    QString forkName, branchName;
    int idx2 = f.indexOf("__");
    if (idx2 >= 0) {
      forkName = f.left(idx2);
      branchName = f.mid(idx2 + 2);
    } else {
      int sp2 = f.indexOf(' ');
      if (sp2 >= 0) {
        forkName = f.left(sp2);
        branchName = f.mid(sp2 + 1);
      } else {
        forkName = f;
      }
    }
    // Create a horizontal layout for this fork row
    QHBoxLayout *rowLayout = new QHBoxLayout();
    rowLayout->setContentsMargins(8, 4, 8, 4);
    rowLayout->setSpacing(8);
    // Add labels for fork name and branch
    QLabel *forkNameLabel = new QLabel(forkName, this);
    if (f == activeForkEntry) {
      forkNameLabel->setText(forkNameLabel->text() + "  [active]");
      forkNameLabel->setStyleSheet("font-weight: bold; color: #4CAF50;");
    }
    rowLayout->addWidget(forkNameLabel);
    if (!branchName.isEmpty()) {
      rowLayout->addWidget(new QLabel(branchName, this));
    }
    // Drive button: switch to this fork
    ButtonControl *driveBtn = new ButtonControl(QString(), tr("Drive"), "", this, 200);
    driveBtn->setStyleSheet("background-color: #4CAF50; color: white;");
    connect(driveBtn, &ButtonControl::clicked, [=]() { onTriggerClicked(UpdateType::FORK_SWAP, f); }); rowLayout->addWidget(driveBtn);
    // Update button: pull latest changes for this fork
    ButtonControl *updateBtn = new ButtonControl(QString(), tr("Update"), "", this, 200);
    updateBtn->setStyleSheet("background-color: #2196F3; color: white;");
    connect(updateBtn, &ButtonControl::clicked, [=]() { onTriggerClicked(UpdateType::FORK_UPDATE, f); }); rowLayout->addWidget(updateBtn);
    // Delete button: remove this fork installation
    ButtonControl *delBtn = new ButtonControl(QString(), tr("Delete"), "", this, 200);
    delBtn->setStyleSheet("background-color: #F44336; color: white;");
    connect(delBtn, &ButtonControl::clicked, [=]() { onTriggerClicked(UpdateType::FORK_CLEANUP, f); }); rowLayout->addWidget(delBtn);
    // Wrap layout in a widget and add to the list container
    QWidget *rowWidget = new QWidget(this);
    rowWidget->setLayout(rowLayout);
    forksListLayout->addWidget(rowWidget);
  }
  // Auto-size container to include all rows, margins, and spacing
  forksListWidget->setMinimumHeight(forksListWidget->sizeHint().height() * 6);
}

QStringList lastForkEntries;
