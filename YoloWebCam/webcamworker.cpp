#include "webcamworker.h"
#include <QThread>

WebcamWorker::WebcamWorker(QObject *parent)
    : QObject(parent), running(false)
{
}

WebcamWorker::~WebcamWorker()
{
    stop();
}

void WebcamWorker::start()
{
    if (running) return;

    running = true;
    cap.open(0); // 0번 카메라 열기

    if (!cap.isOpened()) {
        qWarning("Failed to open webcam.");
        running = false;
        return;
    }

    while (running) {
        cv::Mat frame;
        cap >> frame;
        if (frame.empty())
            continue;

        cv::cvtColor(frame, frame, cv::COLOR_BGR2RGB);
        QImage image(frame.data, frame.cols, frame.rows, frame.step, QImage::Format_RGB888);

        emit frameReady(image.copy()); // QImage 복사해서 보내기

        QThread::msleep(30); // 대략 30FPS
    }

    cap.release();
}

void WebcamWorker::stop()
{
    QMutexLocker locker(&mutex);
    running = false;
}
