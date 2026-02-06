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

# New: Conversation history list | 新增：对话历史列表
chat_context = [] 
MAX_CONTEXT_LINES = 15 # How many recent screenshot records to show the AI | 给AI看最近多少次截图记录
MAX_REPLY_LENGTH = 20# New: Maximum character limit for AI replies | 新增：AI回复的最大字符数限制
last_processed_chat_name = "" # New: Records the name of the last processed chat, used for detecting switches | 新增：记录上一次处理的聊天名称，用于检测切换

# Event to signal immediate stop of worker/AI actions (used by hotkey to abort ongoing work)
stop_event = threading.Event()

INI_FILE = "qq_config.ini"
LOG_DIR = "logs"
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "chat_history.txt") # New: History record file (absolute path in script dir) | 新增：历史记录文件（脚本目录的绝对路径）

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Log initialization | 日志初始化
log_filename = f"qq_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
LOG_FILE = os.path.join(LOG_DIR, log_filename)
log_fp = open(LOG_FILE, "a", encoding="utf-8")

def log_info(message):
    """Thread-safe logging | 线程安全的日志记录"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    if log_fp:
        log_fp.write(f"[{full_timestamp}] [LOG] {message}\n")
        log_fp.flush()
    
    if log_display and root:
        try:
            root.after(0, lambda: (
                log_display.insert(tk.END, formatted_message + "\n"),
                log_display.see(tk.END)
            ))
        except: pass
    print(formatted_message)

def update_status(text, color):
    """Updates the status label on the GUI | 更新 GUI 上的状态标签"""
    if root and status_label:
        root.after(0, lambda: status_label.config(text=f"Status: {text} | 状态: {text}", fg=color))

# ---------- History Record Management (New) | 历史记录管理 (新增) ----------

# New: Chat history management with deduplication
def _update_chat_history_with_deduplication(group_chat_name_hint, chat_content_from_ocr):
    """
    Saves processed chat content to file and memory, with advanced deduplication.
    OCR结果处理：
    1. 分离群聊名称
    2. 将剩下的聊天内容以行作为基本单元进行去重与历史更新
    3. 如果新内容是旧内容的扩展，则更新旧内容
    4. 如果新内容包含旧内容，则替换旧内容
    5. 其他情况，追加新内容
    """
    global chat_context

    if not chat_content_from_ocr or not chat_content_from_ocr.strip():
        return False

    # Split by whitespace as requested; first token is forced group chat name
    tokens = [t for t in chat_content_from_ocr.split() if t.strip()]
    if not tokens:
        return False

    # If caller provided a group chat name hint, use it and keep all tokens as content.
    # Otherwise, treat tokens[0] as the group name and the rest as content.
    if group_chat_name_hint:
        group_name = group_chat_name_hint
        new_tokens = tokens
    else:
        group_name = tokens[0]
        new_tokens = tokens[1:]

    # Ensure the global chat_context keeps index 0 as group name
    if not chat_context:
        # Initialize with group name + tokens
        chat_context[:] = [group_name] + new_tokens
    else:
        # Replace/force the group name at position 0
        chat_context[0] = group_name

    existing_tokens = chat_context[1:]
    # If no new tokens (only group name), nothing else to update
    if not new_tokens:
        return False

    # Find the longest common contiguous subsequence between new_tokens and existing_tokens
    best_len = 0
    best_existing_start = -1
    best_new_start = -1
    for e_start in range(len(existing_tokens)):
        for n_start in range(len(new_tokens)):
            l = 0
            while e_start + l < len(existing_tokens) and n_start + l < len(new_tokens) and existing_tokens[e_start + l] == new_tokens[n_start + l]:
                l += 1
            if l > best_len:
                best_len = l
                best_existing_start = e_start
                best_new_start = n_start

    if best_len > 0:
        # Delete the overlapping range from existing_tokens (indices best_existing_start .. best_existing_start+best_len-1)
        insert_pos = 1 + best_existing_start  # position in chat_context to insert new sequence
        del chat_context[insert_pos: insert_pos + best_len]
        # Insert the full new_tokens at insert_pos, so numbering inherits deleted range start
        for idx, tok in enumerate(new_tokens):
            chat_context.insert(insert_pos + idx, tok)
    else:
        # No overlap found: append new tokens to the end, preserving group name at index 0
        chat_context.extend(new_tokens)

    # Trim to MAX_CONTEXT_LINES if needed, but preserve group name at index 0
    while len(chat_context) > MAX_CONTEXT_LINES:
        # remove from the end
        chat_context.pop()

    # Write updated numbered history to file
    try:
        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"\n--- [Record Time: {timestamp} | Group: {group_name}] ---\n")
            for i, entry in enumerate(chat_context):
                f.write(f"{i+1}: {entry}\n")
            f.write('\n')
        log_info(f"Chat history updated (file and cache), current cache entries: {len(chat_context)} | 历史记录已更新 (文件和缓存)，当前缓存条数: {len(chat_context)}")
        return True
    except Exception as e:
        log_info(f"Failed to save chat history: {e} | 保存历史记录失败: {e}")
        return True

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
    windows = gw.getWindowsWithTitle('QQ')
    if not windows:
        log_info("QQ window not found. | 未找到QQ窗口。")
        return False
    
    qq = windows[0]
    
    if qq.isMinimized:
        qq.restore()
    qq.activate()
    _time.sleep(0.5) # Allow activation to settle

    if reposition_right_if_needed:
        screen_width, screen_height = pyautogui.size()
        right_half_left_edge_target = screen_width / 2
        
        # Check if QQ window is approximately snapped to the right half
        # We allow a small tolerance for pixel variations
        # 检查QQ窗口是否大致吸附到右半边
        # 我们允许像素变化有小的容差
        is_snapped_right = False
        if abs(qq.left - right_half_left_edge_target) < 10 and abs(qq.width - right_half_left_edge_target) < 10:
             is_snapped_right = True

        if not is_snapped_right:
            log_info("QQ window is not on the right or not properly docked, executing Win+Right shortcut to adjust position. | QQ窗口不在右侧或未正确停靠，执行Win+Right快捷键以调整位置。")
            keyboard.press_and_release('win+right')
            _time.sleep(0.8) # Wait for window to reposition
            # Re-get window object after repositioning to update its coordinates
            # 重新获取窗口对象以在重定位后更新其坐标
            windows = gw.getWindowsWithTitle('QQ')
            if windows:
                qq = windows[0]
            else:
                log_info("Warning: QQ window disappeared after repositioning. Skipping screenshot. | 警告: QQ窗口在调整位置后消失。跳过截图。")
                return False
        else:
            log_info("QQ window is already on the right and properly docked, skipping Win+Right shortcut. | QQ窗口已在右侧并正确停靠，跳过Win+Right快捷键。")
            
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
    save_config() # Save configuration after updating name | 更新名称后保存配置
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
                        {"type": "text", "text": "Convert the document to markdown."}
                    ]
                }
            ]
        )
        text_content = response_obj.choices[0].message.content
        return text_content
    except Exception as e:
        log_info(f"OCR Error: {e}")
        return ""

def AI2_Generate_Reply(ocr_chat_name_hint=""): # New parameter ocr_chat_name_hint | 新增参数 ocr_chat_name_hint
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
    full_context_str = "\n".join(chat_context)

    # Build AI's current chat environment information | 构建AI的当前聊天环境信息
    if ocr_chat_name_hint:
        current_identity_for_ai = f"The current chat object/group chat mainly appears as 【{ocr_chat_name_hint}】. | 当前聊天对象/群聊主要显示为【{ocr_chat_name_hint}】。"
        if last_processed_chat_name and last_processed_chat_name != "QQ" and last_processed_chat_name != ocr_chat_name_hint:
            current_identity_for_ai += f"The window name detected by the system is 【{last_processed_chat_name}】. | 系统检测的窗口名称是【{last_processed_chat_name}】。"
    elif last_processed_chat_name and last_processed_chat_name != "QQ":
        current_identity_for_ai = f"The current chat name detected by the system is 【{last_processed_chat_name}】. | 系统检测的当前聊天名称是【{last_processed_chat_name}】。"
    elif last_processed_chat_name == "QQ":
        current_identity_for_ai = "The current chat window title is the generic name 【QQ】. | 当前聊天窗口标题为通用名称【QQ】。"


    system_prompt = f"""
