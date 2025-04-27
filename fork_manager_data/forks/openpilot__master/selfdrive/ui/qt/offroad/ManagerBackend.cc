#include "ManagerBackend.h"
#include <QTimer>
#include <QDateTime>

ManagerBackend::ManagerBackend(QObject *parent) : QObject(parent), running_(false) {
  // Heartbeat timer to emit periodic logs
  QTimer *timer = new QTimer(this);
  connect(timer, &QTimer::timeout, this, [this]() {
    if (!running_) return;
    QString timestamp = QDateTime::currentDateTime().toString("hh:mm:ss");
    emit logUpdated(timestamp + " - heartbeat");
  });
  timer->start(1000);
}

void ManagerBackend::start() {
  if (running_) return;
  running_ = true;
  emit statusChanged(tr("Running"));
  emit logUpdated(tr("Manager backend started"));
}

void ManagerBackend::stop() {
  if (!running_) return;
  running_ = false;
  emit statusChanged(tr("Stopped"));
  emit logUpdated(tr("Manager backend stopped"));
}
