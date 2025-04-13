#include "ForkManagerPanel.h"
#include "ProfileSelectDialog.h"
#include "InstallForkDialog.h"
#include <QMessageBox>
#include <QTimer>
#include <QDebug>
#include <QRegularExpression>

// ... (existing constructor code) ...

// Add this in ForkManagerPanel constructor after creating the forks area:
installForkBtn = new QPushButton("Install New Fork", this);
mainLayout->addWidget(installForkBtn);
connect(installForkBtn, &QPushButton::clicked, this, &ForkManagerPanel::onInstallForkClicked);

// ... (rest of constructor code) ...

void ForkManagerPanel::onInstallForkClicked() {
  InstallForkDialog dlg(this);
  if (dlg.exec() == QDialog::Accepted) {
    QString url = dlg.gitUrl();
    QString branch = dlg.branch();
    if (!url.isEmpty() && !branch.isEmpty()) {
      runCliCommand(QString("install %1 %2").arg(url, branch));
    }
  }
}

// ... (rest of ForkManagerPanel methods unchanged) ...
