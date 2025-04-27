#include "ProfileSelectDialog.h"
#include <QHBoxLayout>
#include <QLabel>
#include <QListWidgetItem>

ProfileSelectDialog::ProfileSelectDialog(const QStringList &profiles, const QString &currentProfile, QWidget *parent)
    : QDialog(parent), selected(currentProfile) {
  setWindowTitle("Select Profile");
  setModal(true);
  QVBoxLayout *mainLayout = new QVBoxLayout(this);

  QLabel *label = new QLabel("Select a profile to activate:", this);
  mainLayout->addWidget(label);

  profileList = new QListWidget(this);
  for (const QString &profile : profiles) {
    QListWidgetItem *item = new QListWidgetItem(profile, profileList);
    if (profile == currentProfile) {
      item->setSelected(true);
      item->setBackground(Qt::lightGray);
    }
  }
  mainLayout->addWidget(profileList);

  QHBoxLayout *btnLayout = new QHBoxLayout();
  createBtn = new QPushButton("Create", this);
  editBtn = new QPushButton("Edit", this);
  deleteBtn = new QPushButton("Delete", this);
  btnLayout->addWidget(createBtn);
  btnLayout->addWidget(editBtn);
  btnLayout->addWidget(deleteBtn);
  mainLayout->addLayout(btnLayout);

  connect(profileList, &QListWidget::itemDoubleClicked, this, &ProfileSelectDialog::onProfileActivated);
  connect(createBtn, &QPushButton::clicked, this, &ProfileSelectDialog::onCreateClicked);
  connect(editBtn, &QPushButton::clicked, this, &ProfileSelectDialog::onEditClicked);
  connect(deleteBtn, &QPushButton::clicked, this, &ProfileSelectDialog::onDeleteClicked);

  // Accept dialog on single click (optional: or use a separate "Activate" button)
  connect(profileList, &QListWidget::itemClicked, [=](QListWidgetItem *item) {
    selected = item->text();
    accept();
  });
}

QString ProfileSelectDialog::selectedProfile() const {
  return selected;
}

void ProfileSelectDialog::onProfileActivated(QListWidgetItem *item) {
  selected = item->text();
  accept();
}

void ProfileSelectDialog::onCreateClicked() {
  emit createProfileRequested();
}

void ProfileSelectDialog::onEditClicked() {
  QListWidgetItem *item = profileList->currentItem();
  if (item) emit editProfileRequested(item->text());
}

void ProfileSelectDialog::onDeleteClicked() {
  QListWidgetItem *item = profileList->currentItem();
  if (item) emit deleteProfileRequested(item->text());
}
