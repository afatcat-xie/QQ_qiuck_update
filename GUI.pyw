#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# QQ_quick_update_gui.py  by afatcat-xie

import random
import string
import threading
import time as _time
import keyboard
import tkinter as tk
from tkinter import ttk

running = False
thread  = None
time    = 1.0          # 默认间隔 1 秒

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
        _time.sleep(time)

def start_script():
    global running, thread, time
    if running:
        return

    # 读取用户输入的间隔
    try:
        time = float(interval_entry.get())
    except ValueError:
        time = 1.0

    running = True
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    status_label.config(text="Status: Running")

def stop_script():
    global running
    running = False
    status_label.config(text="Status: Stopped")

# -------------------- GUI --------------------
root = tk.Tk()
root.title("QQ Quick Update  – by afatcat-xie")
root.resizable(False, False)

# 新增：间隔输入框
ttk.Label(root, text="Interval (seconds)").grid(row=0, column=0, padx=5, pady=5, sticky="e")
interval_entry = ttk.Entry(root, width=6)
interval_entry.insert(0, "1.0")
interval_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Button(root, text="Start", width=10, command=start_script).grid(row=1, column=0, padx=10, pady=10)
ttk.Button(root, text="Stop",  width=10, command=stop_script).grid(row=1, column=1, padx=10, pady=10)

status_label = tk.Label(root, text="Status: Stopped", fg="blue")
status_label.grid(row=2, column=0, columnspan=2, pady=5)

tk.Label(root, text="Tip: Put QQ chat box in focus and press Start.", font=(None, 9))\
  .grid(row=3, column=0, columnspan=2, padx=10, pady=5)

root.mainloop()
