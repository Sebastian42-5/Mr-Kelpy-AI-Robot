import speech_recognition as sr
from speech_recognition import Recognizer
import pocketsphinx
import pyttsx3
import webbrowser
import serial
import serial.tools.list_ports
import time
import traceback
import subprocess

recognizer = Recognizer()
engine = pyttsx3.init()

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

recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    subprocess.run(["espeak", text])
        
while True:
    try:
        print("Listening...")

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)

        print("🧠 Recognizing...")
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


    except sr.WaitTimeoutError:
        print("No speech detected")

    except sr.UnknownValueError:
        print("Could not understand audio")

    except sr.RequestError as e:
        print(f"API error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")

    time.sleep(0.3)
