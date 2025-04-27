#include <QtTest>
#include "SoftwareManagerUtils.h"

class TestSoftwareManagerUtils : public QObject {
  Q_OBJECT

private slots:
  void test_parseForkLines_simple();
  void test_parseForkLines_with_branches();
  void test_parseForkLines_ignore_lines();
};

void TestSoftwareManagerUtils::test_parseForkLines_simple() {
  QStringList raw = {"openpilot [master] at /path"};
  QStringList parsed = SoftwareManagerUtils::parseForkLines(raw);
  QCOMPARE(parsed.size(), 1);
  QCOMPARE(parsed.first(), QString("openpilot__master"));
}

void TestSoftwareManagerUtils::test_parseForkLines_with_branches() {
  QStringList raw = {"repo [dev] at /path", "otherrepo at /otherpath"};
  QStringList parsed = SoftwareManagerUtils::parseForkLines(raw);
  QCOMPARE(parsed.size(), 2);
  QCOMPARE(parsed[0], QString("repo__dev"));
  QCOMPARE(parsed[1], QString("otherrepo"));
}

void TestSoftwareManagerUtils::test_parseForkLines_ignore_lines() {
  QStringList raw = {"Installed forks:", "    ", "something [x] at /p"};
  QStringList parsed = SoftwareManagerUtils::parseForkLines(raw);
  QCOMPARE(parsed.size(), 1);
  QCOMPARE(parsed.first(), QString("something__x"));
}

QTEST_MAIN(TestSoftwareManagerUtils)
#include "test_SoftwareManagerUtils.moc"
