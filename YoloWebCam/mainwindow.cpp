#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QTimer>
#include <QImage>
#include <QPixmap>
#include <QFileDialog>
#include <QDir>
#include <QFileInfoList>
#include <QDateTime>
#include <QFontMetrics>
#include <QMessageBox>
#include <QPainter>
#include <QPen>
#include <QTextStream>

int currentTabIndex = 0;  // 0: Train, 1: Val

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    ui->videoLabel->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Ignored);

    webcamWorker = new WebcamWorker();
    workerThread = new QThread();

    webcamWorker->moveToThread(workerThread);

    connect(workerThread, &QThread::started, webcamWorker, &WebcamWorker::start);
    connect(webcamWorker, &WebcamWorker::frameReady, this, &MainWindow::updateFrame);
    connect(this, &MainWindow::destroyed, this, &MainWindow::cleanupWorker);
    connect(ui->fileListWidget, &QListWidget::itemClicked, this, &MainWindow::on_fileItemClicked);
    connect(ui->tabWidget, &QTabWidget::currentChanged, this, &MainWindow::on_tabWidget_currentChanged);

    connect(ui->actionSetPath, &QAction::triggered, this, &MainWindow::openFolder);


    workerThread->start();
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::updateFrame(const QImage &frame)
{
    currentFrame = frame;
    setImage(currentFrame);
}

void MainWindow::cleanupWorker()
{
    webcamWorker->stop();
    workerThread->quit();
    workerThread->wait();
    delete webcamWorker;
    delete workerThread;
}

void MainWindow::setImage(const QImage& image)
{
    if (ui->videoLabel->size().isEmpty()) return;

    QPixmap pixmap = QPixmap::fromImage(image);

    QSize labelSize = ui->videoLabel->size();
    QPixmap scaledPixmap = pixmap.scaled(labelSize, Qt::KeepAspectRatio, Qt::SmoothTransformation);

    ui->videoLabel->setPixmap(scaledPixmap);
}

void MainWindow::on_captureButton_clicked()
{
    if (currentFrame.isNull()) {
        qWarning("No frame to capture.");
        return;
    }

    if (currentDirectory.isEmpty()) {
        qWarning("No directory selected.");
        return;
    }

    QString subFolder = (currentTabIndex == 0) ? "train" : "val";

    QString timestamp = QDateTime::currentDateTime().toString("yyyyMMddHHmmss");
    QString savePath = currentDirectory + "/images/" + subFolder + "/capture_" + timestamp + ".jpg";

    if (currentFrame.save(savePath)) {
        refreshFileList(); // 캡처 후 리스트 갱신
    }
    else {
        qWarning("Failed to save image.");
    }
}


void MainWindow::on_setDirButton_clicked()
{
    openFolder();
}

void MainWindow::openFolder()
{
    QString dir = QFileDialog::getExistingDirectory(this, tr("폴더 선택"), "");

    if (dir.isEmpty())
        return;

    currentDirectory = dir; // 현재 디렉토리 기억

    refreshFileList(); // 리스트 갱신

    ui->captureButton->setDisabled(false);
    ui->prevButton->setDisabled(false);
    ui->fileDeleteButton->setDisabled(false);
    ui->nextButton->setDisabled(false);
}

