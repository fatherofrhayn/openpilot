#include "InstallForkDialog.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QMessageBox>

InstallForkDialog::InstallForkDialog(QWidget *parent)
    : QDialog(parent), urlStr(""), branchStr("") {
  setWindowTitle("Install New Fork");
  setModal(true);
  QVBoxLayout *mainLayout = new QVBoxLayout(this);

  QLabel *urlLabel = new QLabel("Git URL:", this);
  urlEdit = new QLineEdit(this);
  urlEdit->setPlaceholderText(tr("e.g. https://github.com/commaai/openpilot.git"));
  mainLayout->addWidget(urlLabel);
  mainLayout->addWidget(urlEdit);

  QLabel *branchLabel = new QLabel("Branch:", this);
  branchEdit = new QLineEdit(this);
  branchEdit->setPlaceholderText(tr("branch (e.g. master)"));
  mainLayout->addWidget(branchLabel);
  mainLayout->addWidget(branchEdit);

  installBtn = new QPushButton("Install", this);
  mainLayout->addWidget(installBtn);

  connect(installBtn, &QPushButton::clicked, this, &InstallForkDialog::onInstallClicked);
}

QString InstallForkDialog::gitUrl() const {
  return urlStr;
}

QString InstallForkDialog::branch() const {
  return branchStr;
}

void InstallForkDialog::onInstallClicked() {
  urlStr = urlEdit->text().trimmed();
  branchStr = branchEdit->text().trimmed();
  if (urlStr.isEmpty() || branchStr.isEmpty()) {
    QMessageBox::warning(this, tr("Invalid Input"), tr("Both Git URL and branch must be provided."));
    return;
  }
  accept();
}
