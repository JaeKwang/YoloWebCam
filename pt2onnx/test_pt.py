from ultralytics import YOLO

# 1. 모델 로드
model = YOLO("best.pt")  # 파일 경로는 적절히 수정

# 2. 예측 실행 (이미지 하나)
results = model.predict(source="test.jpg", save=True, conf=0.25)  # test.jpg → 실제 이미지 경로

# 3. 결과 출력
for result in results:
    print("감지된 객체 수:", len(result.boxes))
    for box in result.boxes:
        cls = int(box.cls[0])              # 클래스 인덱스
        conf = float(box.conf[0])          # 신뢰도
        xyxy = box.xyxy[0].tolist()        # 바운딩 박스 좌표 [x1, y1, x2, y2]
        print(f"Class: {cls}, Confidence: {conf:.2f}, BBox: {xyxy}")
