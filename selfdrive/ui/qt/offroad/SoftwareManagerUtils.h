#ifndef SOFTWAREMANAGERUTILS_H
#define SOFTWAREMANAGERUTILS_H

#include <QStringList>

namespace SoftwareManagerUtils {
  // Parses raw fork listing lines into normalized entries "fork__branch" or "fork".
  QStringList parseForkLines(const QStringList &rawLines);
}

#endif // SOFTWAREMANAGERUTILS_H
