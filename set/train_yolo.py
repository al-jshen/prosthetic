from ultralytics import YOLO

model = YOLO("./yolov8n.pt")
model.train(
    data="set.yaml", epochs=10, imgsz=1920, verbose=True, val=False, device="mps"
)
model.export(format="onnx")
