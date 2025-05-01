// inferenceworker.cpp
#include "inferenceworker.h"
#include <QImage>
#include <chrono>

InferenceWorker::InferenceWorker(QObject *parent) : QObject(parent) {}

void InferenceWorker::setModel(cv::dnn::Net model) {
    net = model;
}

void InferenceWorker::processFrame(const cv::Mat &frame) {

    if (frame.empty()) return;

    auto start = std::chrono::high_resolution_clock::now();

    cv::Mat blob = cv::dnn::blobFromImage(frame, 1/255.0, cv::Size(640, 640), cv::Scalar(), true, false);
    net.setInput(blob);

    std::vector<cv::Mat> outputs;
    net.forward(outputs, net.getUnconnectedOutLayersNames());

    qDebug("InferenceWorker::processFrame: %d", outputs.size());
    // 단순히 원본을 전달 (여기선 바운딩 박스 처리 생략)
    QImage result(frame.data, frame.cols, frame.rows, frame.step, QImage::Format_RGB888);

    auto end = std::chrono::high_resolution_clock::now();
    double durationMs = std::chrono::duration<double, std::milli>(end - start).count();
    emit inferenceCompleted(result.rgbSwapped(), durationMs);  // 🔥 처리 시간 전달
}
