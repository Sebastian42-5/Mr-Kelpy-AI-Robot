import serial
import pyvolume
import time

serial = serial.Serial(port="COM6", baudrate=9600, timeout=0.1)


while True:
    packet = serial.readline()
    if packet:
        message = packet.decode('utf-8').strip()
        if message:
            print(message)
            desired_message = float(message)
            volume = int((100 * desired_message) / 675)
            pyvolume.custom(percent=30)




