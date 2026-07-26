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
from serial.tools import list_ports
import time
import threading
from ollama import chat
import subprocess
import pocketsphinx
from pathlib import Path
from PIL import Image
import json
import pickle
import tkinter as tk
import keyboard
from skimage.metrics import structural_similarity as ssim
import queue
from concurrent.futures import ThreadPoolExecutor

# libraries to install

from transformers import CLIPProcessor, CLIPModel

# classes created

from eye_animation import GIFPlayer
from face_greeting import load_db, get_face_embedding, get_similarity_score, associate_name_with_face, process_face, recognize_face

recognizer = Recognizer()

# load pretrained models

model = YOLO("yolov8n.pt")
embed_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

possible_labels = ["A photo of a screw", "A photo of a battery"]

cache_path = "output_frames/embedding_cache.pkl"
face_db_path = 'face_memory/face_db.pkl'
face_images_dir = 'face_memory/face_images'

name_db = {}

# boolean flags

hunting_mode = False
target_object = ""
camera_thread_running = False
face_detection_mode = False
object_found = False


state_lock = threading.Lock()


# global variables for face detecting loop

latest_face_embedding = None
pending_greeting = None
people_greeted_this_session = set()
face_state_lock = threading.Lock()


cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not os.path.exists('output_frames'):
    os.makedirs('output_frames')

frame_count = 0
frame_skip = 5
image_count = 0

# history of moves made

moves_made = []

# tk animation 

animation_player = None
root = None 


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

# arduino_port = recognize_arduino_port()
    
# arduino = serial.Serial(port="/dev/ttyACM0", baudrate=9600, timeout=0.1)

# def send_message_to_arduino(message):
#     arduino.write(bytes(message, 'utf-8'))
#     time.sleep(0.05)
#     data = arduino.readline().decode('utf-8').strip()
#     print(data)

def save_convo_to_json(user_input, response):
    convo = {
        "user_input": user_input,
        "response": response,
    }
    with open("conversation_history.json", "a") as f:
        json.dump(convo, f)
        f.write("\n")
        

recognizer = sr.Recognizer()


speech_executor = ThreadPoolExecutor(max_workers=1)

def speech_worker(text):
    engine = pyttsx3.init()
    engine.say(text)
    start_time = time.perf_counter()
    engine.runAndWait()
    end_time = time.perf_counter()
    del engine
    speaking_time = end_time - start_time
    return speaking_time
    # subprocess.run(["espeak", text])

def speak(text):
    # submit the worker without arguments; the worker reads from speech_queue
    future = speech_executor.submit(speech_worker, text)
    return future


# def explore_mode():
#     detected_walls = {}
#     data = arduino.readline().decode('utf-8').strip()
#     if data.startswith("distance"):
#         distance n= data
    
#     is_over = False

#     prompt = f"""

#     You are a robot navigatig in a room 

#     Look at your previous action, unless it is the first action you do.
#     The distance from an obstacle is {distance}

#     what should you do? 
#     Respond by either: forward, backward, left, or right

#     save your actions with an index, so it would be: 1forward, 2left, 3right, etc. 
#     """

#     messages = [
#         {
#             "role":"user",
#             "content": prompt
#         },
#     ]

#     response = chat(model="llama3.2:latest", messages=messages)
#     messages.append(response.message) # type: ignore
#     direction = response.message.content[1:] # type: ignore
#     moves_made.append(direction)
#     send_message_to_arduino(direction)

def send_speech_to_ollama(text):
    prompt = text 
    messages = [
        {
            "role": "user",
            "content": prompt
        },
    ]
    response = chat(model="llama3.2:latest", messages=messages)
    return response["message"]["content"]


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
    global latest_face_embedding, pending_greeting

    os.makedirs(f'output_frames/objects', exist_ok=True)
    os.makedirs(f'output_frames/faces', exist_ok=True)

    live_embedding = None
    
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

                face_crop = facial_area[y: y + h, x: x + w]

                if face_crop.size == 0:
                    return None
                cluster = process_face(face_crop, frame)
                if cluster is not None:
                    current_embed = cluster["embeddings"][-1]
                with state_lock:
                    latest_face_embedding = current_embed

                matching_name = recognize_face(current_embed)

                if matching_name:
                    with state_lock:
                        if matching_name not in people_greeted_this_session:
                            pending_greeting = matching_name 
                            people_greeted_this_session.add(name)
            

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

