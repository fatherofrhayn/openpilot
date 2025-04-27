#pragma once

#include <QObject>
#include <QString>

class ManagerBackend : public QObject {
  Q_OBJECT

public:
  explicit ManagerBackend(QObject *parent = nullptr);

public slots:
  void start();
  void stop();

signals:
  void statusChanged(const QString &status);
  void logUpdated(const QString &log);

private:
  bool running_;
};
