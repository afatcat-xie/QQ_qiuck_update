# QQ_quick_update.py —— QQ 状态极速刷屏小工具

## 1. 脚本作用
在 QQ 聊天窗口（或任意文本输入框）内以极快速度循环发送 8 位随机字符串，用于：
- 测试消息防刷屏限制
- 快速顶掉旧状态/公告
- 简单压测键盘事件响应

**⚠️ 仅供学习/测试，请勿在生产环境或公共群滥用，否则可能导致封号或打扰他人！**

---

## 2. 一键运行

# 克隆或下载脚本后，安装依赖
pip install keyboard

# 直接启动
python QQ_quick_update.py


使用步骤
把 QQ 聊天窗口（或其他目标输入框）置于前台并保持焦点
终端里运行脚本，看到提示「Script started, press F8 to stop.」即可开始
想停止时 按 F8，脚本会立即退出并打印「F8 pressed, script ended.」




# QQ_quick_update.py — QQ Status Rapid Update Tool

## 1. Script Purpose
Rapidly sends 8-character random strings in the QQ chat window (or any text input field) in a loop, used for:
- Testing message anti-spam limits
- Quickly replacing old status/announcements
- Simple keyboard event response stress testing

**⚠️ For learning/testing purposes only. Do not abuse in production environments or public groups, as it may result in account suspension or disturbing others!**

---

## 2. One-Click Run

# After cloning or downloading the script, install dependencies
pip install keyboard

# Launch directly
python QQ_quick_update.py


Usage Steps:
1. Bring the QQ chat window (or other target input field) to the foreground and keep it focused.
2. Run the script in the terminal, you will see the prompt "Script started, press F8 to stop." and it will begin.
3. To stop, press F8, and the script will immediately exit and print "F8 pressed, script ended."



---

## 3. 编译与打包指南（可选） | Build & Pack Guide (Optional)

如果目标机器不想装 Python 环境，可把脚本打成**单文件可执行程序**。  
If the target machine has no Python, you can build a **single-file executable**.

---

### 3.1 安装打包工具 | Install PyInstaller
```bash
pip install -U pyinstaller
```

---

### 3.2 一键生成可执行文件 | One-command Build
```bash
# Windows → dist/QQ_quick_update.exe  
# Linux/macOS → dist/QQ_quick_update
pyinstaller -F -w QQ_quick_update.py \
            --name QQ_quick_update   \
            --hidden-import keyboard._winkeyboard
```

| 参数 | 中文说明 | English Description |
| ---- | -------- | ------------------- |
| `-F` | 单文件模式 | one-file bundle |
| `-w` | 无控制台窗口 | no console window (drop it if you want debug output) |
| `--hidden-import` | 打包 keyboard 钩子，避免运行报错 | include keyboard’s low-level hook to avoid `ImportError` |

---

### 3.3 编译完成 | Build Finished
输出文件在 `dist/` 目录：  
Output files are in `dist/`:
- **Windows**: `QQ_quick_update.exe`
- **Linux/macOS**: `QQ_quick_update` (no extension)

拷贝到同平台任意电脑，**双击或终端运行即可**，无需 Python 与第三方库。  
Copy to any same-OS computer and **double-click or run in terminal**—no Python required.

---

### 3.4 交叉编译提示 | Cross-compilation Note
PyInstaller **不支持跨平台交叉编译**。  
PyInstaller does **NOT** support cross-platform builds.  
需要 Windows `.exe` 请在 Windows 或 Windows CI 里打包。  
For Windows `.exe`, build on Windows or use a Windows CI (GitHub Actions, AppVeyor, etc.).

---

### 3.5 体积优化（可选）| Size Optimization (Optional)
```bash
pip install upx
pyinstaller -F -w QQ_quick_update.py --upx-dir=/usr/local/bin
```
可缩小 30–50 % 体积。  
Reduces file size by 30–50 %.
---
##4.GUI
如果你不是个傻子，GUI将是非常容易使用的，但不过你可能要懂一些英文。

If you are not a fool, the GUI will be very easy to use.
---
##5.Thanks
致所有用户：抱歉，由于作者第一次干，很多事还不是很完善

To all users: Sorry, since this is the author's first attempt, many things are not yet perfect.