Ignore all LV*, they represent levels; only focus on the specific names that follow as roles. | 忽略所有LV*，它们是等级，只能关注后面的具体名称作为角色。
You are a chat assistant. Your role is 【{saved_name}】, please reply from the perspective and identity of 【{saved_name}】. | 你是一个聊天助手。你的角色是【{saved_name}】，请以【{saved_name}】的视角和身份进行回复。
The current chat context is: {current_identity_for_ai}
You need to read the 【numbered chat history records】 I provide. | 你需要阅读我提供的【带编号的聊天记录历史】。
Note: These records are processed and de-duplicated. You should analyze the conversation logic based on these numbered lines. | 注意：这些记录是经过处理和去重后的。你需要根据这些带编号的行来分析对话逻辑。

Please predict and output my next reply based on the latest conversation progress. | 请根据最新的对话进展，预测并输出我的下一句回复。
Requirements: | 要求：
1. Only output the reply content, do not output the analysis process. | 1. 只输出回复内容，不要输出分析过程。
2. If the other party has ended the topic or no reply is needed, output "PASS". | 2. 如果对方已经结束话题或不需要回复，输出 "PASS"。
3. The tone of voice should be natural. | 3. 语气要自然。
4.话要短，20个字以内，符合年轻人的聊天习惯

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
    with auto.UIAutomationInitializerInThread(debug=False):
        stop_event.clear()
        log_info("Core monitoring engine started... | 核心监控引擎已启动...")
        
        while running:
            if stop_event.is_set():
                log_info("Stop event set, exiting worker loop immediately. | 收到停止事件，立即退出工作循环。")
                break
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
                else:
                    ctrl_type = el.ControlTypeName
                    try:
                        window = el.GetTopLevelControl()
                        win_title = window.Name if window else "Unknown | 未知"
                    except: win_title = "Unknown | 未知"

                    if win_title and "QQ" == win_title and "\\" not in win_title:
                        # Try to get chat name from EditControl (input box) instead of OCR/window title
                        chat_name_detected = ""
                        try:
                            if ctrl_type == 'EditControl' and getattr(el, 'Name', None):
                                chat_name_detected = el.Name.split('(')[0].strip() if '(' in el.Name else el.Name.strip()
                            else:
                                # Search children of top-level window for an EditControl holding chat name
                                if window:
                                    for child in window.GetChildren():
                                        if child.ControlTypeName == 'EditControl' and getattr(child, 'Name', None) and child.Name != "QQ":
                                            chat_name_detected = child.Name.split('(')[0].strip() if '(' in child.Name else child.Name.strip()
                                            break
                        except Exception as e:
                            log_info(f"Error detecting chat name from EditControl: {e}")
                        
                        # Fallback to window title if no edit control name found
                        if not chat_name_detected:
                            current_chat_name_from_title = win_title.split('(')[0].strip() if '(' in win_title else win_title.strip()
                            chat_name_detected = current_chat_name_from_title
                            log_info(f"Using window title as fallback for chat name detection: '{chat_name_detected}'")
                        else:
                            current_chat_name_from_title = chat_name_detected
                            log_info(f"Using EditControl name for chat detection: '{current_chat_name_from_title}'")
                        
                        if current_chat_name_from_title != last_processed_chat_name:
                            log_info(f"Chat switch detected! From '{last_processed_chat_name if last_processed_chat_name else 'None | 无'}' to '{current_chat_name_from_title}'. | 检测到聊天切换！从 '{last_processed_chat_name if last_processed_chat_name else '无'}' 切换到 '{current_chat_name_from_title}'。")
                            last_processed_chat_name = current_chat_name_from_title
                            chat_context.clear() # Clear conversation history when switching chats | 切换聊天时清空对话历史

                            log_info("Chat history context cleared. | 已清空聊天历史上下文。")

                        if ctrl_type == 'DocumentControl':
                            update_status("Input prohibited in document area | 禁止在文档区输入", "red")
                        
                        elif ctrl_type in VALID_CONTROL_TYPES:
                            
                            # =========== AI Mode | AI 模式 ===========
                            if ai_mode:
                                if stop_event.is_set():
                                    log_info("Stop requested before AI actions, skipping AI mode. | 在AI操作前收到停止请求，跳过AI模式。")
                                    break
                                log_info(f"【AI Mode】Chat window '{current_chat_name_from_title}' detected... | 【AI模式】检测到聊天窗口 '{current_chat_name_from_title}'...") 
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

                                if stop_event.is_set():
                                    log_info("Stop requested before screenshot, aborting AI actions. | 在截图前收到停止请求，放弃AI操作。")
                                    break
                                if capture_qq_with_padding(reposition_right_if_needed=True): # Pass True for conditional repositioning | 传递True以条件性重定位
                                    crop_center_chat_no_header("qq_trimmed.png", "image.png")
                                    image_to_base64("image.png")
                                    
                                    # 2. OCR Recognition | 2. OCR 识别
                                    if stop_event.is_set():
                                        log_info("Stop requested before OCR, aborting AI actions. | 在OCR前收到停止请求，放弃AI操作。")
                                        break
                                    current_ocr_text = AI1_OCR()
                                    log_info(f"OCR Recognition Result:\n{current_ocr_text} | OCR识别结果:\n{current_ocr_text}")
                                    
                                    # --- Use EditControl / window title as chat name hint (no longer using OCR for name) ---
                                    ocr_chat_name_hint = current_chat_name_from_title
                                    log_info(f"Using EditControl/window title as group chat name: {ocr_chat_name_hint} | 使用输入框控件名/窗口标题作为群聊名称: {ocr_chat_name_hint}")
                                        
                                    # The full OCR text (with original line breaks) will be used for deduplication.
                                    chat_content_for_deduplication = current_ocr_text
                                    # --- End OCR chat name slice and content splitting | 结束 OCR 聊天名称切片和内容拆分 ---

                                    # 3. Update history and judge if there's new content, only consider replying when new content appears
                                    # 3. 更新历史并判断是否有新内容，只有在新内容出现时才考虑回复
                                    if _update_chat_history_with_deduplication(ocr_chat_name_hint, chat_content_for_deduplication): 
                                        log_info(f"History for '{last_processed_chat_name}' updated, generating reply... | 已更新 '{last_processed_chat_name}' 的历史记录，生成回复中...")
                                        # 4. Generate reply based on history | 4. 基于历史生成回复
                                        # Pass ocr_chat_name_hint to AI2_Generate_Reply (Note: API key replaced with placeholder)
                                        # 将 ocr_chat_name_hint 传递给 AI2_Generate_Reply (注意API密钥已替换为占位符)
                                        if stop_event.is_set():
                                            log_info("Stop requested before generating reply, aborting generation. | 在生成回复前收到停止请求，放弃生成。")
                                            break
                                        reply_text = AI2_Generate_Reply(ocr_chat_name_hint=ocr_chat_name_hint)
                                        
                                        # --- Limit AI reply max length --- | --- 限制 AI 回复的最大长度 ---
                                        if len(reply_text) > MAX_REPLY_LENGTH:
                                            reply_text = reply_text[:MAX_REPLY_LENGTH - 3] + "..." # Truncate and add ellipsis | 截断并添加省略号
                                            log_info(f"AI reply content too long, truncated to {MAX_REPLY_LENGTH} characters. | AI回复内容过长，已截断至 {MAX_REPLY_LENGTH} 字符。")

                                        if reply_text and "PASS" not in reply_text and len(reply_text) > 0:
                                            log_info(f"AI decided to reply: {reply_text} | AI 决定回复: {reply_text}")
                                            prefixed_reply_text = f"AI回复: {reply_text}"
                                            log_info(f"Preparing to send AI reply: '{prefixed_reply_text}' | 准备发送AI回复: '{prefixed_reply_text}'")
                                            if stop_event.is_set():
                                                log_info("Stop requested before sending reply, aborting send. | 在发送回复前收到停止请求，放弃发送。")
                                                break
                                            keyboard.write(prefixed_reply_text)
                                            if send_with_ctrl:
                                                keyboard.press_and_release('ctrl+enter')
                                            else:
                                                keyboard.press_and_release('enter')
                                            
                                            update_status("AI replied successfully | AI 回复成功", "green")
                                            replied_this_cycle = True # Mark as replied | 标记已回复
                                            
                                            # --- Key modification: after AI replies, rescreenshot and re-OCR to update chat_context
                                            # This is crucial for avoiding the AI repeatedly replying to its own content.
                                            # --- 关键修改：AI 回复后，重新截图并重新OCR以更新 chat_context
                                            # 这对于避免AI重复回复自身内容至关重要。
                                            log_info("AI has finished replying, rescreenshotting to update baseline recognition content to avoid self-repeated replies... | AI已完成回复，重新截图更新基准识别内容，避免自我重复回复...")
                                            _time.sleep(1.0) # Wait for message to send and display on screen | 等待消息发送并显示到屏幕
                                            if stop_event.is_set():
                                                log_info("Stop requested after send, skipping post-reply rescreenshot. | 发送后收到停止请求，跳过回复后的重新截图。")
                                                continue
                                            if capture_qq_with_padding(reposition_right_if_needed=False): # This screenshot only gets current status, no need to reposition again | 此次截图仅获取当前状态，无需再次重定位
                                                crop_center_chat_no_header("qq_trimmed.png", "image.png")
                                                image_to_base64("image.png")
                                                post_reply_ocr_text = AI1_OCR()

                                                # Re-process the content after AI reply to update chat_context and ensure deduplication
                                                # 重新处理AI回复后的内容，以更新 chat_context 并确保去重
                                                post_reply_ocr_chat_name_hint = current_chat_name_from_title
                                                post_reply_chat_content_for_deduplication = post_reply_ocr_text
                                                post_reply_first_line_parts = post_reply_ocr_text.split(None, 1)
                                                if len(post_reply_first_line_parts) > 0:
                                                    potential_group_name_post_reply = post_reply_first_line_parts[0].strip()
                                                    if potential_group_name_post_reply:
                                                        post_reply_ocr_chat_name_hint = potential_group_name_post_reply
                                                        if len(post_reply_first_line_parts) > 1:
                                                            post_reply_chat_content_for_deduplication = post_reply_first_line_parts[1].strip()
                                                        else:
                                                            post_reply_chat_content_for_deduplication = ""

                                                _update_chat_history_with_deduplication(post_reply_ocr_chat_name_hint, post_reply_chat_content_for_deduplication)
                                                log_info(f"Baseline recognition content updated (including AI reply). | 基准识别内容已更新 (包含AI回复)。")
                                            else:
                                                log_info("Warning: Rescreenshot failed after AI reply, may cause AI to repeatedly reply to its own content in the next loop. | 警告: AI回复后重新截图失败，可能导致下一次循环中AI重复回复自身内容。")
                                            # --- End update after AI reply | 结束 AI 回复后更新 ---

                                        else:
                                            log_info("AI decided to remain silent (PASS). | AI 决定保持沉默 (PASS)。")
                                            update_status("AI standby (no reply) | AI 待机中 (无回复)", "blue")
                                    else:
                                        log_info("No new message or content is duplicated with previous record, skipping reply. | 无新消息或内容与上一记录重复，跳过回复。")
                                        update_status("Monitoring (no necessary reply) | 监控中 (非必要回复)", "blue")

                                # If no AI reply was made this round, set the last OCR result as the baseline for the next round
                                # 如果本轮没有进行 AI 回复，则将上次 OCR 结果作为下一轮的基准
                                # Removed: last_ocr_words logic is now handled by _update_chat_history_with_deduplication
                                
                                else:
                                    log_info("Screenshot failed, unable to perform AI analysis. | 截图失败，无法进行AI分析.")
                                    update_status("AI: Screenshot failed | AI: 截图失败", "red")

                                # AI mode cooldown time | AI 模式的冷却时间
                                _time.sleep(max(2.0, time_interval))

                            # =========== Random Character Mode | 随机字符模式 ===========
                            else:
                                text_to_send = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(input_length))
                                log_info(f"Preparing to send random characters: '{text_to_send}' | 准备发送随机字符: '{text_to_send}'")
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

            except Exception as e:
                log_info(f"Exception: {str(e)} | 异常: {str(e)}")
            
            _time.sleep(0.5)
        log_info("Engine stopped. | 引擎已停止。")

