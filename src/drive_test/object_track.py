import cv2

capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    success, img = capture.read()
    cv2.imshow("Tracking", img)

    if cv2.waitKey(1) and 0xff == ord("q"):
        break 

