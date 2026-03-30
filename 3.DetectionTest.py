import mss
import cv2
import numpy as np
from ultralytics import YOLO

# REPLACE with your actual region from Step 2: (left, top, width, height)
GAME_REGION = {"top": 0, "left": 0, "width": 1920, "height": 1080}

model = YOLO("C:/Users/linph/OneDrive/Desktop/Bachalor/Element 2/Element 2 Project Code and Documentation (Leader)/Complete bot/weights/best.pt")   # <-- UPDATE THIS

with mss.mss() as sct:
    while True:
        img = sct.grab(GAME_REGION)
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        # Run detection
        results = model(frame, conf=0.3)
        annotated = results[0].plot()
        
        cv2.imshow("Fruit Ninja Detection Test", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