void MainWindow::refreshFileList()
{
    QString imagesPath, labelsPath;

    if (currentTabIndex == 0) { // Train 탭
        imagesPath = currentDirectory + "/images/train/";
        labelsPath = currentDirectory + "/labels/train/";
    } else { // Val 탭
        imagesPath = currentDirectory + "/images/val/";
        labelsPath = currentDirectory + "/labels/val/";
    }

    QDir imagesDir(imagesPath);
    QDir labelsDir(labelsPath);

    bool needCreate = false;
    QString missingFolders;

    if (!imagesDir.exists()) {
        if (currentTabIndex == 0) { // Train 탭
            missingFolders += "images/train ";
        } else {
            missingFolders += "images/val ";
        }
        needCreate = true;
    }
    if (!labelsDir.exists()) {
        if (currentTabIndex == 0) { // Train 탭
            missingFolders += "labels/train ";
        } else {
            missingFolders += "labels/val ";
        }
        needCreate = true;
    }

    if (needCreate) {
        QMessageBox::StandardButton reply = QMessageBox::question(
            this,
            "폴더 없음",
            QString("%1폴더가 없습니다.\n생성하시겠습니까?").arg(missingFolders),
            QMessageBox::Yes | QMessageBox::Cancel
        );

        if (reply == QMessageBox::Yes) {
            if (!imagesDir.exists() && !imagesDir.mkpath(".")) {
                qWarning("Failed to create images folder!");
                return;
            }
            if (!labelsDir.exists() && !labelsDir.mkpath(".")) {
                qWarning("Failed to create labels folder!");
                return;
            }
        } else {
            return;
        }
    }

    // 🔥 이미지 파일만 필터링
    QStringList filters;
    filters << "*.png" << "*.jpg" << "*.jpeg" << "*.bmp";
    imagesDir.setNameFilters(filters);
    imagesDir.setFilter(QDir::Files | QDir::NoDotAndDotDot);

    QFileInfoList entries = imagesDir.entryInfoList(QDir::Files | QDir::NoDotAndDotDot, QDir::Name);

    ui->fileListWidget->clear();

    for (const QFileInfo &entry : entries) {
        QString baseName = entry.completeBaseName();  // 파일명 (확장자 제거)

        QString labelFilePath = labelsPath + baseName + ".txt";
        bool labelExists = QFile::exists(labelFilePath);

        QListWidgetItem* item = new QListWidgetItem(entry.fileName());
        if (labelExists) {
            item->setForeground(Qt::blue);
        } else {
            item->setForeground(Qt::red);
        }
        ui->fileListWidget->addItem(item);
    }

    int fileCount = entries.count();
    ui->imageInfoLabel->setText(QString("0 / %1").arg(fileCount));
    updatePathLabel(currentDirectory);
}

void MainWindow::updatePathLabel(const QString& path)
{
    QFontMetrics metrics(ui->pathLabel->font());
    QString elidedPath = metrics.elidedText(path, Qt::ElideMiddle, ui->pathLabel->width());
    ui->pathLabel->setText(elidedPath);
}

void MainWindow::on_fileItemClicked(QListWidgetItem* item)
{
    if (!item)
        return;

    // 1. 웹캠 스레드 정지
    if (workerThread && workerThread->isRunning()) {
        webcamWorker->stop();
        workerThread->quit();
        workerThread->wait();
    }

    // 2. 현재 탭에 따라 이미지/레이블 경로 결정
    QString subFolder = (currentTabIndex == 0) ? "train" : "val";

    QString fileName = item->text();
    QString imagePath = currentDirectory + "/images/" + subFolder + "/" + fileName;
    QString labelPath = currentDirectory + "/labels/" + subFolder + "/" + QFileInfo(fileName).completeBaseName() + ".txt";

    // 3. 이미지 로드
    QImage image;
    if (!image.load(imagePath)) {
        qWarning("Failed to load image: %s", qPrintable(imagePath));
        return;
    }

    QPixmap pixmap = QPixmap::fromImage(image);
    QPainter painter(&pixmap);
    painter.setPen(QPen(Qt::red, 2)); // 빨간색, 굵기 2

    // 4. 라벨 파일 읽기
    QFile labelFile(labelPath);
    if (labelFile.exists() && labelFile.open(QIODevice::ReadOnly | QIODevice::Text)) {
        QTextStream in(&labelFile);
        while (!in.atEnd()) {
            QString line = in.readLine();
            QStringList parts = line.split(' ');
            if (parts.size() != 5)
                continue; // 포맷 이상하면 건너뛴다

            // YOLO 포맷: class_id x_center y_center width height
            float x_center = parts[1].toFloat();
            float y_center = parts[2].toFloat();
            float width = parts[3].toFloat();
            float height = parts[4].toFloat();

            int imgWidth = pixmap.width();
            int imgHeight = pixmap.height();

            QRectF box(
                (x_center - width / 2) * imgWidth,
                (y_center - height / 2) * imgHeight,
                width * imgWidth,
                height * imgHeight
            );

            painter.drawRect(box);
        }
        labelFile.close();
    }

    painter.end();

    currentFrame = pixmap.toImage(); // currentFrame 업데이트
    setImage(currentFrame);          // QLabel에 띄우기

    // 5. 선택된 파일 인덱스 업데이트
    int selectedIndex = ui->fileListWidget->row(item) + 1;
    int totalCount = ui->fileListWidget->count();

    ui->imageInfoLabel->setText(QString("%1 / %2").arg(selectedIndex).arg(totalCount));
    ui->captureButton->setDisabled(true);
    ui->webcamButton->setDisabled(false);
}

