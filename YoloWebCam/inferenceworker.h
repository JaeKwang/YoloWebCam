// inferenceworker.h
#pragma once
#include <QObject>
#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>

class InferenceWorker : public QObject {
    Q_OBJECT
public:
    explicit InferenceWorker(QObject *parent = nullptr);
    void setModel(cv::dnn::Net net);
public slots:
    void processFrame(const cv::Mat &frame); // 외부에서 호출
signals:
    void inferenceCompleted(const QImage &image, const double time);
private:
    cv::dnn::Net net;
};
