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
import uiautomation as auto
import configparser
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageGrab, ImageDraw
import pystray
from pystray import MenuItem as item
import pygetwindow as gw
import pyautogui
from openai import OpenAI
import base64
import sys

# redirect stdout and stderr to logfile as well
class TeeWriter:
    def __init__(self, original, file_handle):
        self.original = original
        self.file_handle = file_handle

    def write(self, message):
        try:
            self.original.write(message)
        except Exception:
            pass
        try:
            if self.file_handle:
                self.file_handle.write(message)
                self.file_handle.flush()
        except Exception:
            pass

    def flush(self):
        try:
            self.original.flush()
        except Exception:
            pass
        try:
            if self.file_handle:
                self.file_handle.flush()
        except Exception:
            pass


# ---------- Global variables | 全局变量 ----------
running = False
worker_thread = None
time_interval = 1.0          
input_length = 10            
send_with_ctrl = False       
root = None                  
status_label = None
log_display = None  
tray_icon = None
ai_mode = False 
entry = None
saved_name = "User" # Default value | 默认值
image64 = ""    
api_key_global = "" # New: Global API Key variable | 新增：全局API密钥变量

# (previous docking-tracking logic removed, no longer needed)

# remember the baseline QQ.exe window rectangle after first start hotkey
# 在第一次启动热键后记录QQ.exe窗口的基准位置
qq_initial_rect = None

# New: Conversation history list | 新增：对话历史列表
chat_context = [] 
MAX_CONTEXT_LINES = 15 # How many recent screenshot records to show the AI | 给AI看最近多少次截图记录
MAX_REPLY_LENGTH = 150 # New: Maximum character limit for AI replies | 新增：AI回复的最大字符数限制
last_processed_chat_name = "" # New: Records the name of the last processed chat, used for detecting switches | 新增：记录上一次处理的聊天名称，用于检测切换

# Event used to block processing until we have extracted a chat name under the mouse pointer
chat_name_ready = threading.Event()

INI_FILE = "qq_config.ini"
LOG_DIR = "logs"
HISTORY_FILE = "chat_history.txt" # New: History record file | 新增：历史记录文件

# ensure log directory exists (with error handling)
try:
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
except Exception as e:
    print(f"Failed to create log directory '{LOG_DIR}': {e}")

# Log initialization using UTC timestamp | 日志初始化 (使用 UTC 时间戳)
start_utc = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
log_filename = f"qq_monitor_{start_utc}.log"
LOG_FILE = os.path.join(LOG_DIR, log_filename)
try:
    log_fp = open(LOG_FILE, "a", encoding="utf-8")
except Exception as e:
    log_fp = None
    print(f"Failed to open log file '{LOG_FILE}': {e}")

# redirect standard output and error to the log file as well
if log_fp:
    sys.stdout = TeeWriter(sys.stdout, log_fp)
    sys.stderr = TeeWriter(sys.stderr, log_fp)

def log_info(message):
    """Thread-safe logging | 线程安全的日志记录"""
    timestamp = datetime.utcnow().strftime("%H:%M:%S")
    full_timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    if log_fp:
        try:
            log_fp.write(f"[{full_timestamp}] [LOG] {message}\n")
            log_fp.flush()
        except Exception:
            pass
    
    if log_display and root:
        try:
            root.after(0, lambda: (
                log_display.insert(tk.END, formatted_message + "\n"),
                log_display.see(tk.END)
            ))
        except: pass
    print(formatted_message)


def clean_name(name_str):
    """Strip trailing parentheses content and whitespace, mimicking mouse_control_monitor logic."""
    if not name_str:
        return ""
    return name_str.split('(')[0].strip()


def detect_chat_identity(element):
    """Given a UIAutomation element, return a cleaned chat/group name if available.
    This mirrors the logic in mouse_control_monitor.get_logic_context.
    """
    try:
        window = element.GetTopLevelControl()
        if window:
            win_name = window.Name or ""
            # if it's a QQ window we try deeper detection
            if "QQ" in win_name:
                # if the element itself is an edit control with a name
                if element.ControlTypeName == 'EditControl' and element.Name and element.Name != 'QQ':
                    return clean_name(element.Name)
                # otherwise search children
                for child in window.GetChildren():
                    if child.ControlTypeName == 'EditControl' and child.Name and child.Name != 'QQ':
                        return clean_name(child.Name)
                # fallback to cleaned window title
                return clean_name(win_name)
            else:
                # non-QQ window, return cleaned title
                return clean_name(win_name)
    except Exception:
        pass
    return ""


def detect_chat_name_from_point():
    """Use current mouse coordinates to detect chat identity via underlying control."""
    try:
        x, y = pyautogui.position()
        ctrl = auto.ControlFromPoint(x, y)
        if not ctrl:
            return ""
        # only consider EditControl for performance
        if ctrl.ControlTypeName != 'EditControl':
            log_info(f"Mouse control is {ctrl.ControlTypeName}, not EditControl – ignoring")
            return ""
        name = detect_chat_identity(ctrl)
        if name:
            log_info(f"Control under mouse yields name '{name}'")
            return name
    except Exception as e:
        log_info(f"Failed to get control under mouse: {e}")
    return ""