void MainWindow::resumeWebcam()
{
    if (workerThread && !workerThread->isRunning()) {
        workerThread->start();

        ui->captureButton->setDisabled(false);
        ui->webcamButton->setDisabled(true);
    }
}


void MainWindow::on_webcamButton_clicked()
{
    resumeWebcam();
}


void MainWindow::on_prevButton_clicked()
{
    int currentRow = ui->fileListWidget->currentRow();
    if (currentRow > 0) {
        ui->fileListWidget->setCurrentRow(currentRow - 1);
        on_fileItemClicked(ui->fileListWidget->currentItem()); // 항목 클릭 함수 호출
    }
}

void MainWindow::on_nextButton_clicked()
{
    int currentRow = ui->fileListWidget->currentRow();
    int totalCount = ui->fileListWidget->count();

    if (currentRow < totalCount - 1) {
        ui->fileListWidget->setCurrentRow(currentRow + 1);
        on_fileItemClicked(ui->fileListWidget->currentItem()); // 항목 클릭 함수 호출
    }
}

void MainWindow::on_fileDeleteButton_clicked()
{
    QListWidgetItem* item = ui->fileListWidget->currentItem();
    if (!item) {
        qWarning("No item selected for deletion.");
        return;
    }

    QString subFolder = (currentTabIndex == 0) ? "train" : "val";

    QString fileName = item->text();
    QString imagePath = currentDirectory + "/images/" + subFolder + "/" + fileName;
    QString labelPath = currentDirectory + "/labels/" + subFolder + "/" + QFileInfo(fileName).completeBaseName() + ".txt";

    // 🔥 정말 삭제할지 물어보기
    QMessageBox::StandardButton reply;
    reply = QMessageBox::question(
        this,
        "파일 삭제 확인",
        QString("이미지와 레이블 파일을 삭제하시겠습니까?\n\n%1\n%2").arg(imagePath, labelPath),
        QMessageBox::Yes | QMessageBox::No
    );

    if (reply == QMessageBox::Yes) {
        bool imageDeleted = false;
        bool labelDeleted = false;

        // 이미지 파일 삭제
        if (QFile::exists(imagePath)) {
            imageDeleted = QFile::remove(imagePath);
        }

        // 레이블 파일 삭제
        if (QFile::exists(labelPath)) {
            labelDeleted = QFile::remove(labelPath);
        }

        if (imageDeleted || labelDeleted) {
            qDebug("Files deleted successfully.");

            // 리스트 갱신
            refreshFileList();
        } else {
            qWarning("Failed to delete files.");
            QMessageBox::warning(this, "삭제 실패", "파일 삭제에 실패했습니다.");
        }
    }
}


void MainWindow::on_tabWidget_currentChanged(int index)
{
    if (currentDirectory.isEmpty())
        return;

    currentTabIndex = index;
    refreshFileList();
}
