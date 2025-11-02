#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# QQ_quick_update_gui.py  by afatcat-xie
#
# Enhancement: Loop detection for whether QQ.exe exists, automatic enable/disable buttons, console English logs.

import random
import string
import threading
import time as _time
import ctypes
import ctypes.wintypes
import tkinter as tk
from tkinter import ttk
import keyboard

# ----------Global variable ----------
running = False
worker_thread = None
time_interval = 1.0          # Default sending interval
qq_exists = False            # Current QQ status
lock = threading.Lock()      # Protect qq_exists read and write
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
            exe_name = entry.szExeFile.decode('utf-8', errors='ignore')
            if exe_name.lower() == "qq.exe":
                found = True
                break
            if not kernel32.Process32Next(snap, ctypes.byref(entry)):
                break
    kernel32.CloseHandle(snap)
    return found

# ---------- Background monitoring thread ----------
def monitor_qq():
    global qq_exists
    while True:
        current = qq_is_running()
        with lock:
            changed = current != qq_exists
            qq_exists = current
        if changed:
            log_msg = "[QQ Monitor] QQ.exe is now RUNNING." if current else "[QQ Monitor] QQ.exe is NOT running."
            print(log_msg)
            root.after(0, update_buttons, current)
            if not current:                     # QQ just disappeared
                root.after(0, auto_stop_if_needed)

        _time.sleep(1)

def auto_stop_if_needed():
    """If QQ disappears while the script is running, stop it automatically."""
    global running
    if running:
        print("[QQ Monitor] QQ.exe lost, stopping script automatically.")
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
    global running
    while running:
        if keyboard.is_pressed('f8'):
            stop_script()
            break
        keyboard.write(random_8())
        keyboard.send('enter')
        _time.sleep(time_interval)

def start_script():
    global running, worker_thread, time_interval
    if running:
        return
    try:
        time_interval = float(interval_entry.get())
    except ValueError:
        time_interval = 1.0
    running = True
    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()
    status_label.config(text="Status: Running")

def stop_script():
    global running
    running = False
    status_label.config(text="Status: Stopped")

# ---------- GUI ----------
root = tk.Tk()
root.title("QQ Quick Update  – by afatcat-xie")
root.resizable(False, False)

# Interval
ttk.Label(root, text="Interval (seconds)").grid(row=0, column=0, padx=5, pady=5, sticky="e")
interval_entry = ttk.Entry(root, width=6)
interval_entry.insert(0, "1.0")
interval_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

# Buttons
start_btn = ttk.Button(root, text="Start", width=10, command=start_script, state='disabled')
start_btn.grid(row=1, column=0, padx=10, pady=10)
stop_btn  = ttk.Button(root, text="Stop",  width=10, command=stop_script)
stop_btn.grid(row=1, column=1, padx=10, pady=10)

# Status
status_label = tk.Label(root, text="Status: Stopped", fg="blue")
status_label.grid(row=2, column=0, columnspan=2, pady=5)

tk.Label(root, text="Tip: Put QQ chat box in focus and press Start.", font=(None, 9))\
  .grid(row=3, column=0, columnspan=2, padx=10, pady=5)

# Start the monitoring thread
threading.Thread(target=monitor_qq, daemon=True).start()

root.mainloop()
