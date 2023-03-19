import serial
import time
import numpy as np
import cv2
from ultralytics import YOLO

# with serial.Serial("/dev/cu.usbmodem3101", 9600, timeout=1) as ser:
#     time.sleep(2)
#     for i in range(100):
#         i, j = np.random.randint(1, 4, size=(2, 3)).astype(int)
#         print(f"{i},{j}")
#         # check that the random number pairs are not the same
#         if (
#             (i[0] == i[1] and j[0] == j[1])
#             or (i[0] == i[2] and j[0] == j[2])
#             or (i[1] == i[2] and j[1] == j[2])
#         ):
#             continue
#         ser.write(bytes(f"{i[0]},{j[0]}\n", "utf-8"))
#         ser.write(bytes(f"{i[1]},{j[1]}\n", "utf-8"))
#         ser.write(bytes(f"{i[2]},{j[2]}\n", "utf-8"))
#         time.sleep(0.2)
#         ser.write(bytes(f"{i[0]},{j[0]}\n", "utf-8"))
#         ser.write(bytes(f"{i[1]},{j[1]}\n", "utf-8"))
#         ser.write(bytes(f"{i[2]},{j[2]}\n", "utf-8"))
#         time.sleep(0.05)

yolo = YOLO("yolov8n.pt", task="detect")

cap = cv2.VideoCapture(1)

ctr = 0

while True:
    ret, frame = cap.read()
    res = yolo.predict(frame)
    res_plotted = res[0].plot()
    cv2.imshow("result", res_plotted)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        cv2.imwrite("test.png", res_plotted)
        break
    if ctr == 0:
        print(res)
    ctr += 1

cap.release()
cv2.destroyAllWindows()