def get_chat_name_from_mouse():
    """Deprecated wrapper pointing to detect_chat_name_from_point."""
    return detect_chat_name_from_point()

def update_status(text, color):
    """Updates the status label on the GUI | 更新 GUI 上的状态标签"""
    if root and status_label:
        root.after(0, lambda: status_label.config(text=f"Status: {text} | 状态: {text}", fg=color))

# ---------- History Record Management (New) | 历史记录管理 (新增) ----------
def update_chat_history(new_text, chat_name=""):
    """
    Saves OCR results to file and memory, tagging each entry with the associated chat/group name.
    Simple deduplication logic: if a new block of text is identical to the last, it won't be saved.
    保存 OCR 结果到文件和内存，同时标记每条记录所属的聊天/群名。
    简单的去重逻辑：如果新的一段文字和上一段完全一样，就不保存。
    """
    global chat_context
    
    if not new_text or not new_text.strip():
        return False # Empty content does not update | 空内容不更新

    # Remove leading/trailing whitespace | 去除首尾空格
    clean_text = new_text.strip()
    entry_text = clean_text
    if chat_name:
        entry_text = f"[{chat_name}] {clean_text}"
    
    # Check if it's identical to the previous record | 检查是否和上一条记录完全重复
    if chat_context and chat_context[-1] == entry_text:
        # log_info("Overall text is duplicated, not updating chat history.") # Reduce log output, just skip simply | 减少日志输出，仅做简单跳过
        return False # Content duplicated, no update | 内容重复，不更新
        
    # Add to in-memory list | 添加到内存列表
    chat_context.append(entry_text)
    
    # Keep the in-memory list from getting too long to prevent Token explosion | 保持内存列表不要太长，防止Token爆炸
    if len(chat_context) > MAX_CONTEXT_LINES:
        chat_context.pop(0)
        
    # Append to file (permanent storage) | 追加写入文件（永久保存）
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n--- [Record Time: {timestamp} | 记录时间: {timestamp}] ---\n")
            f.write(entry_text)
            f.write("\n")
        print(f"Chat history updated, current cache entries: {len(chat_context)} | 历史记录已更新，当前缓存条数: {len(chat_context)}")
        return True # Update successful | 更新成功
    except Exception as e:
        log_info(f"Failed to save chat history: {e} | 保存历史记录失败: {e}")
        return True

# ---------- Core Detection and Auto-Send Logic | 核心检测与自动发送逻辑 ----------
def crop_center_chat_no_header(image_path, output_path):
    try:
        img = Image.open(image_path)
        width, height = img.size
        # --- 1. Define left/right boundaries --- | --- 1. 定义左右边界 ---
        left_boundary = int(width * 0.33)
        right_boundary = int(width * 0.78)
        # --- 2. Define top/bottom boundaries --- | --- 2. 定义上下边界 ---
        top_boundary = int(height * 0.05)
        bottom_boundary = height
        crop_box = (left_boundary, top_boundary, right_boundary, bottom_boundary)
        # --- 3. Perform cropping and saving --- | --- 3. 执行裁剪并保存 ---
        cropped_img = img.crop(crop_box)
        cropped_img.save(output_path)
    except Exception as e:
        print(f"Cropping error: {e} | 裁剪错误: {e}")

def image_to_base64(image_path):
    global image64
    try:
        with open(image_path, "rb") as image_file:
            image64 = base64.b64encode(image_file.read()).decode()
    except Exception as e:
        return f"Conversion failed: {e} | 转换失败: {e}"

def capture_qq_with_padding(reposition_right_if_needed=False):
    global qq_initial_rect
    windows = gw.getWindowsWithTitle('QQ')
    if not windows:
        log_info("QQ window not found. | 未找到QQ窗口。")
        return False
    
    qq = windows[0]
    
    # if we have remembered a baseline rect, validate it now
    if qq_initial_rect is not None:
        current_rect = (qq.left, qq.top, qq.width, qq.height)
        if current_rect != qq_initial_rect or not qq.isActive:
            log_info("QQ window moved or covered; attempting to reactivate/switch. | QQ窗口位置变化或被覆盖，尝试重新激活。")
            try:
                qq.activate()
            except Exception:
                pass
            _time.sleep(0.5)
            # update baseline regardless of result; subsequent loops will use this
            qq_initial_rect = (qq.left, qq.top, qq.width, qq.height)
            log_info(f"New baseline QQ window rect: {qq_initial_rect}")

    if qq.isMinimized:
        qq.restore()
    qq.activate()
    _time.sleep(0.5) # Allow activation to settle

    if reposition_right_if_needed:
        # simply apply the Win+Right shortcut whenever repositioning is requested
        log_info("Repositioning QQ window using Win+Right per request. | 根据要求使用 Win+Right 重定位 QQ 窗口。")
        keyboard.press_and_release('win+right')
        _time.sleep(0.8)
        # refresh window reference in case geometry changed
        windows = gw.getWindowsWithTitle('QQ')
        if windows:
            qq = windows[0]
        else:
            log_info("Warning: QQ window disappeared after repositioning. Skipping screenshot. | 警告: QQ窗口在调整位置后消失。跳过截图。")
            return False

    padding_side = 0.5
    try:
        # Use updated qq coordinates after potential repositioning | 使用可能重定位后的更新QQ坐标
        screenshot = ImageGrab.grab(bbox=(qq.left+padding_side, qq.top, qq.right-padding_side, qq.bottom), all_screens=True)
        screenshot.save("qq_trimmed.png")
        return True
    except Exception as e:
        log_info(f"Screenshot failed: {e} | 截图失败: {e}")
        return False

