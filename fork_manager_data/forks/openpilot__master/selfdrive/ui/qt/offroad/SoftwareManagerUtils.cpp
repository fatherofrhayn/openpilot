#include "SoftwareManagerUtils.h"
#include <QRegExp>

namespace SoftwareManagerUtils {

QStringList parseForkLines(const QStringList &rawLines) {
  QStringList entries;
  QRegExp re("\\s*(.+?)\\s*(?:\\[(.*?)\\])?\\s*at\\s");
  for (const QString &line : rawLines) {
    QString trim = line.trimmed();
    if (trim.isEmpty() || trim.startsWith("Installed")) continue;
    if (trim.contains(" at ") && re.indexIn(trim) != -1) {
      QString fname = re.cap(1);
      QString bname = re.cap(2);
      entries << (bname.isEmpty() ? fname : fname + "__" + bname);
    } else {
      entries << trim;
    }
  }
  return entries;
}

} // namespace SoftwareManagerUtils
