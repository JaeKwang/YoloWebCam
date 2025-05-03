# mainwindow.py (with ImageLabel for stable scaling)
import os
import cv2
import sys
import time
import traceback
import numpy as np
from PySide6.QtCore import Qt, QThread, QSize, QTimer, QPointF, QRectF, QDateTime
from PySide6.QtWidgets import QMainWindow, QFileDialog, QListWidgetItem, QMessageBox, QSizePolicy
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from webcam_worker import WebcamWorker
from inference_worker import InferenceWorker
from image_label import ImageLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = self.load_ui(self)
        self.setCentralWidget(self.ui.centralWidget())

        self.weightFileLoad = False
        self.is_image_preview = False
        self.last_preview_image_path = ""
        self.current_directory = ""
        self.current_tab_index = 0
        self.current_frame = QImage()
        self.last_boxes = []
        self.class_names = {}
        self.last_infer_time = 0

        # Inference worker setup
        self.infer_thread = QThread()
        self.infer_worker = InferenceWorker()
        self.infer_worker.moveToThread(self.infer_thread)
        self.infer_worker.inferenceCompleted.connect(self.update_overlay_boxes)
        self.infer_thread.start()

        # Webcam worker setup
        self.webcam_thread = QThread()
        self.webcam_worker = WebcamWorker()
        self.webcam_worker.moveToThread(self.webcam_thread)
        self.webcam_worker.frameCaptured.connect(self.update_frame)
        self.webcam_worker.frameCaptured.connect(self.send_for_inference)
        self.webcam_thread.started.connect(self.webcam_worker.start)
        self.webcam_thread.start()

        self.ui.setWeightButton.clicked.connect(self.on_set_weight_button_clicked)
        self.ui.captureButton.clicked.connect(self.on_capture_button_clicked)
        self.ui.setDirButton.clicked.connect(self.on_set_dir_button_clicked)
        self.ui.fileListWidget.itemClicked.connect(self.on_file_item_clicked)
        self.ui.tabWidget.currentChanged.connect(self.on_tab_widget_changed)
        self.ui.newClassButton.clicked.connect(self.on_new_class_button_clicked)
        self.ui.deleteClassButton.clicked.connect(self.on_delete_class_button_clicked)
        self.ui.webcamButton.clicked.connect(self.resume_webcam)
        self.ui.prevButton.clicked.connect(self.on_prev_button_clicked)
        self.ui.nextButton.clicked.connect(self.on_next_button_clicked)
        self.ui.fileDeleteButton.clicked.connect(self.on_file_delete_button_clicked)
        self.ui.InfStartButton.clicked.connect(self.on_start_inference_clicked)
        self.ui.InfStopButton.clicked.connect(self.on_stop_inference_clicked)
        self.ui.videoLabel.rectDrawn.connect(self.save_drawn_box)
        self.showMaximized()

    def load_ui(self, parent=None):
        from PySide6.QtUiTools import QUiLoader
        from PySide6.QtCore import QFile
        from pathlib import Path
        from PySide6.QtWidgets import QLabel, QHBoxLayout

        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        ui = loader.load(ui_file, parent)
        ui_file.close()

        old = ui.findChild(QLabel, "videoLabel")
        if old:
            layout = ui.findChild(QHBoxLayout, "mainLayout")
            idx = layout.indexOf(old)
            layout.removeWidget(old)
            old.setParent(None)

            new_label = ImageLabel()
            new_label.setObjectName("videoLabel")
            layout.insertWidget(idx, new_label, 4)

            ui.videoLabel = new_label  # 필수: 코드 접근을 위해 바꿔줌
        return ui

    def update_frame(self, qimage: QImage):
        if self.is_image_preview:
            return
        try:
            self.current_frame = qimage
            pixmap = QPixmap.fromImage(qimage)
            self.ui.videoLabel.setImage(pixmap, self.last_boxes)
        except Exception as e:
            print("[ERROR] update_frame failed:", e)
            traceback.print_exc()

    def send_for_inference(self, qimage: QImage):
        now = time.time()
        if now - self.last_infer_time >= 0.2:  # 이미지 추론 간격
            self.last_infer_time = now
            self.infer_worker.infer(qimage)

    def update_overlay_boxes(self, boxes: list):
        self.last_boxes = boxes
        if self.is_image_preview and os.path.exists(self.last_preview_image_path):
            image = QImage(self.last_preview_image_path)
            if image.isNull():
                print(f"[ERROR] 이미지 로드 실패: {self.last_preview_image_path}")
                return

            self.current_frame = image  # ✅ 현재 프레임으로 설정
            self.ui.videoLabel.setImage(QPixmap.fromImage(image), self.last_boxes)
        else:
            print("[INFO] 이미지 미리보기 상태가 아님, 무시됨")

    def closeEvent(self, event):
        self.webcam_worker.stop()
        self.webcam_thread.quit()
        self.webcam_thread.wait()

        self.infer_thread.quit()
        self.infer_thread.wait()
        super().closeEvent(event)

    def open_folder(self):
        dir = QFileDialog.getExistingDirectory(self, self.tr("폴더 선택"), "")
        if not dir:
            return

        prevDir = self.current_directory
        self.current_directory = dir
        if not self.refresh_file_list():
            self.current_directory = prevDir
            return

        self.load_class_names(os.path.join(self.current_directory, "data.yaml"))
        self.resume_webcam()

        self.ui.newClassButton.setDisabled(False)
        self.ui.classNameEdit.setDisabled(False)
        self.ui.deleteClassButton.setDisabled(False)
        self.ui.captureButton.setDisabled(False)
        self.ui.prevButton.setDisabled(False)
        self.ui.fileDeleteButton.setDisabled(False)
        self.ui.nextButton.setDisabled(False)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "YOLO 모델 선택",
            "",  # 시작 경로 (비워두면 현재 디렉토리)
            "YOLOv8 모델 파일 (*.pt)"
        )

        if not file_path:
            return

        self.infer_worker.set_model(file_path)
        metrics = self.ui.weightLabel.fontMetrics()
        elided = metrics.elidedText(file_path, Qt.ElideMiddle, self.ui.weightLabel.width())
        self.ui.weightLabel.setStyleSheet("color: black;")
        self.ui.weightLabel.setText(elided)
        self.on_stop_inference_clicked()
        self.weightFileLoad = True

    def on_start_inference_clicked(self):
        self.infer_worker.start_inference()
        self.ui.InfStartButton.setDisabled(True)
        self.ui.InfStopButton.setDisabled(False)

        if self.is_image_preview and os.path.exists(self.last_preview_image_path):
            image = QImage(self.last_preview_image_path)
            if not image.isNull():
                self.send_for_inference(image)
            else:
                print("[ERROR] 이미지 로드 실패")

    def on_stop_inference_clicked(self):
        self.infer_worker.stop_inference()
        self.ui.InfStartButton.setDisabled(False)
        self.ui.InfStopButton.setDisabled(True)
        self.last_boxes = []

    def load_class_names(self, yaml_path):
        from PySide6.QtCore import QFile, QTextStream
        self.class_names = {}
        if self.ui.classListWidget:
            self.ui.classListWidget.clear()
        file = QFile(yaml_path)
        if not file.open(QFile.ReadOnly | QFile.Text):
            print("[WARN] Failed to open data.yaml")
            return
        in_stream = QTextStream(file)
        names_section = False
        names_content = ""
        while not in_stream.atEnd():
            line = in_stream.readLine().strip()
            if line.startswith("names:"):
                names_section = True
                if '[' in line:
                    names_content = line[line.index('['):]
                continue
            if names_section:
                if not names_content and line.startswith('['):
                    names_content = line
                elif names_content:
                    names_content += line
                if ']' in names_content:
                    break
        file.close()
        if names_content:
            names_content = names_content.replace('[', '').replace(']', '').replace("'", "").replace('"', '')
            name_list = names_content.split(',')
            for idx, name in enumerate(name.strip() for name in name_list if name.strip()):
                self.class_names[idx] = name
                self.ui.classListWidget.addItem(f"{idx}: {name}")
            self.ui.classListWidget.setCurrentRow(0)

    def refresh_file_list(self):
        from PySide6.QtCore import QDir
        if self.current_tab_index == 0:
            images_path = os.path.join(self.current_directory, "images/train")
            labels_path = os.path.join(self.current_directory, "labels/train")
        else:
            images_path = os.path.join(self.current_directory, "images/val")
            labels_path = os.path.join(self.current_directory, "labels/val")
        images_dir = QDir(images_path)
        labels_dir = QDir(labels_path)
        need_create = False
        missing = []
        if not images_dir.exists():
            missing.append("images/train" if self.current_tab_index == 0 else "images/val")
            need_create = True
        if not labels_dir.exists():
            missing.append("labels/train" if self.current_tab_index == 0 else "labels/val")
            need_create = True
        if need_create:
            confirm = QMessageBox.question(
                self, "폴더 없음",
                f"{' '.join(missing)} 폴더가 없습니다.\n생성하시겠습니까?",
                QMessageBox.Yes | QMessageBox.Cancel
            )
            if confirm == QMessageBox.Yes:
                if not images_dir.exists():
                    QDir().mkpath(images_path)
                if not labels_dir.exists():
                    QDir().mkpath(labels_path)
            else:
                return False
        self.ui.fileListWidget.clear()
        filters = ["*.png", "*.jpg", "*.jpeg", "*.bmp"]
        images_dir.setNameFilters(filters)
        images_dir.setFilter(QDir.Files | QDir.NoDotAndDotDot)
        entries = images_dir.entryInfoList(QDir.Files | QDir.NoDotAndDotDot, QDir.Name)
        for entry in entries:
            base_name = entry.completeBaseName()
            label_path = os.path.join(labels_path, base_name + ".txt")
            item = QListWidgetItem(entry.fileName())

            if os.path.exists(label_path):
                try:
                    valid = True
                    with open(label_path, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) != 5:
                                valid = False
                                break
                            try:
                                cid = int(parts[0])
                                xc, yc, w, h = map(float, parts[1:])
                                if not (0 <= xc <= 1 and 0 <= yc <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                                    valid = False
                                    break
                                if cid < 0:
                                    valid = False
                                    break
                            except ValueError:
                                valid = False
                                break

                    if valid:
                        item.setForeground(Qt.blue)     # 유효한 라벨
                    else:
                        item.setForeground(QColor("orange"))  # 형식 오류 라벨
                except Exception as e:
                    print(f"[ERROR] Failed to read label: {label_path} - {e}")
                    item.setForeground(QColor("orange"))
            else:
                item.setForeground(Qt.red)  # 레이블 없음
            self.ui.fileListWidget.addItem(item)
        self.ui.imageInfoLabel.setText(f"0 / {len(entries)}")
        self.update_path_label(self.current_directory)
        return True

    def on_set_dir_button_clicked(self):
        self.open_folder()

    def on_set_weight_button_clicked(self):
        self.open_file()

    def update_path_label(self, path):
        metrics = self.ui.pathLabel.fontMetrics()
        elided = metrics.elidedText(path, Qt.ElideMiddle, self.ui.pathLabel.width())
        self.ui.pathLabel.setStyleSheet("color: black;")
        self.ui.pathLabel.setText(elided)

    def on_capture_button_clicked(self):
        if self.current_frame.isNull():
            print("[WARN] No frame to capture")
            return

        if not self.current_directory:
            print("[WARN] No directory set")
            return

        sub = "train" if self.current_tab_index == 0 else "val"
        timestamp = QDateTime.currentDateTime().toString("yyyyMMddHHmmss")
        save_dir = os.path.join(self.current_directory, "images", sub)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"capture_{timestamp}.jpg")

        if self.current_frame.save(save_path):
            print(f"[INFO] Saved to {save_path}")
            self.refresh_file_list()
        else:
            print("[ERROR] Failed to save image")

    def resume_webcam(self):
        self.is_image_preview = False

        if self.webcam_thread and not self.webcam_thread.isRunning():
            self.webcam_thread.start()
            self.ui.captureButton.setDisabled(False)
            self.ui.webcamButton.setDisabled(True)

    def on_file_item_clicked(self, item):
        if not item:
            return

        self.is_image_preview = True
        
        # 1. 웹캠 정지
        if self.webcam_thread and self.webcam_thread.isRunning():
            self.webcam_worker.stop()
            self.webcam_thread.quit()
            self.webcam_thread.wait()
        sub = "train" if self.current_tab_index == 0 else "val"
        fname = item.text()
        img_path = os.path.join(self.current_directory, "images", sub, fname)
        label_path = os.path.join(self.current_directory, "labels", sub, os.path.splitext(fname)[0] + ".txt")
        image = QImage()
        if not image.load(img_path):
            print(f"[WARN] Failed to load image: {img_path}")
            return
        
        self.last_preview_image_path = img_path
        pixmap = QPixmap.fromImage(image)
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.red, 2))
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split(' ')
                    if len(parts) != 5:
                        continue
                    cid = int(parts[0])
                    xc, yc, w, h = map(float, parts[1:])
                    iw, ih = pixmap.width(), pixmap.height()
                    rect = QRectF(
                        (xc - w/2) * iw,
                        (yc - h/2) * ih,
                        w * iw,
                        h * ih
                    )
                    painter.drawRect(rect)
                    if cid in self.class_names:
                        painter.setPen(Qt.green)
                        painter.drawText(rect.topLeft() + QPointF(2, 12), self.class_names[cid])
                        painter.setPen(QPen(Qt.red, 2))
        painter.end()
        self.current_frame = pixmap.toImage()
        self.ui.videoLabel.setImage(QPixmap.fromImage(self.current_frame), [])
        row = self.ui.fileListWidget.row(item) + 1
        total = self.ui.fileListWidget.count()
        self.ui.imageInfoLabel.setText(f"{row} / {total}")
        self.ui.captureButton.setDisabled(True)
        self.ui.webcamButton.setDisabled(False)

        if self.weightFileLoad:
            self.on_stop_inference_clicked()

    def on_tab_widget_changed(self, index):
        self.current_tab_index = index

        if not self.current_directory:
            return

        self.refresh_file_list()

    def on_prev_button_clicked(self):
        row = self.ui.fileListWidget.currentRow()
        if row > 0:
            self.ui.fileListWidget.setCurrentRow(row - 1)
            self.on_file_item_clicked(self.ui.fileListWidget.currentItem())

    def on_next_button_clicked(self):
        row = self.ui.fileListWidget.currentRow()
        total = self.ui.fileListWidget.count()
        if row < total - 1:
            self.ui.fileListWidget.setCurrentRow(row + 1)
            self.on_file_item_clicked(self.ui.fileListWidget.currentItem())

    def on_file_delete_button_clicked(self):
        item = self.ui.fileListWidget.currentItem()
        if not item:
            print("[WARN] No item selected")
            return

        sub = "train" if self.current_tab_index == 0 else "val"
        fname = item.text()
        img_path = os.path.join(self.current_directory, "images", sub, fname)
        label_path = os.path.join(self.current_directory, "labels", sub, os.path.splitext(fname)[0] + ".txt")

        reply = QMessageBox.question(
            self,
            "파일 삭제 확인",
            f"다음 파일을 삭제하시겠습니까?\n\n{img_path}\n{label_path}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted = False
            if os.path.exists(img_path):
                os.remove(img_path)
                deleted = True
            if os.path.exists(label_path):
                os.remove(label_path)
                deleted = True

            if deleted:
                print("[INFO] Files deleted")
                self.on_prev_button_clicked()
                self.refresh_file_list()

            else:
                QMessageBox.warning(self, "삭제 실패", "파일 삭제에 실패했습니다.")

    def on_new_class_button_clicked(self):
        new_class = self.ui.classNameEdit.text().strip().replace(",", "")
        if not new_class:
            return

        if new_class in self.class_names.values():
            QMessageBox.warning(self, "중복 경고", "이미 존재하는 클래스입니다.")
            return

        yaml_path = os.path.join(self.current_directory, "data.yaml")

        # yaml 없으면 생성
        if not os.path.exists(yaml_path):
            reply = QMessageBox.question(
                self,
                "data.yaml 없음",
                "data.yaml 파일이 존재하지 않습니다.\n새로 생성하시겠습니까?",
                QMessageBox.Yes | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                with open(yaml_path, 'w') as f:
                    f.write("train: images/train\nval: images/val\n\nnc: 0\nnames: []\n")
            else:
                return

        # 기존 내용 읽기
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # names 수정
        try:
            names_start = content.index('[')
            names_end = content.index(']', names_start)
            names_str = content[names_start + 1:names_end].strip()
            name_list = [name.strip(" '\"") for name in names_str.split(',') if name.strip()]
        except ValueError:
            QMessageBox.warning(self, "오류", "data.yaml 포맷이 잘못되었습니다.")
            return

        name_list.append(new_class)
        updated_names = ', '.join(f"'{n}'" for n in name_list)
        content = content[:names_start + 1] + updated_names + content[names_end:]

        # nc 수정
        import re
        nc_match = re.search(r"nc\s*:\s*(\d+)", content)
        if nc_match:
            nc_value = int(nc_match.group(1)) + 1
            content = re.sub(r"nc\s*:\s*\d+", f"nc: {nc_value}", content)
        else:
            QMessageBox.warning(self, "오류", "nc 항목을 찾을 수 없습니다.")
            return

        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)

        self.load_class_names(yaml_path)
        self.ui.classNameEdit.clear()


    def on_delete_class_button_clicked(self):
        item = self.ui.classListWidget.currentItem()
        if not item:
            return

        # 예: "2: person" → "person"
        text = item.text()
        if ':' not in text:
            QMessageBox.warning(self, "삭제 실패", "클래스 항목 형식이 잘못되었습니다.")
            return
        class_name = text.split(':', 1)[1].strip()

        yaml_path = os.path.join(self.current_directory, "data.yaml")
        if not os.path.exists(yaml_path):
            QMessageBox.warning(self, "오류", "data.yaml 파일이 존재하지 않습니다.")
            return

        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            names_start = content.index('[')
            names_end = content.index(']', names_start)
            names_str = content[names_start + 1:names_end].strip()
            name_list = [name.strip(" '\"") for name in names_str.split(',') if name.strip()]
        except ValueError:
            QMessageBox.warning(self, "오류", "data.yaml 포맷이 잘못되었습니다.")
            return

        if class_name not in name_list:
            QMessageBox.warning(self, "오류", f"{class_name} 클래스가 존재하지 않습니다.")
            return

        name_list.remove(class_name)
        updated_names = ', '.join(f"'{n}'" for n in name_list)
        content = content[:names_start + 1] + updated_names + content[names_end:]

        # nc 수정
        import re
        nc_match = re.search(r"nc\s*:\s*(\d+)", content)
        if nc_match:
            nc_value = max(0, int(nc_match.group(1)) - 1)
            content = re.sub(r"nc\s*:\s*\d+", f"nc: {nc_value}", content)

        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)

        self.load_class_names(yaml_path)

    def save_drawn_box(self, xc, yc, w, h):
        print(f"{xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
