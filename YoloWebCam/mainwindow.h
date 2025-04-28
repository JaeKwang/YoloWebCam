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
#include <QMap> // 추가
#include <QStringList> // 추가

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
    void on_newClassButton_clicked();
    void on_deleteClassButton_clicked();
    void setupImageLabel();
    void onBoxCreated(const QRectF& rect);

protected:
    void keyPressEvent(QKeyEvent *event) override;

private:
    Ui::MainWindow *ui;
    QImage currentFrame;            // 마지막 프레임 저장

    QString currentDirectory;  // 현재 폴더 경로 저장
    QMap<int, QString> classNames;

    WebcamWorker *webcamWorker;
    QThread *workerThread;

    void setImage(const QImage& image);
    QImage cvMatToQImage(const cv::Mat &mat);
    void updatePathLabel(const QString& path);
    void loadClassNames(const QString& yamlPath);
};

#endif // MAINWINDOW_H
