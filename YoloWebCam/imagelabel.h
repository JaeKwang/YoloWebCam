#pragma once

#include <QLabel>
#include <QMouseEvent>
#include <QPainter>

class ImageLabel : public QLabel
{
    Q_OBJECT

public:
    explicit ImageLabel(QWidget* parent = nullptr)
        : QLabel(parent), mouseX(-1), mouseY(-1), dragging(false)
    {
        setMouseTracking(true);
    }

signals:
    void boxCreated(QRectF box); // 🔥 드래그 끝나면 MainWindow로 알릴 신호

protected:
    void mousePressEvent(QMouseEvent* event) override
    {
        if (event->button() == Qt::LeftButton) {
            dragging = true;
            startPos = event->pos();
            currentPos = startPos;
            update();
        }
    }

    void mouseMoveEvent(QMouseEvent* event) override
    {
        mouseX = event->x();
        mouseY = event->y();
        if (dragging) {
            currentPos = event->pos();
        }
        update();
    }

    void mouseReleaseEvent(QMouseEvent* event) override
    {
        if (dragging && event->button() == Qt::LeftButton) {
            dragging = false;
            QRect rect = QRect(startPos, currentPos).normalized();
            if (rect.width() > 5 && rect.height() > 5) { // 너무 작은 박스는 무시
                emit boxCreated(rect); // 🔥 MainWindow로 신호 보낸다
            }
            update();
        }
    }

    void leaveEvent(QEvent* event) override
    {
        mouseX = -1;
        mouseY = -1;
        update();
        QLabel::leaveEvent(event);
    }

    void paintEvent(QPaintEvent* event) override
    {
        QLabel::paintEvent(event);

        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing);

        // 🔥 항상 그려지는 십자 구분선
        if (mouseX >= 0 && mouseY >= 0) {
            painter.setPen(QPen(QColor(150, 150, 150, 180), 1, Qt::DashLine));
            painter.drawLine(0, mouseY, width(), mouseY);
            painter.drawLine(mouseX, 0, mouseX, height());
        }

        // 🔥 현재 드래그 중인 박스
        if (dragging) {
            painter.setPen(QPen(Qt::red, 2, Qt::DashLine));
            QRect rect = QRect(startPos, currentPos).normalized();
            painter.drawRect(rect);
        }
    }

private:
    int mouseX;
    int mouseY;

    bool dragging;
    QPoint startPos;
    QPoint currentPos;
};
