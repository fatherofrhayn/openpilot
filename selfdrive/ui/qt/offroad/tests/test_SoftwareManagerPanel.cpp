#include <QSignalSpy>
#include <QtTest>
#include "selfdrive/ui/qt/offroad/SoftwareManagerPanel.h"
#include <QMetaObject>

class TestSoftwareManagerPanel : public QObject {
  Q_OBJECT

private slots:
  void test_updateNotification_signal();
};

void TestSoftwareManagerPanel::test_updateNotification_signal() {
  // Instantiate panel
  SoftwareManagerPanel panel;
  QSignalSpy spy(&panel, SIGNAL(updateNotification(QString)));
  QVERIFY(spy.isValid());

  // Simulate CLI output containing an update availability message
  QString simulatedOutput = "Local version: abc123\nRemote version: def456\nUpdate available.";
  bool invoked = QMetaObject::invokeMethod(&panel, "onManagerCliOutput",
                                           Q_ARG(QString, simulatedOutput));
  QVERIFY(invoked);

  // Wait briefly for signal
  QVERIFY(spy.wait(100));
  QCOMPARE(spy.count(), 1);
  QList<QVariant> args = spy.takeFirst();
  QString notif = args.at(0).toString();
  QVERIFY(notif.contains("def456"));
}

QTEST_MAIN(TestSoftwareManagerPanel)
#include "test_SoftwareManagerPanel.moc"
