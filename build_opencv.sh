#!/bin/bash

sudo apt install qtbase5-dev libv4l-dev

# ✅ OpenCV 버전 설정
OPENCV_VERSION=4.8.1

# ✅ 설치 디렉토리
INSTALL_DIR=/usr/local

echo "🔥 OpenCV $OPENCV_VERSION 빌드 시작!"

# ✅ 필요한 패키지 설치
sudo apt update
sudo apt install -y build-essential cmake git pkg-config \
    libjpeg-dev libpng-dev libtiff-dev \
    libavcodec-dev libavformat-dev libswscale-dev \
    libv4l-dev libxvidcore-dev libx264-dev \
    libgtk-3-dev libatlas-base-dev gfortran python3-dev

# ✅ 기존 설치 제거
sudo apt remove -y libopencv-dev python3-opencv

# ✅ 소스 다운로드
cd ~
rm -rf opencv opencv_contrib
git clone -b ${OPENCV_VERSION} https://github.com/opencv/opencv.git
git clone -b ${OPENCV_VERSION} https://github.com/opencv/opencv_contrib.git

# ✅ 빌드 디렉토리 생성
cd opencv
mkdir -p build
cd build

# ✅ CMake 설정
cmake .. \
  -D CMAKE_BUILD_TYPE=Release \
  -D CMAKE_INSTALL_PREFIX=/usr/local \
  -D OPENCV_GENERATE_PKGCONFIG=ON \
  -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
  -D BUILD_opencv_python3=ON \
  -D BUILD_opencv_dnn=ON \
  -D WITH_OPENGL=ON \
  -D WITH_QT=ON \
  -D WITH_CUDA=OFF \
  -D OPENCV_DNN_CUDA=OFF \
  -D ENABLE_FAST_MATH=1 \
  -D WITH_CUBLAS=1



# ✅ 빌드 시작
make -j$(nproc)

# ✅ 설치
sudo make install
sudo ldconfig

echo "✅ OpenCV $OPENCV_VERSION 설치 완료!"

# ✅ 실행 방법
# chmod +x build_opencv.sh
# ./build_opencv.sh

