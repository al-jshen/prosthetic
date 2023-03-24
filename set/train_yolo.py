from ultralytics import YOLO

model = YOLO("./yolov8n.pt")
model.train(data="./set.yaml", epochs=10, imgsz=(1920, 1080), cache=True)
model.export(format="onnx")
