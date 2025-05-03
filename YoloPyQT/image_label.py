from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QPainter, QPen, QMouseEvent
from PySide6.QtCore import Qt, QRect, QPoint, Signal

class ImageLabel(QLabel):
    rectDrawn = Signal(float, float, float, float)  # xc, yc, w, h

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap_data = None
        self.boxes = []
        self.drawing = False
        self.start_pos = None
        self.end_pos = None
        self.mouse_pos = None
        self.setMouseTracking(True)
        self.setMinimumSize(640, 480)

    def setImage(self, pixmap: QPixmap, boxes=None):
        self.pixmap_data = pixmap
        self.boxes = boxes if boxes else []
        self.update()

    def get_scaled_geometry(self):
        """이미지가 QLabel 내에 그려지는 위치와 크기 반환"""
        if not self.pixmap_data:
            return 0, 0, 0, 0
        scaled = self.pixmap_data.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        return x, y, scaled.width(), scaled.height()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.pixmap_data:
            return

        painter = QPainter(self)
        x, y, w, h = self.get_scaled_geometry()
        scaled = self.pixmap_data.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(x, y, scaled)

        # 기존 바운딩 박스 그리기
        if self.boxes:
            scale_x = w / self.pixmap_data.width()
            scale_y = h / self.pixmap_data.height()
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

        # 드래그 중 실시간 박스
        if self.drawing and self.start_pos and self.end_pos:
            temp_rect = QRect(self.start_pos, self.end_pos)
            temp_rect = temp_rect.normalized()
            image_area = QRect(x, y, w, h)
            temp_rect = temp_rect.intersected(image_area)
            painter.setPen(QPen(Qt.green, 2, Qt.DashLine))
            painter.drawRect(temp_rect)

        # 마우스 오버 가이드 선
        if self.mouse_pos:
            painter.setPen(QPen(Qt.red, 1, Qt.DotLine))
            painter.drawLine(self.mouse_pos.x(), 0, self.mouse_pos.x(), self.height())
            painter.drawLine(0, self.mouse_pos.y(), self.width(), self.mouse_pos.y())

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        if not self.pixmap_data:
            return

        scaled = self.pixmap_data.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        offset_x = (self.width() - scaled.width()) // 2
        offset_y = (self.height() - scaled.height()) // 2

        # 이미지 경계 내 좌표로 clamp
        x = max(offset_x, min(event.pos().x(), offset_x + scaled.width() - 1))
        y = max(offset_y, min(event.pos().y(), offset_y + scaled.height() - 1))

        self.drawing = True
        self.start_pos = QPoint(x, y)
        self.end_pos = self.start_pos
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        self.mouse_pos = event.pos()
        if self.drawing:
            self.end_pos = event.pos()
            self.update()
        else:
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.drawing and self.start_pos and self.end_pos:
            x, y, w, h = self.get_scaled_geometry()
            rect = QRect(self.start_pos, self.end_pos).normalized()
            rect = rect.intersected(QRect(x, y, w, h))

            scaled = self.pixmap_data.scaled(self.size(), Qt.KeepAspectRatio)
            offset_x = (self.width() - scaled.width()) // 2
            offset_y = (self.height() - scaled.height()) // 2

            img_w = self.pixmap_data.width()
            img_h = self.pixmap_data.height()
            scale_x = img_w / scaled.width()
            scale_y = img_h / scaled.height()

            x1 = (rect.left() - offset_x) * scale_x
            y1 = (rect.top() - offset_y) * scale_y
            x2 = (rect.right() - offset_x) * scale_x
            y2 = (rect.bottom() - offset_y) * scale_y

            xc = (x1 + x2) / 2 / img_w
            yc = (y1 + y2) / 2 / img_h
            w = (x2 - x1) / img_w
            h = (y2 - y1) / img_h

            self.rectDrawn.emit(xc, yc, w, h)

        self.drawing = False
        self.start_pos = None
        self.end_pos = None
        self.update()

    def leaveEvent(self, event):
        self.mouse_pos = None
        self.update()
