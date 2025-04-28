#ifndef WEBCAMWORKER_H
#define WEBCAMWORKER_H

#include <QObject>
#include <QImage>
#include <QMutex>
#include <opencv2/opencv.hpp>

class WebcamWorker : public QObject
{
    Q_OBJECT

public:
    explicit WebcamWorker(QObject *parent = nullptr);
    ~WebcamWorker();

public slots:
    void start();
    void stop();

signals:
    void frameReady(const QImage &frame);

private:
    bool running;
    QMutex mutex;
    cv::VideoCapture cap;
};

#endif // WEBCAMWORKER_H
