import cv2
import torch
import os
from ultralytics import YOLO
from deepface import DeepFace
import speech_recognition as sr
from speech_recognition import Recognizer
import pyttsx3
import webbrowser
import serial
import time
import threading
from ollama import chat
import subprocess
import pocketsphinx
from pathlib import Path
from PIL import Image
import json
import pickle

# libraries to install

from transformers import CLIPProcessor, CLIPModel


recognizer = Recognizer()
engine = pyttsx3.init()

# load pretrained models

model = YOLO("yolov8n.pt")
embed_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

possible_labels = ["A photo of a screw", "A photo of a battery"]

cache_path = "output_frames/embedding_cache.pkl"

# boolean flags

hunting_mode = False
target_object = ""
camera_thread_running = False
face_detection_mode = False
object_found = False


state_lock = threading.Lock()

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not os.path.exists('output_frames'):
    os.makedirs('output_frames')

frame_count = 0
frame_skip = 5
image_count = 0

# history of moves made

moves_made = []


def recognize_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    keywords = ['arduino', 'ch340', 'ch341', 'ftdi', 'cp210', 'usb serial']

    for p in ports:
        if (p.description.lower() in keywords) or ((p.manufacturer or '').lower() in keywords):
            return p.device
    print("No arduino has been found")
    for p in ports:
        print(f"{p.device} - {p.description}")
    return None

arduino_port = recognize_arduino_port()
    
arduino = serial.Serial(port="/dev/ttyACM0", baudrate=9600, timeout=0.1)

def send_message_to_arduino(message):
    arduino.write(bytes(message, 'utf-8'))
    time.sleep(0.05)
    data = arduino.readline().decode('utf-8').strip()
    print(data)

def save_convo_to_json(user_input, response):
    convo = {
        "user_input": user_input,
        "response": response,
    }
    with open("conversation_history.json", "a") as f:
        json.dump(convo, f)
        f.write("\n")
        

recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    subprocess.run(["espeak", text])

def explore_mode():
    detected_walls = {}
    data = arduino.readline().decode('utf-8').strip()
    if data.startswith("distance"):
        distance = data
    
    is_over = False

    prompt = f"""

    You are a robot navigating in a room 

    Look at your previous action, unless it is the first action you do.
    The distance from an obstacle is {distance}

    what should you do? 
    Respond by either: forward, backward, left, or right

    save your actions with an index, so it would be: 1forward, 2left, 3right, etc. 
    """

    messages = [
        {
            "role":"user",
            "content": prompt
        },
    ]

    response = chat(model="llama3.2:latest", messages=messages)
    messages.append(response.message) # type: ignore
    direction = response.message.content[1:] # type: ignore
    moves_made.append(direction)
    send_message_to_arduino(direction)


# Automatically naming objects from images taken by the object_tracking model

def name_and_embed_saved_image(image_path):
    pil_image = Image.open(image_path).convert("RGB")
    text_inputs = processor(
        text=possible_labels, 
        images=pil_image, 
        return_tensors="pt", 
        padding=True
    )

    with torch.no_grad():
        outputs = embed_model(**text_inputs)

    logits = outputs.logits_per_image()
    probs = logits.softmax(dim=-1).squeeze(0)
    best_idx = probs.arg_max().item()
    best_label = possible_labels[best_idx].replace("a photo of a", "")
    best_confidence = probs[best_idx].item()

    print(f"detected {best_label} with a {best_confidence} confidence")

    # saving the image into the correct folder
    
    label_folder = f"output_frames/{best_label}"
    os.makedirs(label_folder)
    new_label = os.path.basename(image_path)
    new_image_path = os.path.join(label_folder, new_label)
    pil_image.save(image_path)

    # cache the embedding of the image

    embedding = get_image_embedding(pil_image)
    
    cache = load_cache()
    cache.append({
        "label": best_label,
        "image_path": new_image_path,
        "embedding": embedding,
        "confidence": best_confidence
    })

    save_cache(cache)

    print(f"Saved to {new_image_path} with a total of {len(cache)} total entries")

    return embedding, best_label


    
def get_image_embedding(pil_image):
    inputs = processor(images=pil_image, return_tensors="pt")
    with torch.no_grad():
        image_embedding = embed_model.get_image_features(**inputs)
        image_embedding = image_embedding / image_embedding.norm(p=2, dim=-1, keepdim=True)
    return image_embedding.squeeze(0)

