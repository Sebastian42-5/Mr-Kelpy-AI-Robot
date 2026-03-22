import cv2
import torch
import os
from ultralytics import YOLO
from deepface import DeepFace

# I would have to add the logic such that when Mr Kelpy sees an object and you tell him to grab it, he will align with the object using a draw box
# around his claw and align it 

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not os.path.exists('output_frames'):
    os.makedirs('output_frames')

frame_count = 0
frame_skip = 5
image_count = 0

current_object = 'battery'

os.makedirs(f'output_frames/{current_object}', exist_ok=True)
os.makedirs(f'output_frames/faces', exist_ok=True)

model.train(data="data.yaml", epochs=100, imgsz=640, batch=16, device=0)


try:
    while True:
        timer = cv2.getTickCount()
        fps = cap.get(cv2.CAP_PROP_FPS)
        ret, frame = cap.read()

        frame_count += 1

        detected_faces = DeepFace.extract_faces(frame, detector_backend='opencv', enforce_detection=False)

        if len(detected_faces) > 0 and (frame_count % frame_skip == 0):
            print(f"faces detected: {len(detected_faces)}")
            for face_info in detected_faces:
                facial_area = face_info['facial_area'] # type: ignore
                x, y, w, h = face_info.get('x', 0), face_info.get('y', 0), face_info.get('w', 0), face_info.get('h', 0) # type: ignore
                cv2.rectangle(frame, (x, w), (y, h), (0, 0, 255), 2)
            cv2.imwrite(f"output_frames/faces_frame_{frame_count}.jpg", frame)


        if frame_count % frame_skip == 0:
            cv2.imwrite(f"output_frames/{current_object}_frame_{frame_count}.jpg", frame)

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
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    cv2.imshow("Object Detection", frame) 
        x3, y3, x4, y4 = 100, 0, 300, 100
        claw_center_x = (x3 + x4) // 2
        claw_center_y = (y3 + y4) // 2
        cv2.rectangle(frame, (x3, y3), (x4, y4), (255, 0, 0), 2)


        if cv2.waitKey(1) and 0xff == ord("q"):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    del model


