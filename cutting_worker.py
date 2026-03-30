# cutting_worker.py
import ctypes
import sys
import time
import win32api
import win32con
import multiprocessing as mp

def init_process():
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("❌ Cutting worker: Administrator rights required!")
        sys.exit(1)

def slice_worker(queue: mp.Queue):
    init_process()
    screen_w = win32api.GetSystemMetrics(0)
    screen_h = win32api.GetSystemMetrics(1)

    def move_mouse(x, y):
        nx = int(x / screen_w * 65535.0)
        ny = int(y / screen_h * 65535.0)
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, nx, ny, 0, 0)

    def slice_action(x, y):
        try:
            # 1. Start higher up for a "Long Distance" swipe
            start_y = y - 100  
            end_y = y + 100
        
            # Move to start and press down
            move_mouse(x, start_y)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        
            # 2. Fast Swipe with internal "Hold"
            # We use fewer steps to maintain speed, but a micro-sleep for the 'hold' effect
            steps = 5 
            dist_per_step = (end_y - start_y) // steps
        
            for i in range(1, steps + 1):
                current_y = start_y + (i * dist_per_step)
                move_mouse(x, current_y)
            
                # This creates the 'hold' effect during the swipe
                # Adjust 0.01 (10ms) to be longer if the game isn't registering the power
                time.sleep(0.01) 
        
            # 3. Release
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        except Exception as e:
            print(f"Slice error: {e}")

    print("✂️ Cutting worker ready (HOLD mode enabled)")
    while True:
        coords = queue.get()
        if coords is None:
            break
        x, y = coords
        slice_action(x, y)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        x, y = int(sys.argv[1]), int(sys.argv[2])
        q = mp.Queue()
        q.put((x, y))
        slice_worker(q)
    else:
        print("Usage: python cutting_worker.py <x> <y>")