def save_value():
    global saved_name
    user_input = entry.get() 
    saved_name = user_input
    messagebox.showinfo("Tip | 提示", f"Name saved: {saved_name} | 名字已保存: {saved_name}")
    
def AI1_OCR():
    """Executes OCR recognition, returns recognized text | 执行 OCR 识别，返回识别到的文本"""
    # Please replace with your actual API Key (if needed, it should be read from config file or managed securely)
    # 请将此占位符替换为你在OpenAI或Siliconflow获得的有效API Key
    client = OpenAI(
        api_key=api_key_global, # Use global API key variable | 使用全局API密钥变量
        base_url="https://api.siliconflow.cn/v1"
    )
    
    try:
        response_obj = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-OCR",
            temperature=0,
            top_p=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url":f"data:image/png;base64,{image64}"}},
                        {"type": "text", "text": "Output all text in the image, preserving original line breaks. | 输出图片中的所有文字，保持原有换行。"}
                    ]
                }
            ]
        )
        text_content = response_obj.choices[0].message.content
        return text_content
    except Exception as e:
        log_info(f"OCR Error: {e}")
        return ""

def AI2_Generate_Reply(ocr_chat_name_hint="", current_chat_name=""): # Added current_chat_name parameter for clarity
    """
    Reads historical records in chat_context to generate replies.
    读取 chat_context 中的历史记录，生成回复。
    """
    global chat_context, last_processed_chat_name 
    
    if not chat_context:
        return ""

    # Please replace with your actual API Key (if needed, it should be read from config file or managed securely)
    # 请将此占位符替换为你在OpenAI或Siliconflow获得的有效API Key
    client = OpenAI(
        api_key=api_key_global, # Use global API key variable | 使用全局API密钥变量
        base_url="https://api.siliconflow.cn/v1"
    )

    # Concatenate recent OCR results as context
    # Tell the AI there might be repetitive content and let it sort out the conversation logic itself
    # 将最近几次的 OCR 结果拼起来作为上下文
    # 告诉 AI 可能会有重复内容，让它自己梳理
    full_context_str = "\n====== Previous Screenshot Records | 之前的屏幕截图记录 ======\n".join(chat_context)

    # Build AI's current chat environment information | 构建AI的当前聊天环境信息
    current_identity_for_ai = ""
    # choose the most relevant chat name to tell the AI, prefer explicit OCR hint if available
    effective_name = ocr_chat_name_hint or current_chat_name or last_processed_chat_name
    if effective_name and effective_name != "QQ":
        current_identity_for_ai = f"The current chat object/group chat mainly appears as 【{effective_name}】. | 当前聊天对象/群聊主要显示为【{effective_name}】。"
    elif last_processed_chat_name == "QQ":
        current_identity_for_ai = "The current chat window title is the generic name 【QQ】. | 当前聊天窗口标题为通用名称【QQ】。"

    # Inform the AI that each history fragment is prefixed with the chat/group name
    prefix_info = (
        "Each record in the history may start with a prefix like '[GroupName]' to indicate which chat or group it belongs to. "
        "Please pay attention to that when understanding the conversation context. | "
        "历史中的每条记录前可能会有类似 '[群名]' 的前缀，用以指示所属的聊天或群。理解对话上下文时请注意这一点。"
    )

    system_prompt = f"""
Ignore all LV*, they represent levels; only focus on the specific names that follow as roles. | 忽略所有LV*，它们是等级，只能关注后面的具体名称作为角色。
You are a chat assistant. Your role is 【{saved_name}】, please reply from the perspective and identity of 【{saved_name}】. | 你是一个聊天助手。你的角色是【{saved_name}】，请以【{saved_name}】的视角和身份进行回复。
{current_identity_for_ai}
{prefix_info}
You need to read the 【chat history fragments】 I provide. | 你需要阅读我提供的【聊天记录历史片段】。
Note: These fragments are text from continuous time screenshots, so the content may have a lot of repetition (overlap). You need to ignore the repetitive parts yourself and clarify the conversation logic. | 注意：这些片段是连续时间的屏幕截图文字，因此内容可能会有大量重复（重叠），你需要自行忽略重复部分，理清对话逻辑。

Please predict and output my next reply based on the latest conversation progress. | 请根据最新的对话进展，预测并输出我的下一句回复。
Requirements: | 要求：
1. Only output the reply content, do not output the analysis process. | 1. 只输出回复内容，不要输出分析过程。
2. If the other party has ended the topic or no reply is needed, output "PASS". | 2. 如果对方已经结束话题或不需要回复，输出 "PASS"。
3. The tone of voice should be natural. | 3. 语气要自然。
"""
    log_info(f"System Prompt sent to AI:\n{system_prompt} | 发送给AI的系统Prompt:\n{system_prompt}")
    log_info(f"User content sent to AI (chat history):\n{full_context_str} | 发送给AI的用户内容 (聊天历史):\n{full_context_str}")

    try:
        response_obj = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f'This is the extracted history: \n{full_context_str} | 这是提取到的历史记录：\n{full_context_str}'}
            ]
        )
        reply = response_obj.choices[0].message.content
        log_info(f"AI original reply:\n{reply} | AI原始回复:\n{reply}")
        # Simply clean up the chain of thought <think>...</think> that DeepSeek sometimes includes (if any)
        # 简单清洗一下 DeepSeek 有时会带的思维链 <think>...</think> (如果有)
        if "</think>" in reply:
            reply = reply.split("</think>")[-1].strip()
            
        return reply
    except Exception as e:
        log_info(f"Generation Error: {e}")
        return ""
