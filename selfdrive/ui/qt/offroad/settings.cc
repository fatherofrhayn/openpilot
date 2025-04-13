#include "settings.h"
#include "ForkManagerPanel.h"
// ... other includes ...

// In SettingsWindow constructor, after other panels are added:
ForkManagerPanel *forkManagerPanel = new ForkManagerPanel(this);
QPushButton *forkManagerBtn = new QPushButton(tr("Fork Manager"));
forkManagerBtn->setCheckable(true);
forkManagerBtn->setStyleSheet(R"(
  QPushButton {
    color: grey;
    border: none;
    background: none;
    font-size: 65px;
    font-weight: 500;
  }
  QPushButton:checked {
    color: white;
  }
  QPushButton:pressed {
    color: #ADADAD;
  }
)");
forkManagerBtn->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Expanding);
nav_btns->addButton(forkManagerBtn);
sidebar_layout->addWidget(forkManagerBtn, 0, Qt::AlignRight);

ScrollView *forkManagerPanelFrame = new ScrollView(forkManagerPanel, this);
panel_widget->addWidget(forkManagerPanelFrame);

QObject::connect(forkManagerBtn, &QPushButton::clicked, [=]() {
  forkManagerBtn->setChecked(true);
  panel_widget->setCurrentWidget(forkManagerPanelFrame);
});
