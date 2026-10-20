import serial, time
ard = serial.Serial("COM3", 9600, timeout=0.1)   # use your actual port
time.sleep(4)                                    # let it reboot and calibrate
ard.reset_input_buffer()
ard.write(b"TURN 90\n")
t = time.time()
while time.time() - t < 10:
    line = ard.readline().decode(errors="replace").strip()
    if line: print(line)