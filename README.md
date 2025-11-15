

```markdown
# QQ 状态极速刷屏小工具
# QQ Status Rapid Update Tool

---

## 1. 脚本作用 / Script Purpose
在 QQ 聊天窗口（或任意文本输入框）内以极快速度循环发送 8 位随机字符串，用于：
Rapidly sends 8-character random strings in the QQ chat window (or any text input field) in a loop, used for:
- 测试消息防刷屏限制 / Testing message anti-spam limits
- 快速顶掉旧状态/公告 / Quickly replacing old status/announcements
- 简单压测键盘事件响应 / Simple keyboard event response stress testing

**⚠️ 仅供学习/测试，请勿在生产环境或公共群滥用，否则可能导致封号或打扰他人！**
**⚠️ For learning/testing purposes only. Do not abuse in production environments or public groups, as it may result in account suspension or disturbing others!**

---

## 2. 一键运行 / One-Click Run

### 2.1 GUI 模式 / GUI Mode
```bash
# 克隆或下载脚本后，安装依赖
# After cloning or downloading the script, install dependencies
pip install keyboard

# 启动 GUI 界面
# Launch the GUI interface
python GUI.py
```

**使用步骤:**
**Usage Steps:**
1.  **启动程序:** 运行 `python GUI.py`。
    **Launch the program:** Run `python GUI.py`.
2.  **关注 QQ:** 将 QQ 聊天窗口（或其他目标输入框）置于前台并保持焦点。
    **Focus on QQ:** Bring the QQ chat window (or other target input field) to the foreground and keep it focused.
3.  **点击 Start:** 确保 QQ.exe 正在运行（GUI 会自动检测），然后点击 "Start" 按钮。
    **Click Start:** Ensure `QQ.exe` is running (GUI will auto-detect), then click the "Start" button.
4.  **停止程序:** 点击 "Stop" 按钮，或使用热键 `Ctrl + Alt + Q` (切换) / `F8` (停止)，或直接关闭 GUI 窗口。
    **Stop the program:** Click the "Stop" button, or use hotkeys `Ctrl + Alt + Q` (Toggle) / `F8` (Stop), or close the GUI window directly.

### 2.2 CLI (命令行) 模式 / CLI (Command-Line) Mode
如果不需要 GUI，可以直接使用命令行模式。
If you don't need the GUI, you can use the command-line mode directly.

```bash
# 启动 CLI 模式
# Launch CLI mode
python GUI.py --cli
```

**常用选项 / Common Options:**
-   `-i` 或 `--interval` <秒数> / <seconds>: 设置发送间隔（默认为 1.0 秒）。例如: `python GUI.py --cli -i 0.5`
    Set sending interval (default 1.0 second). Example: `python GUI.py --cli -i 0.5`
-   `-d` 或 `--duration` <秒数> / <seconds>: 设置运行总时长（秒），到时自动停止（留空则不限时）。例如: `python GUI.py --cli -d 30`
    Set the total running duration (seconds), stops automatically when time is up (leave blank for unlimited). Example: `python GUI.py --cli -d 30`

**CLI 模式下的热键:**
**Hotkeys in CLI Mode:**
-   `Ctrl + Alt + Q`: 切换开始/停止刷屏。
    Toggle start/stop spamming.
-   `F8`: 停止刷屏。
    Stop spamming.
-   `Ctrl + C`: 强制退出程序。
    Force exit the program.

---

## 3. 编译与打包指南（可选） / Build & Pack Guide (Optional)

- 如果目标机器不想装 Python 环境，可把脚本打成**单文件可执行程序**。
- If the target machine has no Python, you can build a **single-file executable**.
- **注意:** 编译前请确保在虚拟环境中安装了 `nuitka` 和 `keyboard` 库。
- **Note:** Ensure `nuitka` and `keyboard` libraries are installed in a virtual environment before compiling.

```bash
# 建议在虚拟环境中执行
# Recommended to execute in a virtual environment
python -m nuitka --standalone --onefile --enable-plugin=tk-inter GUI.py
```

---

## 4. GUI 界面说明 / GUI Interface Explanation

GUI 界面提供了直观的操作选项：
The GUI interface provides intuitive operational options:
-   **Interval (seconds):** 设置每次发送随机字符串之间的时间间隔。
    Set the time interval between sending random strings.
-   **Duration (seconds):** 设置脚本运行的总时长，留空表示不限制时长。
    Set the total duration for the script to run; leave blank for unlimited duration.
-   **Start/Stop 按钮:** 控制脚本的开始和停止。
    **Start/Stop Buttons:** Control the start and stop of the script.
-   **Status:** 显示当前脚本的状态（Stopped / Running / Hotkey Error）。
    **Status:** Displays the current script status (Stopped / Running / Hotkey Error).
-   **Tips:** 提示当前聚焦的窗口（QQ 等）以及可用的热键。
    **Tips:** Provides hints about the currently focused window (QQ, etc.) and available hotkeys.

GUI 窗口可以被隐藏，程序仍在后台运行，可通过热键 `Ctrl + Alt + Q` 唤醒或切换状态。
The GUI window can be hidden; the program will continue to run in the background. You can wake it up or toggle its state via the hotkey `Ctrl + Alt + Q`.

---

## 5. Thanks / 致谢

致所有用户：抱歉，由于作者第一次干，很多事还不是很完善。
To all users: Sorry, since this is the author's first attempt, many things are not yet perfect.

---

## 6. Tips / 小贴士

-   **QQ 检测 / QQ Detection:** 程序会自动检测 `QQ.exe` 是否运行。只有当 `QQ.exe` 运行时，GUI 上的 "Start" 按钮才会启用，CLI 模式下若 QQ 未运行，脚本将暂停等待。
    The program automatically detects if `QQ.exe` is running. The "Start" button on the GUI will only be enabled when `QQ.exe` is running. In CLI mode, if QQ is not running, the script will pause and wait.
-   **Linux 支持 / Linux Support:** 作者不太擅长 Linux，若需要在 Linux 上运行，可能需要更改进程校验逻辑。请自行解决或联系作者提交修改方案。
    The author is not very proficient with Linux. If you need to run this on Linux, you may need to modify the process verification logic. Please resolve it yourself or contact the author to submit a modification plan.
-   **库安装 / Library Installation:** 请在虚拟环境中安装 `keyboard` 库。编译打包时，`nuitka` 也建议在虚拟环境中安装。
    Please install the `keyboard` library in a virtual environment. When compiling and packaging, it is also recommended to install `nuitka` in a virtual environment.
-   **CLI/GUI 切换 / CLI/GUI Switching:** 你可以使用 `python GUI.py --cli` 来启动命令行模式，或者直接运行 `python GUI.py` 来启动 GUI 模式。
    You can use `python GUI.py --cli` to launch in command-line mode, or simply run `python GUI.py` to launch in GUI mode.
-   **GUI 隐藏/显示 / GUI Hiding/Showing:** GUI 窗口可以通过其关闭按钮（X）隐藏。程序将继续在后台运行，可通过热键 `Ctrl + Alt + Q` 切换状态，或使用 `F8` 停止。
    The GUI window can be hidden via its close button (X). The program will continue running in the background. You can toggle its state via the hotkey `Ctrl + Alt + Q`, or stop it using `F8`.

---

## 7. 热键支持 / Hotkey Support

为了更便捷地控制程序，支持以下全局热键：
For more convenient program control, the following global hotkeys are supported:

-   `Ctrl + Alt + Q` (或 `^!q`): **切换**脚本运行状态。如果脚本正在运行，它将停止；如果脚本已停止，它将尝试启动（需要 QQ 运行且 GUI 窗口在焦点）。
    `Ctrl + Alt + Q` (or `^!q`): **Toggles** the script's running state. If the script is running, it will stop; if it's stopped, it will attempt to start (requires QQ to be running and the GUI window to have focus).
-   `F8`: **停止**脚本。此热键仅用于停止，不会启动脚本。
    `F8`: **Stops** the script. This hotkey is only for stopping and will not start the script.
-   `Ctrl + C`: 在 **CLI 模式**下，用于强制退出程序。
    `Ctrl + C`: In **CLI mode**, used to force exit the program.

**注意 / Note:**
-   热键将在程序启动时注册，并在程序退出时解除。
    Hotkeys are registered when the program starts and unhooked upon program exit.
-   如果 GUI 窗口被隐藏，热键仍可正常工作。
    If the GUI window is hidden, hotkeys will still function correctly.

