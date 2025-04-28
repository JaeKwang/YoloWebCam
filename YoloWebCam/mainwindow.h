#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QImage>
#include <QTimer>
#include <QPixmap>
#include <opencv2/opencv.hpp>  // OpenCV 사용
#include "webcamworker.h"
#include <QThread>
#include <QListWidgetItem>

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
    void updateFrame(const QImage &frame);
    void cleanupWorker();
    void on_setDirButton_clicked();
    void on_captureButton_clicked();
    void refreshFileList();
    void openFolder();
    void on_fileItemClicked(QListWidgetItem* item);
    void resumeWebcam();
    void on_webcamButton_clicked();
    void on_prevButton_clicked();
    void on_nextButton_clicked();
    void on_fileDeleteButton_clicked();
    void on_tabWidget_currentChanged(int index);

private:
    Ui::MainWindow *ui;
    QImage currentFrame;            // 마지막 프레임 저장

    void setImage(const QImage& image);
    QImage cvMatToQImage(const cv::Mat &mat);
    void updatePathLabel(const QString& path);

    QString currentDirectory;  // 현재 폴더 경로 저장

    WebcamWorker *webcamWorker;
    QThread *workerThread;
};

#endif // MAINWINDOW_H