def worker_logic():
    global running, last_processed_chat_name
    VALID_CONTROL_TYPES = ['EditControl']

    # Introduce a variable to store the OCR results (list of words) from the previous round
    # 引入一个变量来存储上一轮的 OCR 结果（分词列表）
    last_ocr_words = [] # Ensure initialized as a list, not None | 确保初始化为列表，而不是 None

    with auto.UIAutomationInitializerInThread(debug=False):
        log_info("Core monitoring engine started... | 核心监控引擎已启动...")
        
        # before doing anything, try to obtain a chat name from whatever control the mouse is over
        while running and not chat_name_ready.is_set():
            name = get_chat_name_from_mouse()
            if name:
                global last_processed_chat_name
                last_processed_chat_name = name
                chat_name_ready.set()
                log_info(f"Initial chat name obtained from mouse: {last_processed_chat_name}")
                break
            log_info("Waiting for chat name under mouse pointer...")
            _time.sleep(0.5)

        while running:
            # if chat name hasn't been determined yet, keep trying and sleep
            if not chat_name_ready.is_set():
                name = get_chat_name_from_mouse()
                if name:
                    last_processed_chat_name = name
                    chat_name_ready.set()
                    log_info(f"Chat name obtained from mouse: {last_processed_chat_name}")
                else:
                    _time.sleep(0.5)
                    continue

            try:
                el = auto.GetFocusedControl()
                if not el:
                    update_status("Waiting for focus | 等待焦点", "orange")
                    # If focus leaves the QQ window, reset chat context
                    # 如果焦点离开了QQ窗口，重置聊天上下文
                    if last_processed_chat_name:
                        log_info(f"Focus left QQ window, resetting chat context. Original chat: {last_processed_chat_name} | 焦点离开QQ窗口，重置聊天上下文。原聊天: {last_processed_chat_name}")
                        last_processed_chat_name = ""
                        chat_context.clear()
                        last_ocr_words = [] # Clear word history | 清除词汇历史
                else:
                    ctrl_type = el.ControlTypeName
                    try:
                        window = el.GetTopLevelControl()
                        win_title = window.Name if window else "Unknown | 未知"
                    except: win_title = "Unknown | 未知"

                    if win_title and "QQ" == win_title and "\\" not in win_title:
                        # determine chat name using more thorough detection logic
                        current_chat_name_from_title = detect_chat_identity(el)
                        if not current_chat_name_from_title:
                            # fallback to raw window title cleaning
                            current_chat_name_from_title = clean_name(win_title)
                        
                        if current_chat_name_from_title != last_processed_chat_name:
                            log_info(f"Chat switch detected! From '{last_processed_chat_name if last_processed_chat_name else 'None | 无'}' to '{current_chat_name_from_title}'. | 检测到聊天切换！从 '{last_processed_chat_name if last_processed_chat_name else '无'}' 切换到 '{current_chat_name_from_title}'。")
                            last_processed_chat_name = current_chat_name_from_title
                            chat_context.clear() # Clear conversation history when switching chats | 切换聊天时清空对话历史
                            last_ocr_words = [] # Clear word history when switching chats | 切换聊天时清空词汇历史
                            log_info("Chat history context cleared. | 已清空聊天历史上下文。")
                            # clear readiness so that we will wait for mouse-based name next round
                            chat_name_ready.clear()

                        if ctrl_type == 'DocumentControl':
                            update_status("Input prohibited in document area | 禁止在文档区输入", "red")
                        
                        elif ctrl_type in VALID_CONTROL_TYPES:
                            
                            # =========== AI Mode | AI 模式 ===========
                            if ai_mode:
                                log_info(f"【AI Mode】Chat window '{last_processed_chat_name}' detected... | 【AI模式】检测到聊天窗口 '{last_processed_chat_name}'...") 
                                update_status("AI: Capturing screen for analysis... | AI: 正在截屏分析...", "purple")
                                
                                replied_this_cycle = False # Mark if replied this cycle | 标记本轮是否已回复
                                
                                # 1. Adjust window and screenshot (now includes conditional Win+Right)
                                # 1. 调整窗口并截图 (现在包含条件性Win+Right)
                                windows = gw.getWindowsWithTitle('QQ') # Get latest window info again | 再次获取以确保最新的窗口信息
                                if windows:
                                    qq_window = windows[0]
                                    if qq_window.isMinimized: qq_window.restore()
                                    qq_window.activate()
                                    _time.sleep(0.5) # Wait for activation | 等待激活
                                else:
                                    log_info("QQ window disappeared during activation, skipping AI analysis. | QQ窗口在激活时消失，跳过AI分析。")
                                    update_status("AI: QQ window lost | AI: QQ窗口丢失", "red")
                                    _time.sleep(max(2.0, time_interval))
                                    continue # Skip the rest of the current loop | 跳过当前循环的剩余部分

                                if capture_qq_with_padding(reposition_right_if_needed=True): # Pass True for conditional repositioning | 传递True以条件性重定位
                                    crop_center_chat_no_header("qq_trimmed.png", "image.png")
                                    image_to_base64("image.png")
                                    
                                    # 2. OCR Recognition | 2. OCR 识别
                                    current_ocr_text = AI1_OCR()
                                    log_info(f"OCR Recognition Result:\n{current_ocr_text} | OCR识别结果:\n{current_ocr_text}")
                                    
                                    # --- New: Attempt to get chat name slice from OCR results ---
                                    # --- 新增：从OCR结果中尝试获取聊天名称切片 ---
                                    ocr_chat_name_hint = ""
                                    first_non_empty_line = ""
                                    for line in current_ocr_text.split('\n'):
                                        stripped_line = line.strip()
                                        if stripped_line:
                                            first_non_empty_line = stripped_line
                                            break
                                            
                                    if first_non_empty_line:
                                        # Heuristic rule: if the first line is in "Name: Message" format
                                        # 启发式规则：如果第一行是 "名称: 消息" 格式
                                        if "：" in first_non_empty_line and not first_non_empty_line.startswith(saved_name + "："):
                                            parts = first_non_empty_line.split('：', 1)
                                            if parts[0].strip():
                                                ocr_chat_name_hint = parts[0].strip()
                                        # Heuristic rule: if the first line is in "[Group Name] Message" format
                                        # 启发式规则：如果第一行是 "[群名] 消息" 格式
                                        elif first_non_empty_line.startswith('[') and ']' in first_non_empty_line:
                                            end_bracket_idx = first_non_empty_line.find(']')
                                            if end_bracket_idx != -1:
                                                ocr_chat_name_hint = first_non_empty_line[1:end_bracket_idx].strip()
                                    
                                    if ocr_chat_name_hint:
                                        log_info(f"Chat hint name extracted from OCR result: {ocr_chat_name_hint} | 从OCR结果中提取到聊天提示名称: {ocr_chat_name_hint}")
                                    # --- End OCR chat name slice extraction | 结束 OCR 聊天名称切片提取 ---

                                    current_ocr_words_set = set(word for word in current_ocr_text.split() if word.strip())
                                    
                                    is_new_content_at_word_level = False
                                    if last_ocr_words: # Check if list is not empty | 检查列表是否非空
                                        last_ocr_words_set = set(last_ocr_words)
                                        # Check if new words appeared (excluding old overlapping parts)
                                        # 检查是否有新的单词出现 (排除旧的重叠部分)
                                        if current_ocr_words_set - last_ocr_words_set: # Find words in current set but not in history set | 查找当前集合中有而历史集合中没有的词
                                            is_new_content_at_word_level = True
                                    elif current_ocr_words_set: # If last_ocr_words is empty (first run) and current has content, treat as new content | 如果last_ocr_words为空（首次运行），且当前有内容，则视为新内容
                                        is_new_content_at_word_level = True
                                    
                                    # 3. Update history and judge if there's new content, only consider replying when new content appears
                                    # 3. 更新历史并判断是否有新内容，只有在新内容出现时才考虑回复
                                    if is_new_content_at_word_level:
                                        log_info("New message detected at word level, considering generating a reply... | 检测到词汇级别的新消息，正在考虑生成回复...")
                                        # update_chat_history still handles overall text deduplication (against the last whole entry)
                                        # update_chat_history 仍然处理整体文本的去重（与上一整条）
                                        if update_chat_history(current_ocr_text, last_processed_chat_name): 
                                            log_info(f"History for '{last_processed_chat_name}' updated (chat tagged), generating reply... | 已更新 '{last_processed_chat_name}' 的历史记录（已标记聊天），生成回复中...")
                                            # 4. Generate reply based on history | 4. 基于历史生成回复
                                            # Pass ocr_chat_name_hint to AI2_Generate_Reply (Note: API key replaced with placeholder)
                                            # 将 ocr_chat_name_hint 传递给 AI2_Generate_Reply (注意API密钥已替换为占位符)
                                            reply_text = AI2_Generate_Reply(ocr_chat_name_hint=ocr_chat_name_hint, current_chat_name=last_processed_chat_name)
                                            
                                            # --- Limit AI reply max length --- | --- 限制 AI 回复的最大长度 ---
                                            if len(reply_text) > MAX_REPLY_LENGTH:
                                                reply_text = reply_text[:MAX_REPLY_LENGTH - 3] + "..." # Truncate and add ellipsis | 截断并添加省略号
                                                log_info(f"AI reply content too long, truncated to {MAX_REPLY_LENGTH} characters. | AI回复内容过长，已截断至 {MAX_REPLY_LENGTH} 字符。")

                                            if reply_text and "PASS" not in reply_text and len(reply_text) > 0:
                                                log_info(f"AI decided to reply: {reply_text} | AI 决定回复: {reply_text}")
                                                keyboard.write(reply_text)
                                                _time.sleep(0.5)
                                                
                                                if send_with_ctrl:
                                                    keyboard.press_and_release('ctrl+enter')
                                                else:
                                                    keyboard.press_and_release('enter')
                                                
                                                update_status("AI replied successfully | AI 回复成功", "green")
                                                replied_this_cycle = True # Mark as replied | 标记已回复
                                                
                                                # --- Key modification: update last_ocr_words immediately after AI replies ---
                                                # Rescreenshot to update baseline recognition content, including AI's own reply, to avoid treating it as "new content" next time
                                                # --- 关键修改：AI 回复后立即更新 last_ocr_words ---
                                                # 重新截图更新基准识别内容，包含AI自己的回复，避免下次检测将其视为"新内容"
                                                log_info("AI has finished replying, rescreenshotting to update baseline recognition content to avoid self-repeated replies... | AI已完成回复，重新截图更新基准识别内容，避免自我重复回复...")
                                                _time.sleep(1.0) # Wait for message to send and display on screen | 等待消息发送并显示到屏幕
                                                if capture_qq_with_padding(reposition_right_if_needed=False): # This screenshot only gets current status, no need to reposition again | 此次截图仅获取当前状态，无需再次重定位
                                                    crop_center_chat_no_header("qq_trimmed.png", "image.png")
                                                    image_to_base64("image.png")
                                                    post_reply_ocr_text = AI1_OCR()
                                                    # Update last_ocr_words to screen text after AI reply, as baseline for next comparison
                                                    # 更新 last_ocr_words 为AI回复后的屏幕文字，作为下一次比较的基准
                                                    last_ocr_words = list(set(word for word in post_reply_ocr_text.split() if word.strip()))
                                                    log_info(f"Baseline recognition content updated (including AI reply). | 基准识别内容已更新 (包含AI回复)。")
                                                else:
                                                    log_info("Warning: Rescreenshot failed after AI reply, may cause AI to repeatedly reply to its own content in the next loop. | 警告: AI回复后重新截图失败，可能导致下一次循环中AI重复回复自身内容。")
                                                # --- End update after AI reply | 结束 AI 回复后更新 ---

                                            else:
                                                log_info("AI decided to remain silent (PASS). | AI 决定保持沉默 (PASS)。")
                                                update_status("AI standby (no reply) | AI 待机中 (无回复)", "blue")
                                        else:
                                            log_info("Although new words appeared, skipping reply due to overall content duplication with previous record. | 尽管有新词汇，但由于整体内容与上一记录重复，跳过回复。")
                                            update_status("Monitoring (no necessary reply) | 监控中 (非必要回复)", "blue")
                                    else:
                                        log_info("Screen content highly repetitive or no new words, skipping processing. | 画面内容高度重复或无新词汇，跳过处理。")
                                        update_status("Monitoring (no new messages) | 监控中 (无新消息)", "gray")

                                    # If no AI reply was made this round, set the last OCR result as the baseline for the next round
                                    # 如果本轮没有进行 AI 回复，则将上次 OCR 结果作为下一轮的基准
                                    if not replied_this_cycle:
                                        last_ocr_words = list(current_ocr_words_set)
                                    
                                else:
                                    log_info("Screenshot failed, unable to perform AI analysis. | 截图失败，无法进行AI分析。")
                                    update_status("AI: Screenshot failed | AI: 截图失败", "red")

                                # AI mode cooldown time | AI 模式的冷却时间
                                _time.sleep(max(2.0, time_interval))

                            # =========== Random Character Mode | 随机字符模式 ===========
                            else:
                                text_to_send = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(input_length))
                                keyboard.write(text_to_send)
                                _time.sleep(0.1) 
                                if send_with_ctrl: keyboard.press_and_release('ctrl+enter')
                                else: keyboard.press_and_release('enter')
                                log_info(f"Randomly sent: {text_to_send} | 随机发送: {text_to_send}")
                                _time.sleep(max(0.1, time_interval))
                        else:
                            update_status("Not input area | 非输入区域", "orange")
                    else:
                        update_status("Not QQ window | 非 QQ 窗口", "orange")
                        # If not QQ window, reset chat context
                        # 如果非QQ窗口，重置聊天上下文
                        if last_processed_chat_name:
                            log_info(f"Focus left QQ window, resetting chat context. Original chat: {last_processed_chat_name} | 焦点离开QQ窗口，重置聊天上下文。原聊天: {last_processed_chat_name}")
                            last_processed_chat_name = ""
                            chat_context.clear()
                            last_ocr_words = [] # Clear word history | 清除词汇历史

            except Exception as e:
                log_info(f"Exception: {str(e)} | 异常: {str(e)}")
            
            _time.sleep(0.5)
        log_info("Engine stopped. | 引擎已停止。")

