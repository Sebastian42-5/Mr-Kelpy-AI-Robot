import cv2
import torch
import os
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

try:
    while True:
        timer = cv2.getTickCount()
        fps = cap.get(cv2.CAP_PROP_FPS)
        ret, frame = cap.read()

        results = model(frame, stream=False)

        for r in results:
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            confidences = r.boxes.conf.cpu().numpy()

            for i in range(len(boxes)):
                x1, y1, x2, y2 = boxes[i]
                conf = confidences[i]
                cls = classes[i]

                if conf > 0.5:
                    class_name = model.names[cls]
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    cv2.putText(frame, f"{class_name} {conf:.2f}", (int(x1), int(y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2) 
                    cv2.imshow("Object Detection", frame) 

        if cv2.waitKey(1) and 0xff == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    del model


