#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# QQ_quick_update_gui.py by afatcat-xie

import random
import string
import threading
import time as _time
import ctypes
import ctypes.wintypes
import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import os
import configparser
import sys
from datetime import datetime, timezone
import traceback
import signal
from PIL import Image
import pystray

# ---------- Global variables ----------
running = False
worker_thread = None
time_interval = 1.0          
qq_exists = False            
lock = threading.Lock()      
log_lock = threading.Lock()  
run_duration = None          
start_time = None            
send_with_ctrl = False       
root = None                  
tray_icon = None             

# ---------- File & Path Config ----------
INI_FILE = "qq_config.ini"
ICON_FILE = "icon.ico"  
LOG_DIR = "logs"

# Dynamically generate log filename based on UTC time
# Format: logs/qq_monitor_YYYYMMDD_HHMMSS_UTC.log
utc_now = datetime.now(timezone.utc)
log_filename = f"qq_monitor_{utc_now.strftime('%Y%m%d_%H%M%S')}_UTC.log"
LOG_FILE = os.path.join(LOG_DIR, log_filename)

TOGGLE_HOTKEY = "ctrl+alt+q"
STOP_HOTKEY = "f8"

log_fp = None

def log_info(message):
    """
    Thread-safe logging: ensures messages are line-broken and conflict-free 
    under multi-threading.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] [INFO] {message}"
    
    with log_lock:
        print(formatted_message)
        if log_fp:
            log_fp.write(formatted_message + "\n")
            log_fp.flush()

def log_error(message):
    """
    Thread-safe error logging: ensures error messages are written atomically 
    without interleaving.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] [ERROR] {message}"
    
    with log_lock:
        print(formatted_message, file=sys.stderr)
        if log_fp:
            log_fp.write(formatted_message + "\n")
            log_fp.flush()

def perform_cleanup(reason="Unknown"):
    """
    Closes resources and handles final logging before exit.
    """
    global log_fp
    log_info(f"Program exiting. Reason: {reason}")
    if log_fp:
        log_fp.close()
        log_fp = None

def quit_app():
    """
    Completely exit the program (Graceful exit).
    """
    global running, tray_icon
    running = False
    if tray_icon:
        tray_icon.stop()
    perform_cleanup("User requested exit")
    os._exit(0)

def show_window(icon=None, item=None):
    """
    Restore window from tray.
    """
    if root:
        root.after(0, root.deiconify)
        root.after(0, root.lift)
        root.after(0, root.focus_force)

def hide_to_tray():
    """
    Hide the window to the system tray.
    """
    root.withdraw()
    log_info("Window minimized to tray.")

def load_icon_image():
    """
    Load local ICO icon with a fallback color square if missing.
    """
    try:
        if os.path.exists(ICON_FILE):
            return Image.open(ICON_FILE)
        else:
            return Image.new('RGB', (64, 64), (0, 120, 215)) # Default Blue
    except Exception:
        return Image.new('RGB', (64, 64), (200, 0, 0)) # Error Red

def setup_tray():
    """
    System tray initialization and event loop.
    """
    global tray_icon
    menu = pystray.Menu(
        pystray.MenuItem('Show Window', show_window, default=True),
        pystray.MenuItem('Exit Program', quit_app)
    )
    tray_icon = pystray.Icon("QQTool", load_icon_image(), "QQ Quick Update", menu)
    tray_icon.run()

def handle_signal(signum, frame):
    quit_app()

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    err_detail = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_error(f"Unhandled exception occurred:\n{err_detail}")
    quit_app()

sys.excepthook = handle_exception

def load_config():
    global time_interval, run_duration, send_with_ctrl
    config = configparser.ConfigParser()
    if os.path.exists(INI_FILE):
        try:
            config.read(INI_FILE)
            if 'Settings' in config:
                time_interval = config.getfloat('Settings', 'interval', fallback=1.0)
                duration_str = config.get('Settings', 'duration', fallback='unlimited')
                send_with_ctrl = config.getboolean('Settings', 'send_with_ctrl', fallback=False)
                run_duration = None if duration_str.lower() in ['0', 'unlimited', 'inf'] else float(duration_str)
            log_info("Configuration loaded.")
        except Exception as e:
            log_error(f"Error loading config: {e}")

def save_config():
    config = configparser.ConfigParser()
    config['Settings'] = {
        'interval': str(time_interval),
        'duration': 'unlimited' if run_duration is None else str(run_duration),
        'send_with_ctrl': str(send_with_ctrl)
    }
    try:
        with open(INI_FILE, 'w') as configfile:
            config.write(configfile)
    except Exception as e:
        log_error(f"Error saving config: {e}")

def is_qq_running():
    process_name = "QQ.exe"
    TH32CS_SNAPPROCESS = 0x00000002
    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [("dwSize", ctypes.wintypes.DWORD), ("cntUsage", ctypes.wintypes.DWORD),
                    ("th32ProcessID", ctypes.wintypes.DWORD), ("th32DefaultHeapID", ctypes.POINTER(ctypes.wintypes.ULONG)),
                    ("th32ModuleID", ctypes.wintypes.DWORD), ("cntThreads", ctypes.wintypes.DWORD),
                    ("th32ParentProcessID", ctypes.wintypes.DWORD), ("pcPriClassBase", ctypes.wintypes.LONG),
                    ("dwFlags", ctypes.wintypes.DWORD), ("szExeFile", ctypes.c_char * 260)]
    snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == -1: return False
    try:
        pe = PROCESSENTRY32()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
        if ctypes.windll.kernel32.Process32First(snapshot, ctypes.byref(pe)):
            while True:
                if pe.szExeFile.decode('gbk').lower() == process_name.lower(): return True
                if not ctypes.windll.kernel32.Process32Next(snapshot, ctypes.byref(pe)): break
    finally:
        ctypes.windll.kernel32.CloseHandle(snapshot)
    return False

