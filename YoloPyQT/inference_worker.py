# inference_worker.py
import numpy as np
import cv2
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from ultralytics import YOLO

class InferenceWorker(QObject):
    inferenceCompleted = Signal(list)

    def __init__(self):
        super().__init__()
        self.model = None
        self.running = False

    def set_model(self, model_path: str):
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            print(f"[ERROR] 모델 로드 실패: {e}")

    def start_inference(self):
        self.running = True

    def stop_inference(self):
        self.running = False

    def infer(self, qimage: QImage):
        if not self.running:
            return
        
        if self.model is None:
            return

        qimage = qimage.convertToFormat(QImage.Format_RGB888)
        w, h = qimage.width(), qimage.height()
        ptr = qimage.bits()
        rgb = np.frombuffer(ptr, np.uint8).reshape((h, w, 3)).copy()
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        results = self.model(bgr, verbose=False)[0]
        boxes = []

        for det in results.boxes:
            conf = float(det.conf[0])
            x1, y1, x2, y2 = map(int, det.xyxy[0].tolist())
            cls_id = int(det.cls[0].item())
            label = self.model.names[cls_id]
            boxes.append((x1, y1, x2, y2, label, conf))

        self.inferenceCompleted.emit(boxes)
