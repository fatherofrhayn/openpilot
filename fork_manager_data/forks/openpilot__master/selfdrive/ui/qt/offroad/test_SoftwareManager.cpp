#include <QtTest>
#include <QSignalSpy>
#include <QProcess>
#include "SoftwareManager.h"
#include "PathConfig.h"

class TestSoftwareManager : public QObject {
  Q_OBJECT

private slots:
  void initTestCase();
  void test_listForks_signal();
  void cleanupTestCase();
};

void TestSoftwareManager::initTestCase() {
  // Set CLI override to a stub script in tests/data
  qputenv("OPENPILOT_FORK_CLI", "/usr/bin/echo");
}

void TestSoftwareManager::test_listForks_signal() {
  SoftwareManager mgr;
  QSignalSpy spy(&mgr, SIGNAL(forksListed(QStringList)));

  mgr.triggerUpdate(SoftwareManager::UpdateType::LIST_FORKS);

  // Wait for the signal (since echo returns immediately with no args, we expect empty list)
  QVERIFY(spy.wait(1000));
  QList<QVariant> args = spy.takeFirst();
  QStringList forks = args.at(0).toStringList();
  QCOMPARE(forks.size(), 0);
}

void TestSoftwareManager::cleanupTestCase() {
  // Clear override
  qputenv("OPENPILOT_FORK_CLI", "");
}

QTEST_MAIN(TestSoftwareManager)
#include "test_SoftwareManager.moc"
