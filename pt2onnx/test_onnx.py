import onnxruntime as ort
import cv2
import numpy as np

# 모델 경로와 이미지 경로
onnx_model_path = "best.onnx"
image_path = "test.jpg"  # 테스트할 이미지 경로로 변경하세요

# 모델 세션 로드
session = ort.InferenceSession(onnx_model_path)

# 입력 정보 추출
input_name = session.get_inputs()[0].name
input_shape = session.get_inputs()[0].shape

# 이미지 로딩 및 전처리 (BGR → RGB, 정규화, 640x640 리사이즈)
image = cv2.imread(image_path)
image_resized = cv2.resize(image, (640, 640))
image_rgb = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)
image_input = image_rgb.astype(np.float32) / 255.0  # [0, 1] 정규화
image_input = np.transpose(image_input, (2, 0, 1))   # HWC → CHW
image_input = np.expand_dims(image_input, axis=0)   # Add batch dim

# 추론 수행
outputs = session.run(None, {input_name: image_input})[0]  # shape: (1, 5, 8400)
outputs = outputs.squeeze().T                              # (8400, 5)

# 출력 후처리: 클래스별 confidence score threshold
conf_threshold = 0.25
boxes = outputs[outputs[:, 4] > conf_threshold]

# 바운딩 박스 시각화
for det in boxes:
    x, y, w, h, conf = det[:5]
    cx, cy = int(x * image.shape[1]), int(y * image.shape[0])
    box_w, box_h = int(w * image.shape[1]), int(h * image.shape[0])
    x1, y1 = cx - box_w // 2, cy - box_h // 2
    x2, y2 = cx + box_w // 2, cy + box_h // 2
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(image, f"{conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

# 결과 출력
cv2.imshow("ONNX YOLOv8 Result", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
