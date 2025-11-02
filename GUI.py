#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# QQ_quick_update_gui.py  by afatcat-xie
#
# Enhancement: Loop detection for whether QQ.exe exists, automatic enable/disable buttons, console English logs.
# NEW: Save/Load settings to/from qq_quick_update.ini
# NEW: Console logs with timestamp, auto-create "logs" folder, save all stdout/stderr to ini-style log file named by session start time.

import random
import string
import threading
import time as _time
import ctypes
import ctypes.wintypes
import tkinter as tk
from tkinter import ttk
import keyboard
import os
import configparser
import sys
from datetime import datetime
import traceback

# ----------Global variable ----------
running = False
worker_thread = None
time_interval = 1.0          # Default sending interval
qq_exists = False            # Current QQ status
lock = threading.Lock()      # Protect qq_exists read and write
run_duration = None          # New: running duration in seconds (None = unlimited)
start_time = None            # New: timestamp when worker started

INI_FILE = "qq_quick_update.ini"
LOG_DIR = "logs"
log_fp = None
log_ini = None
log_lock = threading.Lock()

# ---------- Logging ----------
def _ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def _open_log_session():
    global log_fp, log_ini
    session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(LOG_DIR, f"{session_time}.ini")
    log_fp = open(log_path, "w", encoding="utf-8")
    log_ini = configparser.ConfigParser()
    log_ini.add_section("Log")
    log_ini.set("Log", "session_start", session_time)
    log_ini.set("Log", "entries", "0")
    log_fp.write("# QQ Quick Update Session Log\n")
    log_fp.flush()

