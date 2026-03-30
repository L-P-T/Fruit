import cv2
import numpy as np
import win32api
import win32con
import threading
import time
import ctypes
import sys
import customtkinter as ctk
import bettercam
from ultralytics import YOLO
import multiprocessing as mp
from cutting_worker import slice_worker

ctypes.windll.shcore.SetProcessDpiAwareness(1)
if not ctypes.windll.shell32.IsUserAnAdmin():
    print("❌ SYSTEM ERROR: YOU MUST RUN AS ADMINISTRATOR!")
    time.sleep(5)
    sys.exit()

class FruitNinjaBot:
    def __init__(self):
        self.running = False
        self.model = YOLO(r'logs\runs\detect\train2\weights\best.onnx', task='detect')
        self.camera = bettercam.create()
        self.screen_w = win32api.GetSystemMetrics(0)
        self.screen_h = win32api.GetSystemMetrics(1)
        self.cut_queue = mp.Queue()
        self.cutter_process = mp.Process(target=slice_worker, args=(self.cut_queue,))
        self.cutter_process.start()
        self.cut_cooldown = 0.3
        print("✅ Bot Initialized and Ready!")

    def start_vision_loop(self):
        print("🚀 Vision Loop Started")
        last_cut_time = 0

        while self.running:
            frame = self.camera.grab()
            if frame is None:
                continue

            # Convert BGR to RGB for YOLO (lossless)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.model(frame_rgb, verbose=False, imgsz=320, conf=0.45)

            # Annotated image is RGB, convert back to BGR for OpenCV display
            annotated_rgb = results[0].plot()
            annotated_bgr = cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR)
            cv2.imshow("Fruit Ninja AI - Tracking View", cv2.resize(annotated_bgr, (640, 360)))
            cv2.waitKey(1)

            # Global ESC detection
            if win32api.GetAsyncKeyState(27) & 0x8000:
                print("⚠️ ESC pressed – stopping AI...")
                self.running = False
                break

            current_time = time.time()
            if current_time - last_cut_time >= self.cut_cooldown:
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        cls = int(box.cls[0])
                        if cls == 0 and box.conf[0] > 0.5:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            self.cut_queue.put((center_x, center_y))
                            last_cut_time = current_time
                            break
                    if current_time - last_cut_time < self.cut_cooldown:
                        break

        cv2.destroyAllWindows()

    def shutdown(self):
        self.running = False
        if self.cut_queue:
            self.cut_queue.put(None)
        if self.cutter_process and self.cutter_process.is_alive():
            self.cutter_process.join(timeout=1)
            if self.cutter_process.is_alive():
                self.cutter_process.terminate()

class BotGUI(ctk.CTk):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.title("Fruit Ninja AI - Ultra Slicer")
        self.geometry("350x380")
        self.attributes("-topmost", True)

        self.label = ctk.CTkLabel(self, text="AI Status: OFFLINE", font=("Arial", 18, "bold"), text_color="red")
        self.label.pack(pady=20)

        self.start_btn = ctk.CTkButton(self, text="START BOT", command=self.toggle_bot,
                                       fg_color="green", hover_color="darkgreen")
        self.start_btn.pack(pady=10, fill="x", padx=40)

        # Cooldown slider
        self.cooldown_slider = ctk.CTkSlider(self, from_=0.1, to=0.8, number_of_steps=7)
        self.cooldown_slider.set(0.3)
        self.cooldown_slider.pack(pady=10, padx=40, fill="x")
        self.cooldown_label = ctk.CTkLabel(self, text="Cut delay: 0.3s")
        self.cooldown_label.pack()
        self.cooldown_slider.configure(command=self.update_cooldown)

        # Color info label
        color_info = ctk.CTkLabel(self, text="Colors are original (BGR↔RGB conversion is lossless)",
                                  font=("Arial", 9), text_color="gray")
        color_info.pack(pady=(5,0))

        hint = ctk.CTkLabel(self, text="Press ESC (anywhere) to stop AI", font=("Arial", 12), text_color="gray")
        hint.pack(pady=(10, 5))

        self.bind('<Escape>', lambda e: self.stop_from_key())

        # Start monitoring bot status
        self.monitor_status()

    def update_cooldown(self, value):
        self.bot.cut_cooldown = value
        self.cooldown_label.configure(text=f"Cut delay: {value:.1f}s")

    def monitor_status(self):
        """Periodically check bot.running and update UI accordingly"""
        if not self.bot.running and self.label.cget("text") == "AI Status: ACTIVE":
            self.label.configure(text="AI Status: OFFLINE", text_color="red")
            self.start_btn.configure(text="START BOT", fg_color="green", hover_color="darkgreen")
        elif self.bot.running and self.label.cget("text") == "AI Status: OFFLINE":
            self.label.configure(text="AI Status: ACTIVE", text_color="green")
            self.start_btn.configure(text="STOP BOT", fg_color="red", hover_color="darkred")
        self.after(200, self.monitor_status)

    def stop_from_key(self):
        if self.bot.running:
            self.toggle_bot()   # this sets bot.running = False and stops threads

    def toggle_bot(self):
        if not self.bot.running:
            self.bot.running = True
            vision_thread = threading.Thread(target=self.bot.start_vision_loop, daemon=True)
            vision_thread.start()
        else:
            self.bot.running = False
            self.bot.shutdown()

    def on_closing(self):
        self.bot.shutdown()
        self.destroy()

if __name__ == "__main__":
    bot_instance = FruitNinjaBot()
    app = BotGUI(bot_instance)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()