cam_thread_running = True
cam_thread = threading.Thread(target=camera_loop, args=(model,), daemon=True)
cam_thread.start()

def run_tk():
    global root, player
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    player = GIFPlayer(root, 'idle-animation.gif', 67, 500)
    root.mainloop()

def switch_animation(gif_name, frame_delay=67, loop_delay=500):
   root.after(0, lambda: player.switch_gif(gif_name, frame_delay, loop_delay))


tk_thread_running = True
tk_thread = threading.Thread(target=run_tk, daemon=True)
tk_thread.start()

command_list = ["youtube", "primal", "hello", "good", "forward", "good", "forward", "backward", "explore", "find", "I am"]

keyword_said = False 

while True:
    try:

        if keyboard.is_pressed('q'):
            break

        print("Listening...")

        with face_state_lock:
            greeding_name = pending_greeting
            pending_greeting = None


        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)

        print("Recognizing...")
        text = recognizer.recognize_google(audio).lower()

        # robot switches to thinking mode

        switch_animation('thinking-animation.gif', 67, 500)

        print(f"Heard: {text}")

        if "youtube" in text:
            print("Opening YouTube")
            webbrowser.open('https://www.youtube.com/')

        elif "primal" in text:
            print("Opening Primal")
            webbrowser.open('https://archive.org/details/primal-s-2-e-10/Primal+S1E2.mp4')

        elif "hello" in text:
            switch_animation('happy-animation.gif', 67, 500)
            future = speak("Hello how are you doing")
            speaking_time = future.result()
            switch_animation('idle-animation.gif', 67, 500)
           

        elif "good" in text:
            switch_animation('talking-animation.gif', 67, 500)
            future = speak("Very good. Glad to be at your service!")
            speaking_time = future.result()
            switch_animation('idle-animation.gif', 67, 500)

        elif "forward" in text:
            switch_animation('talking-animation.gif', 67, 500)
            future = speak("Ok. Moving forward now.")
            speaking_time = future.result()
            switch_animation('idle-animation.gif', 67, 500)
            # send_message_to_arduino("move forward")

        elif "backward" in text:
            switch_animation('talking-animation.gif', 67, 500)
            future = speak("Ok. Moving backward now")
            speaking_time = future.result()
            switch_animation('idle-animation.gif', 67, 500)
            # send_message_to_arduino("move backward")
        
        elif "explore" in text:
            switch_animation('talking-animation.gif', 67, 500)
            future = speak("Ok. It is my time to explore")
            speaking_time = future.result()
            switch_animation('idle-animation.gif', 67, 500)
            # explore_mode()

        elif "find" in text:
            speak("I got you")
            with state_lock:
                hunting_mode = True
                hook = "find the"
                detected_object = text.replace(hook, "")
                target_object = detected_object
            # if hunting_mode:
                # explore_mode()
        
        elif "i am" in text:
            name = text.split("i am", 1)[-1].strip()
            speak(f"nice to meet you {name}")

            if not name:
                speak("Sorry, I did not get that. Could you say it again?")
            else:
                with face_state_lock:
                    current_face_embedding = latest_face_embedding
                
                if current_face_embedding is None:
                    speak("Sorry, I cannot see your face right now.")
                else:
                    successful_naming = associate_name_with_face(current_face_embedding, name)

                    if successful_naming:
                        switch_animation('happy-animation.gif', 67, 500)
                        speak(f"nice to meet you {name}. I will remember you from now on!")
                        player.switch_gif('idle-animation.gif', 67, 500)
                    else:
                        speak("I could not recognize you, since your face does not match my memory. Please try doing a different pose")
        
        elif "healthy" in text:
            switch_animation('talking-animation.gif', 67, 500)
            future = speak("Yes")
            speaking_time = future.result()
            switch_animation('idle-animation.gif', 67, 500)
            # in the future: custom train for the word "kelpy" to be recognized
            keyword_said = True
        
        elif keyword_said:
            print("Waiting for prompt...")
            prompt = text.strip()
            response = send_speech_to_ollama(prompt)
            switch_animation('talking-animation.gif', 67, 500)
            future = speak(response)
            speaking_time = future.result()
            switch_animation('idle-animation.gif', 67, 500)
            keyword_said = False


    except sr.WaitTimeoutError:
        print("No speech detected")

    except sr.UnknownValueError:
        print("Could not understand audio")

    except sr.RequestError as e:
        print(f"API error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")

    time.sleep(0.3)