# ---------- Tray and Configuration (Unchanged) | 托盘与配置 (保持不变) ----------
def create_dummy_icon():
    # return a simple placeholder icon (64x64) with an alpha channel
    width, height = 64, 64
    # RGBA mode ensures the tray icon is correctly handled on Windows
    images = Image.new('RGBA', (width, height), color=(0, 120, 215, 255))
    dc = ImageDraw.Draw(images)
    dc.rectangle([16, 16, 48, 48], fill=(255, 255, 255, 255))
    return images

def on_tray_quit(icon, item):
    icon.stop()
    if log_fp: log_fp.close()
    root.after(0, root.destroy)

def show_window(icon, item):
    icon.stop()
    root.after(0, root.deiconify)

def withdraw_window():
    # hide the main Tk window and create a system tray icon
    root.withdraw()
    global tray_icon

    # determine path of a shipped icon file relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(script_dir, "icon.ico")

    # load the image resource, fall back to dummy if missing or invalid
    if os.path.exists(ico_path):
        try:
            image = Image.open(ico_path)
        except Exception as e:
            log_info(f"Failed to open icon file '{ico_path}': {e}")
            image = create_dummy_icon()
    else:
        image = create_dummy_icon()

    # ensure the image has an alpha channel for proper display
    if image.mode != 'RGBA':
        try:
            image = image.convert('RGBA')
        except Exception:
            pass

    menu = pystray.Menu(
        pystray.MenuItem('Show Window | 显示窗口', show_window),
        pystray.MenuItem('Exit Program | 退出程序', on_tray_quit)
    )

    tray_icon = pystray.Icon("QQTool", image, "QQ Tool | QQ工具", menu)
    # use built-in detached runner rather than manually starting a thread
    try:
        tray_icon.run_detached()
    except Exception:
        # fallback for older pystray versions: spawn a thread
        threading.Thread(target=tray_icon.run, daemon=True).start()

