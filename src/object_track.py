import cv2

capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
tracker = cv2.TrackerCSRT_create()
success, img = capture.read()
bbox = cv2.selectROI("Tracking", img, False)


while True:
    timer = cv2.getTickCount()
    fps = capture.get(cv2.CAP_PROP_FPS)
    success, img = capture.read()
    
    cv2.putText(img, str(int(fps)), (75, 50), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(img, 'hello', (25, 25), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 0, 0), 2)
    cv2.imshow("Tracking", img)

    if cv2.waitKey(1) and 0xff == ord("q"):
        break 

