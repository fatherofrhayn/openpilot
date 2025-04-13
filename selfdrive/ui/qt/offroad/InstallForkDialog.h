#pragma once

#include <QDialog>
#include <QLineEdit>
#include <QPushButton>
#include <QVBoxLayout>
#include <QString>

class InstallForkDialog : public QDialog {
  Q_OBJECT

public:
  explicit InstallForkDialog(QWidget *parent = nullptr);

  QString gitUrl() const;
  QString branch() const;

private slots:
  void onInstallClicked();

private:
  QLineEdit *urlEdit;
  QLineEdit *branchEdit;
  QPushButton *installBtn;
  QString url;
  QString branch;
};