def load_config():
    global time_interval, send_with_ctrl, input_length, ai_mode, api_key_global
    config = configparser.ConfigParser()
    if os.path.exists(INI_FILE):
        try:
            config.read(INI_FILE)
            if 'Settings' in config:
                time_interval = config.getfloat('Settings', 'interval', fallback=1.0)
                input_length = config.getint('Settings', 'input_length', fallback=10)
                send_with_ctrl = config.getboolean('Settings', 'send_with_ctrl', fallback=False)
                ai_mode = config.getboolean('Settings', 'ai_mode', fallback=False)
                api_key_global = config.get('Settings', 'api_key', fallback="") # Load API key | 加载API密钥
        except: pass

def save_config():
    global api_key_global
    config = configparser.ConfigParser()
    config['Settings'] = {
        'interval': str(time_interval),
        'input_length': str(input_length),
        'send_with_ctrl': str(send_with_ctrl),
        'ai_mode': str(ai_mode),
        'api_key': api_key_global # Save API key | 保存API密钥
    }
    with open(INI_FILE, 'w') as f: config.write(f)

def toggle_worker():
    global running, worker_thread, qq_initial_rect
    if running:
        running = False
        update_status("Stopped | 已停止", "blue")
    else:
        # when starting for the first time, capture current QQ window position
        windows = gw.getWindowsWithTitle('QQ')
        if windows:
            qq = windows[0]
            qq_initial_rect = (qq.left, qq.top, qq.width, qq.height)
            log_info(f"Initial QQ window rect recorded: {qq_initial_rect}")
        else:
            log_info("Unable to record initial QQ window rect: no QQ.exe found.")

        running = True
        worker_thread = threading.Thread(target=worker_logic, daemon=True)
        worker_thread.start()
        update_status("Running | 运行中", "green")

