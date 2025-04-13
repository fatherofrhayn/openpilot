#pragma once

#include <QFrame>
#include <QStackedWidget>
#include <QButtonGroup>
#include <QPushButton>
#include <QVBoxLayout>
#include "ForkManagerPanel.h"
// ... other includes ...

class SettingsWindow : public QFrame {
  Q_OBJECT

public:
  explicit SettingsWindow(QWidget *parent = nullptr);

private:
  // ... other members ...
  ForkManagerPanel *forkManagerPanel;
};
