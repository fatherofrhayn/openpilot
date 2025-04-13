#include "InstallForkDialog.h"
#include <QHBoxLayout>
#include <QLabel>

InstallForkDialog::InstallForkDialog(QWidget *parent)
    : QDialog(parent), url(""), branch("") {
  setWindowTitle("Install New Fork");
  setModal(true);
  QVBoxLayout *mainLayout = new QVBoxLayout(this);

  QLabel *urlLabel = new QLabel("Git URL:", this);
  urlEdit = new QLineEdit(this);
  mainLayout->addWidget(urlLabel);
  mainLayout->addWidget(urlEdit);

  QLabel *branchLabel = new QLabel("Branch:", this);
  branchEdit = new QLineEdit(this);
  mainLayout->addWidget(branchLabel);
  mainLayout->addWidget(branchEdit);

  installBtn = new QPushButton("Install", this);
  mainLayout->addWidget(installBtn);

  connect(installBtn, &QPushButton::clicked, this, &InstallForkDialog::onInstallClicked);
}

QString InstallForkDialog::gitUrl() const {
  return url;
}

QString InstallForkDialog::branch() const {
  return branch;
}

void InstallForkDialog::onInstallClicked() {
  url = urlEdit->text().trimmed();
  branch = branchEdit->text().trimmed();
  if (url.isEmpty() || branch.isEmpty()) {
    // Optionally show an error message
    return;
  }
  accept();
}
