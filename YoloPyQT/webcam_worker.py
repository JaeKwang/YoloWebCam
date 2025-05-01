import cv2
import sys
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QImage

class WebcamWorker(QObject):
    frameCaptured = Signal(QImage)

    def __init__(self):
        super().__init__()
        self.running = False
        self.cap = None

    def start(self):
        sys.stdout.flush()
        self.cap = cv2.VideoCapture(0)
        self.running = True

        if not self.cap.isOpened():
            print("[ERROR] Webcam could not be opened.")
            return False

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frameCaptured.emit(qimg)

    def stop(self):
        self.running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()