def load_cache():
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            pickle.load(f)
    return []

def save_cache(cache):
    with open(cache_path, "wb") as f:
        pickle.dump(cache, f)

def find_best_match_in_database(live_frame_embedding, spoken_label=None):
    cache = load_cache()

    if not cache:
        print("Database is empty, keep exploring!")
        return None, 0.0

    best_score = -1
    best_label = "" 

    for entry in cache:
        if spoken_label and spoken_label.lower() not in entry["label"]:
            continue

        cached_embedding = entry["embedding"]
        score = torch.dot(live_frame_embedding, cached_embedding).item()

        if score > best_score:
            best_score = entry["confidence"]
            best_label = entry["label"]

    print(f"best match is: {best_label}, with a {best_score} similarity")
    return best_score, best_label



# creating a logic to embed images as numerical vectors to optimize image database search



def camera_loop(model):

    global frame_count, hunting_mode, target_object

    os.makedirs(f'output_frames/objects', exist_ok=True)
    os.makedirs(f'output_frames/faces', exist_ok=True)
    
    while camera_thread_running:
        timer = cv2.getTickCount()
        fps = cap.get(cv2.CAP_PROP_FPS)
        ret, frame = cap.read()

        frame_count += 1

        detected_faces = DeepFace.extract_faces(frame, detector_backend='opencv', enforce_detection=False)

        # face detection

        if len(detected_faces) > 0 and (frame_count % frame_skip == 0):
            print(f"faces detected: {len(detected_faces)}")
            for face_info in detected_faces:
                facial_area = face_info['facial_area'] # type: ignore
                x, y, w, h = face_info.get('x', 0), face_info.get('y', 0), face_info.get('w', 0), face_info.get('h', 0) # type: ignore
                cv2.rectangle(frame, (x, w), (y, h), (0, 0, 255), 2)
            cv2.imwrite(f"output_frames/faces_frame_{frame_count}.jpg", frame)   

        if frame_count % frame_skip == 0:
            image_dir = f"output_frames/object/frame_{frame_count}.jpg"
            file_path = Path(image_dir)
            cv2.imwrite(image_dir, frame)
            live_embedding, detected_label = name_and_embed_saved_image(image_dir)

        if hunting_mode and target_object:
            best_label, best_score = find_best_match_in_database(live_embedding, spoken_label=target_object)

            if best_score >= 0.85: # type: ignore
                hunting_mode = False
                speak(f"I found the {target_object}")
                target_object = ""

        

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
    cap.release()
    cv2.destroyAllWindows()


# Train the model (this might take time, consider if needed)
# model.train(data="data.yaml", epochs=100, imgsz=640, batch=16, device=0)

cam_thread = threading.Thread(target=camera_loop)
cam_thread.start()


while True:
    try:
        print("🎤 Listening...")

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)

        print("Recognizing...")
        text = recognizer.recognize_sphinx(audio).lower()

        print(f"Heard: {text}")

        if "youtube" in text:
            print("Opening YouTube")
            webbrowser.open('https://www.youtube.com/')

        elif "primal" in text:
            print("Opening Primal")
            webbrowser.open('https://archive.org/details/primal-s-2-e-10/Primal+S1E2.mp4')

        elif "hello" in text:
            speak("Hello how are you doing")

        elif "good" in text:
            speak("Very good. Glad to be at your service!")

        elif "forward" in text:
            speak("Ok. Moving forward now.")
            send_message_to_arduino("move forward")
        elif "backward" in text:
            speak("Ok. Moving backward now")
            send_message_to_arduino("move backward")
        
        elif "explore" in text:
            speak("Ok. It is my time to explore")
            explore_mode()

        elif "find" in text:
            speak("I got you")
            with state_lock:
                hunting_mode = True
                hook = "find the"
                detected_object = text.replace(hook, "")
                target_object = detected_object
            if hunting_mode:
                explore_mode()

    except sr.WaitTimeoutError:
        print("No speech detected")

    except sr.UnknownValueError:
        print("Could not understand audio")

    except sr.RequestError as e:
        print(f"API error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")

    time.sleep(0.3)

