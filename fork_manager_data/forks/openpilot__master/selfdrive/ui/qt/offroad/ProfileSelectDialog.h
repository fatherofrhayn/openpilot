#pragma once

#include <QDialog>
#include <QListWidget>
#include <QPushButton>
#include <QVBoxLayout>
#include <QStringList>

class ProfileSelectDialog : public QDialog {
  Q_OBJECT

public:
  explicit ProfileSelectDialog(const QStringList &profiles, const QString &currentProfile, QWidget *parent = nullptr);

  QString selectedProfile() const;

signals:
  void createProfileRequested();
  void editProfileRequested(const QString &profile);
  void deleteProfileRequested(const QString &profile);

private slots:
  void onProfileActivated(QListWidgetItem *item);
  void onCreateClicked();
  void onEditClicked();
  void onDeleteClicked();

private:
  QListWidget *profileList;
  QPushButton *createBtn;
  QPushButton *editBtn;
  QPushButton *deleteBtn;
  QString selected;
};
