import mss
import cv2
import numpy as np

with mss.mss() as sct:
    # Capture the entire screen first
    monitor = sct.monitors[2]  # primary monitor
    while True:
        img = sct.grab(monitor)
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        cv2.imshow("MSS Capture - Full Screen", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
cv2.destroyAllWindows()