def _log_print(level, msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {level}: {msg}"
    print(line)  # still to console
    if log_ini and log_fp:
        with log_lock:
            try:
                count = int(log_ini.get("Log", "entries"))
                log_ini.set("Log", f"{count+1}", line)
                log_ini.set("Log", "entries", str(count+1))
                log_fp.write(line + "\n")
                log_fp.flush()
            except Exception:
                pass  # ignore log write errors

def log_info(msg):
    _log_print("INFO", msg)

def log_error(msg):
    _log_print("ERROR", msg)

# ---------- INI helper ----------
def load_settings():
    global time_interval, run_duration
    if not os.path.isfile(INI_FILE):
        return
    cfg = configparser.ConfigParser()
    try:
        cfg.read(INI_FILE, encoding="utf-8")
        time_interval = cfg.getfloat("Settings", "interval", fallback=1.0)
        dur = cfg.get("Settings", "duration", fallback="").strip()
        if dur == "":
            run_duration = None
        else:
            run_duration = int(dur) if dur.isdigit() and int(dur) > 0 else None
    except Exception as e:
        log_error(f"Load settings failed: {e}")

def save_settings():
    cfg = configparser.ConfigParser()
    cfg["Settings"] = {
        "interval": str(time_interval),
        "duration": str(run_duration) if run_duration is not None else ""
    }
    try:
        with open(INI_FILE, "w", encoding="utf-8") as f:
            cfg.write(f)
        log_info("Settings saved.")
    except Exception as e:
        log_error(f"Save settings failed: {e}")

# ---------- Win32 detects QQ.exe ----------
TH32CS_SNAPPROCESS = 0x00000002
class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.wintypes.DWORD),
                ("cntUsage", ctypes.wintypes.DWORD),
                ("th32ProcessID", ctypes.wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", ctypes.wintypes.DWORD),
                ("cntThreads", ctypes.wintypes.DWORD),
                ("th32ParentProcessID", ctypes.wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("szExeFile", ctypes.c_char * 260)]

def qq_is_running():
    """Return True if QQ.exe is found in the process snapshot."""
    kernel32 = ctypes.windll.kernel32
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == -1:
        return False
    entry = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
    found = False
    if kernel32.Process32First(snap, ctypes.byref(entry)):
        while True:
            try:
                exe_name = entry.szExeFile.decode('utf-8', errors='ignore')
                if exe_name.lower() == "qq.exe":
                    found = True
                    break
            except Exception:
                pass
            if not kernel32.Process32Next(snap, ctypes.byref(entry)):
                break
    kernel32.CloseHandle(snap)
    return found

# ---------- Background monitoring thread ----------
def monitor_qq():
    global qq_exists
    while True:
        try:
            current = qq_is_running()
            with lock:
                changed = current != qq_exists
                qq_exists = current
            if changed:
                log_msg = "QQ.exe is now RUNNING." if current else "QQ.exe is NOT running."
                log_info(log_msg)
                root.after(0, update_buttons, current)
                if not current:                     # QQ just disappeared
                    root.after(0, auto_stop_if_needed)
        except Exception as e:
            log_error(f"Monitor thread error: {e}")
        _time.sleep(1)

def auto_stop_if_needed():
    """If QQ disappears while the script is running, stop it automatically."""
    global running
    if running:
        log_info("QQ.exe lost, stopping script automatically.")
        stop_script()

def update_buttons(qq_running):
    """Called in main thread to enable/disable Start button."""
    if qq_running:
        start_btn.config(state='normal')
    else:
        start_btn.config(state='disabled')

# ---------- Basic logic ----------
def random_8():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def worker():
    global running, start_time
    start_time = _time.time()
    try:
        while running:
            if keyboard.is_pressed('f8'):
                stop_script()
                break
            keyboard.write(random_8())
            keyboard.send('enter')
            _time.sleep(time_interval)
            # New: check duration
            if run_duration is not None:
                elapsed = _time.time() - start_time
                if elapsed >= run_duration:
                    log_info("Duration reached, stopping automatically.")
                    root.after(0, stop_script)
                    break
    except Exception as e:
        log_error(f"Worker thread error: {e}")
        root.after(0, stop_script)

def start_script():
    global running, worker_thread, time_interval, run_duration, start_time
    if running:
        return
    try:
        time_interval = float(interval_entry.get())
    except ValueError:
        time_interval = 1.0

    # New: parse duration
    dur_str = duration_entry.get().strip()
    if not dur_str:
        run_duration = None
    else:
        try:
            run_duration = int(dur_str)
            if run_duration <= 0:
                run_duration = None
        except ValueError:
            run_duration = None

    save_settings()  # Save on start
    running = True
    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()
    status_label.config(text="Status: Running")
    log_info("Script started.")

def stop_script():
    global running
    running = False
    status_label.config(text="Status: Stopped")
    log_info("Script stopped.")

# ---------- GUI ----------
def excepthook(exc_type, exc_value, exc_tb):
    log_error("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))

sys.excepthook = excepthook

_ensure_log_dir()
_open_log_session()
log_info("Program started.")

root = tk.Tk()
root.title("QQ Quick Update  – by afatcat-xie")
root.resizable(False, False)

# Load settings at launch
load_settings()

# Interval
ttk.Label(root, text="Interval (seconds)").grid(row=0, column=0, padx=5, pady=5, sticky="e")
interval_entry = ttk.Entry(root, width=6)
interval_entry.insert(0, str(time_interval))
interval_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

# New: Duration
ttk.Label(root, text="Duration (seconds, leave blank for unlimited)").grid(row=1, column=0, padx=5, pady=5, sticky="e")
duration_entry = ttk.Entry(root, width=10)
duration_entry.insert(0, str(run_duration) if run_duration is not None else "")
duration_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# Buttons
start_btn = ttk.Button(root, text="Start", width=10, command=start_script, state='disabled')
start_btn.grid(row=2, column=0, padx=10, pady=10)
stop_btn  = ttk.Button(root, text="Stop",  width=10, command=stop_script)
stop_btn.grid(row=2, column=1, padx=10, pady=10)

# Status
status_label = tk.Label(root, text="Status: Stopped", fg="blue")
status_label.grid(row=3, column=0, columnspan=2, pady=5)

tk.Label(root, text="Tip: Put QQ chat box in focus and press Start.", font=(None, 9))\
  .grid(row=4, column=0, columnspan=2, padx=10, pady=5)

# Start the monitoring thread
threading.Thread(target=monitor_qq, daemon=True).start()

log_info("GUI initialized.")
root.mainloop()
