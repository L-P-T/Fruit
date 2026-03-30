from pynput.mouse import Listener

positions = []
#Click Left Top and Right Bottom
def on_click(x, y, button, pressed):
    if pressed:
        positions.append((x, y))
        print(f"Clicked at ({x}, {y})")
        if len(positions) == 2:
            print(f"Region = ({positions[0][0]}, {positions[0][1]}, {positions[1][0]-positions[0][0]}, {positions[1][1]-positions[0][1]})")
            return False  # stop listener

with Listener(on_click=on_click) as listener:
    listener.join()