def monitor_qq():
    global qq_exists
    while True:
        exists = is_qq_running()
        with lock: qq_exists = exists
        _time.sleep(2)

def generate_random_string(length=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def worker():
    global running, start_time
    start_time = _time.time()
    send_key = 'ctrl+enter' if send_with_ctrl else 'enter'
    try:
        while running:
            with lock:
                if not qq_exists:
                    stop_sending("QQ closed unexpectedly")
                    break
            if run_duration and (_time.time() - start_time >= run_duration):
                stop_sending("Duration reached")
                break
            
            keyboard.write(generate_random_string())
            keyboard.press_and_release(send_key)
            _time.sleep(time_interval)
    except Exception as e:
        log_error(f"Worker execution error: {e}")
        stop_sending("Worker Thread Exception")

def start_sending():
    """
    Attempts to start the task. Updates status automatically on failure.
    """
    global running, worker_thread
    if not running:
        with lock:
            if not qq_exists:
                stop_sending("QQ not running")
                return
        
        running = True
        worker_thread = threading.Thread(target=worker, daemon=True)
        worker_thread.start()
        if 'status_label' in globals(): 
            status_label.config(text="Status: Running", fg="green")
        log_info("Sending task started.")

def stop_sending(reason="User stopped"):
    """
    Stops task and updates the GUI with the specific reason.
    """
    global running
    if running or 'status_label' in globals():
        running = False
        display_text = f"Status: Stopped ({reason})"
        if 'status_label' in globals():
            # Use Red for failures, Blue for normal stops
            status_color = "red" if "not" in reason.lower() or "unexpected" in reason.lower() else "blue"
            status_label.config(text=display_text, fg=status_color)
        log_info(f"Sending task stopped. Reason: {reason}")

def toggle_sending():
    stop_sending() if running else start_sending()

keyboard.add_hotkey(TOGGLE_HOTKEY, toggle_sending)
keyboard.add_hotkey(STOP_HOTKEY, lambda: stop_sending("F8 hotkey"))

def start_gui():
    global status_label, log_fp, send_with_ctrl, root
    
    # Ensure log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Open the unique UTC log file in append mode
    try:
        log_fp = open(LOG_FILE, "a", encoding="utf-8")
    except Exception as e:
        print(f"CRITICAL: Failed to open log file {LOG_FILE}: {e}")
    
    load_config()

    root = tk.Tk()
    root.title("QQ Quick Update Tool")
    
    if os.path.exists(ICON_FILE):
        try: root.iconbitmap(ICON_FILE)
        except: pass

    tk.Label(root, text="Interval (s):").grid(row=0, column=0, padx=10, pady=5, sticky="e")
    interval_var = tk.DoubleVar(value=time_interval)
    ttk.Spinbox(root, from_=0.1, to=3600.0, increment=0.1, textvariable=interval_var, width=10).grid(row=0, column=1, padx=10, pady=5)

    tk.Label(root, text="Duration (s, 0=inf):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    duration_var = tk.StringVar(value='unlimited' if run_duration is None else str(run_duration))
    ttk.Entry(root, textvariable=duration_var, width=12).grid(row=1, column=1, padx=10, pady=5)

    send_method_var = tk.BooleanVar(value=send_with_ctrl)
    def update_send_method():
        global send_with_ctrl
        send_with_ctrl = send_method_var.get()
        log_info(f"Mode switched: {'Ctrl+Enter' if send_with_ctrl else 'Enter'}")
        save_config()

    ttk.Checkbutton(root, text="Use Ctrl+Enter (Simultaneous)", variable=send_method_var, command=update_send_method).grid(row=2, column=0, columnspan=2, pady=5)

    def apply_settings():
        global time_interval, run_duration
        try:
            time_interval = interval_var.get()
            d_val = duration_var.get().strip()
            run_duration = None if d_val.lower() in ['0', 'unlimited', 'inf'] else float(d_val)
            save_config()
            messagebox.showinfo("Success", "Settings applied.")
        except: 
            messagebox.showerror("Error", "Invalid configuration.")

    ttk.Button(root, text="Apply Settings", command=apply_settings).grid(row=3, column=0, columnspan=2, pady=10)
    status_label = tk.Label(root, text="Status: Stopped", fg="blue")
    status_label.grid(row=4, column=0, columnspan=2, pady=5)
    
    tk.Label(root, text=f"Hotkeys: {TOGGLE_HOTKEY} Toggle | {STOP_HOTKEY} Stop", font=(None, 8)).grid(row=5, column=0, columnspan=2, pady=5)

    threading.Thread(target=monitor_qq, daemon=True).start()
    threading.Thread(target=setup_tray, daemon=True).start()

    # Intercept close button to hide to tray
    root.protocol("WM_DELETE_WINDOW", hide_to_tray)

    log_info(f"New session started. Log file: {log_filename}")
    root.mainloop()

if __name__ == "__main__":
    start_gui()
