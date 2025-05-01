#include "mainwindow.h"

#include <QApplication>
#include <QMetaType>
#include <opencv2/core.hpp>

int main(int argc, char *argv[])
{
    qRegisterMetaType<cv::Mat>("cv::Mat");

    QApplication a(argc, argv);
    MainWindow w;
    w.show();
    return a.exec();
}
