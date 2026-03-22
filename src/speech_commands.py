import speech_recognition
from speech_recognition import Recognizer
import pyttsx3
import webbrowser
import serial
import time

recognizer = Recognizer()
engine = pyttsx3.init()
arduino = serial.Serial(port='COM4', baudrate=9600, timeout=0.1)

def send_message_to_arduino(message):
    arduino.write(bytes(message, 'utf-8'))
    time.sleep(0.05)
    data = arduino.readline().decode('utf-8').strip()
    print(data)

while True:
    try:
        with speech_recognition.Microphone() as mic:
            recognizer.adjust_for_ambient_noise(mic, duration=0.2)
            audio = recognizer.listen(mic)

            text = recognizer.recognize_google(audio)

            if text.lower() == 'open youtube':
                webbrowser.open('https://www.youtube.com/')
            elif text.lower() == 'primal time':
                webbrowser.open('https://archive.org/details/primal-s-2-e-10/Primal+S1E2.mp4')
            elif text.lower() == 'hello':
                engine.say('Hello how are you doing')
                engine.runAndWait()
            elif text.lower() == 'good and you':
                engine.say('very good. Glad to be at your service!')
            elif text.lower() == 'turn around':
                engine.say('ok. Will do.')
                send_message_to_arduino(text.lower())

            print(f"Text Recognized: {text}")

    except Exception as E:
        print(f"error: {E}")