# ---------- Tray and Configuration (Unchanged) | 托盘与配置 (保持不变) ----------
def create_dummy_icon():
    width, height = 64, 64
    images = Image.new('RGB', (width, height), color=(0, 120, 215))
    dc = ImageDraw.Draw(images)
    dc.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
    return images

def on_tray_quit(icon, item):
    icon.stop()
    if log_fp: log_fp.close()
    root.after(0, root.destroy)

def show_window(icon, item):
    icon.stop()
    root.after(0, root.deiconify)

def withdraw_window():
    root.withdraw()
    global tray_icon
    image = create_dummy_icon()
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        try:
            image = Image.open(icon_path)
        except Exception as e:
            log_info(f"Failed to load icon from {icon_path}: {e} | 从 {icon_path} 加载图标失败: {e}")
    menu = (pystray.MenuItem('Show Window | 显示窗口', show_window), pystray.MenuItem('Exit Program | 退出程序', on_tray_quit))
    tray_icon = pystray.Icon("QQTool", image, "QQ Tool | QQ工具", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

def load_config():
    global time_interval, send_with_ctrl, input_length, ai_mode, api_key_global, saved_name
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
                saved_name = config.get('Settings', 'saved_name', fallback="User") # Load saved name | 加载保存的名称
        except: pass

def save_config():
    global api_key_global, saved_name
    config = configparser.ConfigParser()
    config['Settings'] = {
        'interval': str(time_interval),
        'input_length': str(input_length),
        'send_with_ctrl': str(send_with_ctrl),
        'ai_mode': str(ai_mode),
        'api_key': api_key_global, # Save API key | 保存API密钥
        'saved_name': saved_name # Save saved name | 保存保存的名称
    }
    with open(INI_FILE, 'w') as f: config.write(f)

def toggle_worker():
    global running, worker_thread, stop_event
    if running:
        # Signal immediate stop and flip running flag
        running = False
        stop_event.set()
        update_status("Stopped | 已停止", "blue")
        log_info("Stop requested via hotkey: worker will terminate ASAP. | 通过热键请求停止: 工作线程将尽快终止。")
    else:
        # Clear any previous stop request and start
        stop_event.clear()
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
    entry.insert(0, saved_name) # Display the loaded name | 显示加载的名称
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