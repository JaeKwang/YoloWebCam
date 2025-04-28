#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QTimer>
#include <QImage>
#include <QPixmap>
#include <opencv2/opencv.hpp>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
    , timer(new QTimer(this))
{
    ui->setupUi(this);
    ui->videoLabel->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Ignored);

    connect(timer, &QTimer::timeout, this, &MainWindow::captureFrame);

    startCamera();
}

MainWindow::~MainWindow()
{
    if (cap.isOpened()) cap.release();
    delete ui;
}

void MainWindow::startCamera()
{
    if (!cap.isOpened()) {
        cap.open(0); // 0번 웹캠 열기
        if (!cap.isOpened()) {
            qDebug("Failed to open camera.");
            return;
        }
    }
    timer->start(30); // 30ms마다 frame 캡처 (약 30fps)
}


void MainWindow::captureFrame()
{
    if (!cap.isOpened()) return;

    cv::Mat frame;
    cap >> frame; // 프레임 읽기

    if (!frame.empty()) {
        // OpenCV BGR → RGB 변환
        cv::cvtColor(frame, frame, cv::COLOR_BGR2RGB);

        QImage image = cvMatToQImage(frame);
        currentFrame = image;
        setImage(image);
    }
}

QImage MainWindow::cvMatToQImage(const cv::Mat &mat)
{
    return QImage(mat.data, mat.cols, mat.rows, mat.step, QImage::Format_RGB888).copy();
}

void MainWindow::setImage(const QImage& image)
{
    if (ui->videoLabel->size().isEmpty()) return;

    QPixmap pixmap = QPixmap::fromImage(image);

    QSize labelSize = ui->videoLabel->size();
    QPixmap scaledPixmap = pixmap.scaled(labelSize, Qt::KeepAspectRatio, Qt::SmoothTransformation);

    ui->videoLabel->setPixmap(scaledPixmap);
}
