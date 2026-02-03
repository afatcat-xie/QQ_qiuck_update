
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import string
import threading
import time as _time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import keyboard
import os
import configparser
from datetime import datetime
from PIL import Image, ImageDraw
import pystray
import uiautomation as auto

# ---------- 全局变量 ----------
running = False
worker_thread = None
time_interval = 1.0          
input_length = 10            
send_with_ctrl = False       
root = None                  
status_label = None
log_display = None  
tray_icon = None             

INI_FILE = "qq_config.ini"
LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志初始化
log_filename = f"qq_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
LOG_FILE = os.path.join(LOG_DIR, log_filename)
log_fp = open(LOG_FILE, "a", encoding="utf-8")

def log_info(message):
    """线程安全的日志记录，支持文件、GUI和控制台输出"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    if log_fp:
        log_fp.write(f"[{full_timestamp}] [LOG] {message}\n")
        log_fp.flush()
    
    if log_display and root:
        try:
            # 使用 after 确保在主线程更新 UI
            root.after(0, lambda: (
                log_display.insert(tk.END, formatted_message + "\n"),
                log_display.see(tk.END)
            ))
        except: pass
    print(formatted_message)

def update_status(text, color):
    """更新 GUI 上的状态标签"""
    if root and status_label:
        root.after(0, lambda: status_label.config(text=f"状态: {text}", fg=color))

# ---------- 核心检测与自动发送逻辑 ----------

def worker_logic():
    global running
    # 仅允许 EditControl，排除了可能导致死循环或误触发的 DocumentControl
    VALID_CONTROL_TYPES = ['EditControl']
    
    with auto.UIAutomationInitializerInThread(debug=False):
        log_info("核心监控引擎已启动...")
        while running:
            try:
                el = auto.GetFocusedControl()
                
                if not el:
                    update_status("等待有效焦点", "orange")
                else:
                    ctrl_type = el.ControlTypeName
                    ctrl_name = el.Name if el.Name else "无名称"
                    window = el.GetTopLevelControl()
                    win_title = window.Name if window else "未知窗口"

                    info_str = f"焦点窗口: [{win_title}] | 控件: [{ctrl_type}]"
                    print(info_str)
                    if win_title and "QQ" in win_title and "\\" not in win_title:
                        # 明确禁止在文档展示区（通常是聊天记录区）尝试输入
    
                        if ctrl_type == 'DocumentControl':
                            update_status("禁止在文档区输入", "red")
                        elif ctrl_type in VALID_CONTROL_TYPES:
                            # 模拟输入逻辑
                            text_to_send = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(input_length))
                            keyboard.write(text_to_send)
                            _time.sleep(0.1) # 缓冲，防止发送过快
                            
                            if send_with_ctrl:
                                keyboard.press_and_release('ctrl+enter')
                                print('ctrl+enter')
                            else:
                                keyboard.press_and_release('enter')
                                print('enter')
                            
                            log_info(f"【发送成功】窗口: {win_title} | 内容: {text_to_send}")
                            update_status("运行中 (发送成功)", "green")
                        else:
                            update_status("无效输入区域", "orange")
                    else:
                        update_status("非 QQ 窗口", "orange")

            except Exception as e:
                log_info(f"【循环异常】: {str(e)}")
            
            _time.sleep(max(0.1, time_interval))
        log_info("核心监控引擎已安全停止。")

# ---------- 托盘与配置功能 ----------

def create_dummy_icon():
    """创建一个简单的托盘图标（如果找不到外部图标文件）"""
    width, height = 64, 64
    image = Image.new('RGB', (width, height), color=(0, 120, 215)) # 蓝色背景
    dc = ImageDraw.Draw(image)
    dc.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
    return image

def on_tray_quit(icon, item):
    icon.stop()
    if log_fp: log_fp.close()
    root.after(0, root.destroy)

def show_window(icon, item):
    icon.stop()
    root.after(0, root.deiconify)

def withdraw_window():
    """点击窗口关闭按钮时隐藏到托盘"""
    root.withdraw()
    global tray_icon
    image = create_dummy_icon()
    if os.path.exists("icon.ico"):
        try: image = Image.open("icon.ico")
        except: pass
    
    menu = (
        pystray.MenuItem('显示窗口', show_window), 
        pystray.MenuItem('退出程序', on_tray_quit)
    )
    tray_icon = pystray.Icon("QQTool", image, "QQ自动发送工具", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

def load_config():
    global time_interval, send_with_ctrl, input_length
    config = configparser.ConfigParser()
    if os.path.exists(INI_FILE):
        try:
            config.read(INI_FILE)
            if 'Settings' in config:
                time_interval = config.getfloat('Settings', 'interval', fallback=1.0)
                input_length = config.getint('Settings', 'input_length', fallback=10)
                send_with_ctrl = config.getboolean('Settings', 'send_with_ctrl', fallback=False)
        except: pass

def save_config():
    config = configparser.ConfigParser()
    config['Settings'] = {
        'interval': str(time_interval),
        'input_length': str(input_length),
        'send_with_ctrl': str(send_with_ctrl)
    }
    with open(INI_FILE, 'w') as f: config.write(f)

def toggle_worker():
    """切换监控开启/关闭状态"""
    global running, worker_thread
    if running:
        running = False
        update_status("已停止", "blue")
        log_info("已停止监控")
    else:
        running = True
        worker_thread = threading.Thread(target=worker_logic, daemon=True)
        worker_thread.start()
        update_status("运行中", "green")
        log_info("已启动监控")

def clear_logs():
    if log_display:
        log_display.delete('1.0', tk.END)
        log_info("日志界面已清空")

# ---------- GUI 界面构建 ----------

def run_gui():
    global root, status_label, log_display
    load_config()
    
    root = tk.Tk()
    root.title("QQ 自动发送监控工具")
    root.geometry("800x800")
    root.protocol('WM_DELETE_WINDOW', withdraw_window)

    # 样式配置
    style = ttk.Style()
    style.configure("TButton", padding=5)

    main_frame = ttk.Frame(root, padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # --- 设置区域 ---
    settings_label = ttk.Label(main_frame, text="参数设置", font=("微软雅黑", 10, "bold"))
    settings_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

    ttk.Label(main_frame, text="发送间隔 (秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
    interval_var = tk.DoubleVar(value=time_interval)
    ttk.Entry(main_frame, textvariable=interval_var, width=15).grid(row=1, column=1, sticky=tk.W)

    ttk.Label(main_frame, text="随机字符位数:").grid(row=2, column=0, sticky=tk.W, pady=5)
    length_var = tk.IntVar(value=input_length)
    ttk.Entry(main_frame, textvariable=length_var, width=15).grid(row=2, column=1, sticky=tk.W)

    send_method_var = tk.BooleanVar(value=send_with_ctrl)
    ttk.Checkbutton(main_frame, text="使用 Ctrl+Enter 发送 (QQ设置需匹配)", variable=send_method_var).grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.W)

    def apply():
        global time_interval, input_length, send_with_ctrl
        try:
            time_interval = interval_var.get()
            input_length = length_var.get()
            send_with_ctrl = send_method_var.get()
            save_config()
            log_info("配置已成功应用并保存至本地")
            messagebox.showinfo("成功", "配置已应用")
        except: 
            messagebox.showerror("错误", "请输入有效的数值")

    ttk.Button(main_frame, text="保存并应用配置", command=apply).grid(row=4, column=0, columnspan=2, pady=10)

    # --- 状态与日志 ---
    ttk.Separator(main_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

    status_label = tk.Label(main_frame, text="状态: 已停止", font=("微软雅黑", 11, "bold"), fg="blue")
    status_label.grid(row=6, column=0, columnspan=2, pady=5)

    log_header_frame = ttk.Frame(main_frame)
    log_header_frame.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(10, 2))
    ttk.Label(log_header_frame, text="实时运行日志:").pack(side=tk.LEFT)
    ttk.Button(log_header_frame, text="清空日志", command=clear_logs, width=10).pack(side=tk.LEFT, padx=10)

    log_display = scrolledtext.ScrolledText(main_frame, height=18, width=70, font=("Consolas", 9), bg="#f8f8f8")
    log_display.grid(row=8, column=0, columnspan=2, sticky=tk.NSEW)

    # --- 快捷键提示 ---
    footer_label = ttk.Label(main_frame, text="全局快捷键: Ctrl + Alt + Q (启动/停止)", foreground="gray")
    footer_label.grid(row=9, column=0, columnspan=2, pady=15)

    # 注册快捷键
    try:
        keyboard.add_hotkey("ctrl+alt+q", toggle_worker)
        log_info("热键 Ctrl+Alt+Q 注册成功")
    except Exception as e:
        log_info(f"热键注册失败: {e}")
    
    log_info("程序启动完成，等待操作。")
    
    # 窗口居中
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    run_gui()
