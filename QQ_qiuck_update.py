
import random
import string
import threading
import time
import os
import sys

# ==========  USER CONFIG – EDIT HERE ONLY  ========== #
CFG = {
    "length"   : 8,                         # string length
    "charset"  : string.ascii_letters + string.digits,  # character pool
    "interval" : 0.1,                       # seconds between sends
    "exit_key" : "f8",                      # hotkey to quit
}
# ==================================================== #

exit_flag  = threading.Event()
pause_flag = threading.Event()

def random_string():
    return ''.join(random.choices(CFG["charset"], k=CFG["length"]))

def send_loop():
    while not exit_flag.is_set():
        if pause_flag.is_set():
            time.sleep(0.05)
            continue
        s = random_string()
        if sys.platform == "win32":
            import keyboard
            keyboard.write(s)
            keyboard.send("enter")
        else:
            os.system(f'echo "{s}" && xdotool key Return 2>/dev/null || echo')
        time.sleep(CFG["interval"])

def main():
    print("Script running.  Any key = pause/resume  F8 = exit")
    # backend pick
    if sys.platform == "win32":
        import keyboard
        keyboard.add_hotkey(CFG["exit_key"], lambda: exit_flag.set())
        keyboard.on_press(lambda _: pause_flag.set() if not pause_flag.is_set() else pause_flag.clear())
    else:
        from pynput import keyboard as pkeyboard
        def on_press(key):
            if key == pkeyboard.Key.f8:
                exit_flag.set()
            else:
                pause_flag.set() if not pause_flag.is_set() else pause_flag.clear()
        listener = pkeyboard.Listener(on_press=on_press)
        listener.start()

    sender = threading.Thread(target=send_loop, daemon=True)
    sender.start()
    exit_flag.wait()
    print("\nTerminated.")

if __name__ == "__main__":
    main()
