import serial
import time
from pycaw.pycaw import AudioUtilities



serial = serial.Serial(port="COM6", baudrate=9600, timeout=0.1)

def set_volume(percentage):
   
    device = AudioUtilities.GetSpeakers()
    volume = device.EndpointVolume
    
    volume.SetMasterVolumeLevelScalar(percentage / 100, None)
    print(f"Volume set to {percentage}%")

if __name__ == "__main__":
    while True:
        packet = serial.readline()
        if packet:
            message = packet.decode('utf-8').strip()
            if message:
                print(message)
                desired_message = float(message)
                volume = int((100 * desired_message) / 675)
                set_volume(volume)




