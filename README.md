# YoloCamDetector

YOLOv8을 활용하여 웹캠 실시간 사물 감지를 수행하는 Qt 기반 C++ 애플리케이션입니다.  
Python 서버를 통해 YOLOv8 모델을 로딩하고, C++ 클라이언트가 웹캠 이미지를 표시하며 결과를 받아 표시합니다.

## 📦 프로젝트 구조
/YoloWebCam
    ├── mainwindow.h
    ├── mainwindow.cpp
    ├── mainwindow.ui
    ├── resources/ (필요한 이미지 리소스)
├── .gitignore
├── README.md

## 🚀 설치 및 실행 방법

### 1. 필수 환경

- Ubuntu 20.04 이상
- Qt Creator 6.0.2 이상
- Qt 6.x 이상
- OpenCV 4.x (C++)
- Python 3.8 이상 (YOLOv8 서버용)
- Ultralytics (YOLOv8)

### 2. C++ 측 세팅

**OpenCV 설치 (필요 시)**

```bash
sudo apt update
sudo apt install libopencv-dev

# QT 다운로드
pip install PySide6
