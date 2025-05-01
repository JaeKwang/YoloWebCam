from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QPainter, QPen
from PySide6.QtCore import Qt

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap_data = None
        self.boxes = []

    def setImage(self, pixmap: QPixmap, boxes=None):
        self.pixmap_data = pixmap
        self.boxes = boxes if boxes else []
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.pixmap_data:
            painter = QPainter(self)
            scaled = self.pixmap_data.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

            # 바운딩 박스도 동일 비율로 오버레이
            if self.boxes:
                scale_x = scaled.width() / self.pixmap_data.width()
                scale_y = scaled.height() / self.pixmap_data.height()

                for x1, y1, x2, y2, label, conf in self.boxes:
                    bx1 = int(x + x1 * scale_x)
                    by1 = int(y + y1 * scale_y)
                    bx2 = int(x + x2 * scale_x)
                    by2 = int(y + y2 * scale_y)
                    painter.setPen(QPen(Qt.red, 2))
                    painter.drawRect(bx1, by1, bx2 - bx1, by2 - by1)
                    if label:
                        painter.setPen(QPen(Qt.green, 2))
                        painter.drawText(bx1 + 4, by1 + 16, f"{label} [{conf:.2f}]")
