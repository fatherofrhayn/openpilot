#include "ManagerPanel.h"
#include <QVBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QGroupBox>
#include <QPlainTextEdit>
#include <QHBoxLayout>

ManagerPanel::ManagerPanel(QWidget *parent) : QWidget(parent) {
  QVBoxLayout *layout = new QVBoxLayout(this);

  // Control box
  control_box = new QGroupBox(tr("Control"), this);
  QHBoxLayout *control_layout = new QHBoxLayout(control_box);
  start_btn = new QPushButton(tr("Start"), this);
  stop_btn = new QPushButton(tr("Stop"), this);
  control_layout->addWidget(start_btn);
  control_layout->addWidget(stop_btn);
  control_box->setLayout(control_layout);
  layout->addWidget(control_box);

  // Status box
  status_box = new QGroupBox(tr("Status"), this);
  QHBoxLayout *status_layout = new QHBoxLayout(status_box);
  status_label = new QLabel(tr("Idle"), this);
  status_layout->addWidget(status_label);
  status_box->setLayout(status_layout);
  layout->addWidget(status_box);

  // Log box
  log_box = new QGroupBox(tr("Logs"), this);
  QVBoxLayout *log_layout = new QVBoxLayout(log_box);
  log_view = new QPlainTextEdit(this);
  log_view->setReadOnly(true);
  log_layout->addWidget(log_view);
  log_box->setLayout(log_layout);
  layout->addWidget(log_box);

  // Connect signals
  connect(start_btn, &QPushButton::clicked, this, &ManagerPanel::onStartClicked);
  connect(stop_btn, &QPushButton::clicked, this, &ManagerPanel::onStopClicked);

  // Backend setup
  backend_ = new ManagerBackend(this);
  connect(backend_, &ManagerBackend::statusChanged, status_label, &QLabel::setText);
  connect(backend_, &ManagerBackend::logUpdated, log_view, &QPlainTextEdit::appendPlainText);
  connect(this, &ManagerPanel::startManager, backend_, &ManagerBackend::start);
  connect(this, &ManagerPanel::stopManager, backend_, &ManagerBackend::stop);

  setLayout(layout);
}

// Slot implementations
void ManagerPanel::onStartClicked() {
  status_label->setText(tr("Running"));
  log_view->appendPlainText(tr("Manager started"));
  emit startManager();
}

void ManagerPanel::onStopClicked() {
  status_label->setText(tr("Stopped"));
  log_view->appendPlainText(tr("Manager stopped"));
  emit stopManager();
}