def clear_logs():
    if log_display: log_display.delete('1.0', tk.END)

# ---------- GUI ----------
def run_gui():
    global root, status_label, log_display, entry, api_key_global
    load_config()
    root = tk.Tk()
    root.title("QQ AI Auto Reply Assistant | QQ AI 自动回复助手")
    root.geometry("800x850")
    root.protocol('WM_DELETE_WINDOW', withdraw_window)

    main_frame = ttk.Frame(root, padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main_frame, text="Core Settings | 核心设置", font=("微软雅黑", 10, "bold")).pack(pady=5)
    
    # Mode switch | 模式开关
    frame_mode = ttk.Frame(main_frame)
    frame_mode.pack(fill=tk.X, pady=5)
    send_method_var = tk.BooleanVar(value=send_with_ctrl)
    ttk.Checkbutton(frame_mode, text="Send with Ctrl+Enter | Ctrl+Enter发送", variable=send_method_var).pack(side=tk.LEFT, padx=10)
    send_method_var_AI = tk.BooleanVar(value=ai_mode)
    ttk.Checkbutton(frame_mode, text="Enable AI Smart Reply | 启用 AI 智能回复", variable=send_method_var_AI).pack(side=tk.LEFT, padx=10)

    # Username | 用户名
    ttk.Label(main_frame, text="Set My Nickname (Anti-AI personality split): | 设置我的昵称 (防AI精神分裂):").pack(pady=(10,0))
    entry = ttk.Entry(main_frame)
    entry.pack(pady=5)
    ttk.Button(main_frame, text="Save Nickname | 保存昵称", command=save_value).pack(pady=2)

    # API Key Input Box | API Key 输入框
    ttk.Label(main_frame, text="AI Service API Key:\n(Please get from OpenAI or Siliconflow) | AI 服务 API Key:\n(请从 OpenAI 或 Siliconflow 获取)").pack(pady=(10,0))
    api_key_entry_var = tk.StringVar(value=api_key_global) # Bind API key variable | 绑定API密钥变量
    api_key_entry = ttk.Entry(main_frame, textvariable=api_key_entry_var, width=50, show='*') # Use show='*' to hide input | 使用show='*'隐藏输入
    api_key_entry.pack(pady=5)
    ttk.Button(main_frame, text="Update API Key | 更新API Key", command=lambda: [save_config(), messagebox.showinfo("Tip | 提示", "API Key updated | API Key已更新")]).pack(pady=2)

    # Other parameters | 其他参数
    frame_params = ttk.Frame(main_frame)
    frame_params.pack(fill=tk.X, pady=10)
    ttk.Label(frame_params, text="Detection Interval (s): | 检测间隔(s):").pack(side=tk.LEFT)
    interval_var = tk.DoubleVar(value=time_interval)
    ttk.Entry(frame_params, textvariable=interval_var, width=8).pack(side=tk.LEFT, padx=5)

    ttk.Label(frame_params, text="Random Characters: | 随机字符数:").pack(side=tk.LEFT, padx=(10,0))
    length_var = tk.IntVar(value=input_length)
    ttk.Entry(frame_params, textvariable=length_var, width=8).pack(side=tk.LEFT, padx=5)

    def apply():
        global time_interval, input_length, send_with_ctrl, ai_mode, api_key_global
        try:
            time_interval = interval_var.get()
            input_length = length_var.get()
            send_with_ctrl = send_method_var.get()
            ai_mode = send_method_var_AI.get()
            api_key_global = api_key_entry_var.get() # Get API key and update global variable | 获取API密钥并更新全局变量
            save_config()
            messagebox.showinfo("Success | 成功", "Configuration saved | 配置已保存")
        except tk.TclError as e: # Catch Tkinter specific errors for invalid input
            messagebox.showerror("Error | 错误", f"Invalid value or input format: {e} | 数值无效或输入格式错误: {e}")
        except Exception as e:
            messagebox.showerror("Error | 错误", f"Unknown error occurred while saving configuration: {e} | 保存配置时发生未知错误: {e}")
            


    ttk.Button(main_frame, text="Apply Configuration | 应用配置", command=apply).pack(pady=10)

    # Log | 日志
    status_label = tk.Label(main_frame, text="Status: Standby | 状态: 待机", fg="blue", font=("微软雅黑", 12))
    status_label.pack(pady=5)
    log_display = scrolledtext.ScrolledText(main_frame, height=20)
    log_display.pack(fill=tk.BOTH, expand=True)

    # Hotkey | 热键
    keyboard.add_hotkey("ctrl+alt+q", toggle_worker)
    
    root.mainloop()

if __name__ == "__main__":
    run_gui()