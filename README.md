# QQ_quick_update.py —— QQ 状态极速刷屏小工具

## 1. 脚本作用
在 QQ 聊天窗口（或任意文本输入框）内以极快速度循环发送 8 位随机字符串，用于：
- 测试消息防刷屏限制
- 快速顶掉旧状态/公告
- 简单压测键盘事件响应

**⚠️ 仅供学习/测试，请勿在生产环境或公共群滥用，否则可能导致封号或打扰他人！**

---

## 2. 一键运行
```bash
# 克隆或下载脚本后，安装依赖
pip install keyboard

# 直接启动
python QQ_quick_update.py


使用步骤
把 QQ 聊天窗口（或其他目标输入框）置于前台并保持焦点
终端里运行脚本，看到提示「Script started, press F8 to stop.」即可开始
想停止时 按 F8，脚本会立即退出并打印「F8 pressed, script ended.」


——————————————————————————————————————————————-——————————————
#English
# QQ_quick_update.py — QQ Status Rapid Update Tool

## 1. Script Purpose
Rapidly sends 8-character random strings in the QQ chat window (or any text input field) in a loop, used for:
- Testing message anti-spam limits
- Quickly replacing old status/announcements
- Simple keyboard event response stress testing

**⚠️ For learning/testing purposes only. Do not abuse in production environments or public groups, as it may result in account suspension or disturbing others!**

---

## 2. One-Click Run
```bash
# After cloning or downloading the script, install dependencies
pip install keyboard

# Launch directly
python QQ_quick_update.py
```

Usage Steps:
1. Bring the QQ chat window (or other target input field) to the foreground and keep it focused.
2. Run the script in the terminal, you will see the prompt "Script started, press F8 to stop." and it will begin.
3. To stop, press F8, and the script will immediately exit and print "F8 pressed, script ended."