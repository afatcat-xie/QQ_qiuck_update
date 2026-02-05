---

# QQ 状态极速刷屏与 AI 智能助手

# QQ Status Rapid Update & AI Assistant

---

## 1. 脚本作用 / Script Purpose

本项目是一个基于 Python 的多功能辅助工具，支持两种核心模式：
This project is a multi-functional assistant tool based on Python, supporting two core modes:

* **极速刷屏模式 (Normal Mode)**: 在聊天窗口内循环发送指定长度的随机字符串。
Rapidly sends random strings of a specified length in a loop within the chat window.
* **AI 智能模式 (AI Mode)**: **[新增]** 自动捕获聊天窗口截图，通过 OpenAI 的视觉模型（Vision）分析对话内容并自动生成回复。
**[NEW]** Automatically captures chat window screenshots, analyzes conversations via OpenAI Vision models, and generates intelligent replies.

---

## 2. 环境搭建 / Environment Setup

### Windows (PowerShell / CMD)

1. **创建并激活虚拟环境 / Create & Activate venv:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```


2. **安装所有必要依赖 / Install dependencies:**
```bash
pip install keyboard Pillow pystray uiautomation pygetwindow pyautogui openai
```



---

## 3. 核心功能 / Key Features

* **AI 读屏回复 (AI Vision Reply)**: 自动定位 QQ 窗口并截图，利用 GPT-4o 等模型理解对话并回信。
Auto-locates QQ, takes screenshots, and uses GPT-4o to understand and reply.
* **对话记忆 (Context Memory)**: 支持保存最近 15 条对话记录，让 AI 回复更具逻辑。
Maintains the last 15 conversation records for contextual AI replies.
* **自动对齐 (Auto-Alignment)**: 启动时自动将 QQ 窗口移动至屏幕右侧，确保截图区域精确。
Snaps the QQ window to the right side of the screen for precise capturing.
* **配置持久化 (Config Persistence)**: API Key 和设置会自动保存至 `qq_config.ini`。
API Keys and settings are auto-saved to `qq_config.ini`.

---

## 4. 编译指南 (使用 Nuitka) / Compilation Guide (via Nuitka)

为了获得更好的运行性能并生成独立的可执行文件（.exe），推荐使用 **Nuitka**。
For better performance and creating a standalone executable (.exe), **Nuitka** is recommended.

### 4.1 安装编译工具 / Install Tools

```bash
pip install nuitka
```

*注意：首次编译时，Nuitka 会提示下载 MinGW64 编译器，请输入 `Yes`。*

### 4.2 编译命令 / Compilation Command

在项目根目录下执行以下命令：
Run this command in the project root:

```bash
python -m nuitka --onefile --windows-disable-console --standalone --enable-plugin=tk-inter --include-package=openai --include-package=PIL --include-package=keyboard --include-package=pystray --include-package=pygetwindow --include-package=pyautogui --include-package=uiautomation --include-data-dir=logs=logs --output-dir=dist GUI.py
```

**参数解析 / Parameter Explanation:**

* `--standalone`: 包含所有运行依赖。 / Include all runtime dependencies.
* `--onefile`: 打包为单个 .exe 文件。 / Package into a single .exe.
* `--windows-disable-console`: 隐藏背景黑框（只显示 GUI）。 / Hide the console window (GUI only).
* `--enable-plugin=tk-inter`: 确保窗口界面正常显示。 / Enable Tkinter plugin support.
* `--include-data-dir=logs=logs`: 自动创建日志文件夹。 / Include and create the logs directory.
* `--include-package`: 导入所有第三方库。 / Include all third-party packages.
---

## 5. 使用指南 / Usage Guide

1. **启动 / Start**: 运行 `python GUI.py` 或 `dist/GUI.exe`。
2. **配置 / Setup**: 在界面输入 **OpenAI API Key** 并勾选 **AI Mode**。
3. **准备窗口 / Preparation**: 确保 QQ 聊天窗口在桌面上可见（不要最小化）。
4. **快捷键 / Hotkeys**:
* `Ctrl+Alt+Q`: **开始运行 (Start)**
* `Ctrl+Alt+Q`: **停止运行 (Stop)**



---

## 6. 注意事项 / Important Notes

1. **窗口状态**: AI 模式要求窗口不能被其他程序完全遮挡。
**Window Status**: AI mode requires the window not to be fully obscured.
2. **安全性**: 请勿将包含 API Key 的 `qq_config.ini` 分享给他人。
**Security**: Do not share your `qq_config.ini` with others as it contains your API Key.
3. **误报处理**: 编译后的 `.exe` 可能会被杀毒软件误报，请添加至白名单。
**Antivirus**: The compiled `.exe` may trigger false positives; please whitelist it.

---

**⚠️ 仅供学习/测试，请勿在生产环境滥用！**
**⚠️ For learning/testing purposes only. Do not abuse in production!**

---