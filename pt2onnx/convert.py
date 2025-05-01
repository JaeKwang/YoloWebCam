# python3 -m pip install ultralytics
# pip install numpy==1.26.4

from ultralytics import YOLO
model = YOLO("best.pt")
model.export(format="onnx", dynamic=True, simplify=True, opset=12)

