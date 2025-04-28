#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QImage>
#include <QTimer>
#include <QPixmap>
#include <opencv2/opencv.hpp>  // OpenCV 사용

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void startCamera();
    void captureFrame();

private:
    Ui::MainWindow *ui;
    QTimer *timer;                 // 프레임 캡처용 타이머
    cv::VideoCapture cap;           // OpenCV 웹캠 캡처
    QImage currentFrame;            // 마지막 프레임 저장

    void setImage(const QImage& image);
    QImage cvMatToQImage(const cv::Mat &mat);
};

#endif // MAINWINDOW_H
