import tkinter as tk
from tkinter import ttk
import threading
import time
import cv2
import numpy as np
import mss
from ultralytics import YOLO
from pynput import keyboard, mouse as pynput_mouse

# ================= CONFIGURATION =================
MODEL_PATH = "C:/Users/linph/OneDrive/Desktop/Bachalor/M SOT SDP Assignment - LIN PHONE THANT/Element 1/Element 2 Project Code and Documentation (Leader)/Complete bot/weights/best.pt"    # UPDATE
GAME_REGION = {"top": 0, "left": 0, "width": 1920, "height": 1080}  # UPDATE
HOTKEY = '<f2>'
CONF_THRESHOLD = 0.5
FRUIT_CLASS_ID = 0   # because model.names shows {0:'fruit',1:'bomb',2:'token'}

# ================= BOT CLASS =================
class FruitBot:
    def __init__(self, model_path, region):
        self.model = YOLO(model_path)
        self.region = region          # will be used later in the thread
        self.running = False
        self.mouse = pynput_mouse.Controller()
        print("Model loaded. Classes:", self.model.names)

    def capture_frame(self, sct):
        """Capture one frame using the passed mss instance"""
        img = sct.grab(self.region)
        return cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)

    def detect(self, frame):
        results = self.model(frame, conf=CONF_THRESHOLD, verbose=False)
        detections = []
        if results[0].boxes:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                detections.append((x1, y1, x2, y2, conf, cls))
        # Annotated frame for display
        annotated = results[0].plot() if detections else frame
        return detections, annotated

    def slice(self, detections):
        fruits = [d for d in detections if d[5] == FRUIT_CLASS_ID]
        if not fruits:
            return
        # Average center of fruits (relative to capture region)
        cx = sum((d[0]+d[2])//2 for d in fruits) // len(fruits)
        cy = sum((d[1]+d[3])//2 for d in fruits) // len(fruits)
        # Convert to absolute screen coordinates
        abs_x = self.region["left"] + cx
        abs_y = self.region["top"] + cy

        # Perform the swipe
        self.mouse.position = (abs_x - 150, abs_y - 100)
        time.sleep(0.02)
        self.mouse.press(pynput_mouse.Button.left)
        time.sleep(0.05)
        self.mouse.position = (abs_x + 150, abs_y + 100)
        time.sleep(0.05)
        self.mouse.release(pynput_mouse.Button.left)
        print(f"Sliced at ({abs_x}, {abs_y}) – {len(fruits)} fruits")
        time.sleep(0.1)

    def run(self):
        # Create a NEW mss instance inside the thread
        with mss.mss() as sct:
            cv2.namedWindow("Fruit Ninja AI", cv2.WINDOW_NORMAL)
            self.running = True
            while self.running:
                frame = self.capture_frame(sct)
                detections, annotated = self.detect(frame)
                cv2.imshow("Fruit Ninja AI", annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    break
                if detections:
                    self.slice(detections)
            cv2.destroyWindow("Fruit Ninja AI")

# ================= GUI =================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Fruit Ninja AI Bot")
        self.root.geometry("400x250")
        self.bot = FruitBot(MODEL_PATH, GAME_REGION)
        self.bot_thread = None

        main = ttk.Frame(root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main, text="Fruit Ninja AI", font=('Arial',14,'bold')).pack()
        self.status = tk.StringVar(value="Status: Stopped")
        ttk.Label(main, textvariable=self.status).pack(pady=5)

        # Confidence slider
        frm = ttk.Frame(main)
        frm.pack(pady=10, fill=tk.X)
        ttk.Label(frm, text="Confidence:").pack(side=tk.LEFT)
        self.slider = ttk.Scale(frm, from_=0.1, to=0.9, orient=tk.HORIZONTAL, value=CONF_THRESHOLD)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.slider.configure(command=self.update_conf)
        self.conf_label = ttk.Label(frm, text=f"{CONF_THRESHOLD:.2f}")
        self.conf_label.pack(side=tk.LEFT)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=15)
        self.start_btn = ttk.Button(btn_frame, text="Start Bot", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="Stop Bot", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Label(main, text=f"Hotkey: {HOTKEY.upper()}").pack()
        self.setup_hotkey()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_conf(self, val):
        global CONF_THRESHOLD
        CONF_THRESHOLD = float(val)
        self.conf_label.config(text=f"{CONF_THRESHOLD:.2f}")

    def setup_hotkey(self):
        def on_activate():
            if self.bot.running:
                self.stop()
            else:
                self.start()
        self.listener = keyboard.GlobalHotKeys({HOTKEY: on_activate})
        self.listener.start()

    def start(self):
        if self.bot.running:
            return
        self.bot.running = True
        self.bot_thread = threading.Thread(target=self.bot.run, daemon=True)
        self.bot_thread.start()
        self.status.set("Status: RUNNING")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop(self):
        if not self.bot.running:
            return
        self.bot.running = False
        self.status.set("Status: Stopped")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def on_close(self):
        self.stop()
        if hasattr(self, 'listener'):
            self.listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()