import speech_recognition as sr
from speech_recognition import Recognizer
import pyttsx3
import webbrowser
import serial
import time
import traceback

recognizer = Recognizer()
engine = pyttsx3.init()
# arduino = serial.Serial(port='COM4', baudrate=9600, timeout=0.1)

# def send_message_to_arduino(message):
#     arduino.write(bytes(message, 'utf-8'))
#     time.sleep(0.05)
#     data = arduino.readline().decode('utf-8').strip()
#     print(data)

recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS error: {e}")

mic = sr.Microphone(device_index=2)

while True:
    try:
        print("🎤 Listening...")

        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)

        print("🧠 Recognizing...")
        text = recognizer.recognize_google(audio).lower()

        print(f"✅ Heard: {text}")

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

    except sr.WaitTimeoutError:
        print("⏳ No speech detected")

    except sr.UnknownValueError:
        print("❓ Could not understand audio")

    except sr.RequestError as e:
        print(f"🌐 API error: {e}")

    except Exception as e:
        print(f"🔥 Unexpected error: {e}")

    time.sleep(0.3)
