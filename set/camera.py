import time
import playsound
import numpy as np
import cv2
from ultralytics import YOLO
import set as st

yolo = YOLO("yolov8m-640.onnx", task="detect")

cap = cv2.VideoCapture(1)

ctr = 0

while True:
    ret, frame = cap.read()
    res = yolo.predict(frame, imgsz=640)
    res_plotted = res[0].plot()
    cv2.imshow("result", res_plotted)
    if cv2.waitKey(1) & 0xFF == ord("s"):
        cv2.imwrite(f"test-{np.random.randint(10000000)}.png", res_plotted)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    if ctr == 0:
        print(res)
    boxes = res[0].boxes.boxes
    mask = boxes[:, 4] > 0.5
    boxes = boxes[mask]
    classes = boxes[:, -1]
    cards = [st.mapping[int(c)] for c in classes]
    print(cards)
    sts = st.find_sets(cards)
    if len(sts) > 0:
        chaosflag = set([s[0] for s in sts])
        if 1 in chaosflag:
            playsound.playsound("set_lindsay.mp3", True)
            playsound.playsound("chaos_lindsay.mp3", False)
        else:
            playsound.playsound("set_lindsay.mp3", False)
        print(sts)
        time.sleep(1)
    ctr += 1

cap.release()
cv2.destroyAllWindows()
