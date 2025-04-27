#pragma once

#include <QWidget>
#include <QPushButton>
#include <QPlainTextEdit>
#include <QLabel>
#include <QGroupBox>
#include "ManagerBackend.h"

class ManagerPanel : public QWidget {
  Q_OBJECT

public:
  explicit ManagerPanel(QWidget *parent = nullptr);

 signals:
   void startManager();
   void stopManager();

 private slots:
   void onStartClicked();
   void onStopClicked();

 private:
   QGroupBox *control_box;
   QPushButton *start_btn;
   QPushButton *stop_btn;

   QGroupBox *status_box;
   QLabel *status_label;

   QGroupBox *log_box;
   QPlainTextEdit *log_view;
   ManagerBackend *backend_; 
};
