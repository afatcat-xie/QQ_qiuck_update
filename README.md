# QQ 状态极速刷屏小工具
# QQ Status Rapid Update Tool

---

## 1. 脚本作用 / Script Purpose
在 QQ 聊天窗口（或任意文本输入框）内以极快速度循环发送 8 位随机字符串，用于：
Rapidly sends 8-character random strings in the QQ chat window (or any text input field) in a loop, used for:
- **测试消息防刷屏限制** / Testing message anti-spam limits.
- **快速顶掉旧状态/公告** / Quickly replacing old status/announcements.
- **简单压测键盘事件响应** / Simple keyboard event response stress testing.

**⚠️ 仅供学习/测试，请勿在生产环境滥用！**
**⚠️ For learning/testing purposes only. Do not abuse in production environments!**

---

## 2. 环境搭建 / Environment Setup

强烈建议使用 **虚拟环境 (venv)** 来管理依赖，以避免污染系统全局 Python 环境。
It is highly recommended to use a **Virtual Environment (venv)** to manage dependencies and avoid conflicts with your system-wide Python.



### Windows (PowerShell / CMD)
1.  **创建虚拟环境 / Create the environment:**
    ```powershell
    python -m venv venv
    ```
2.  **激活虚拟环境 / Activate it:**
    - PowerShell: `.\venv\Scripts\Activate.ps1`
    - CMD: `.\venv\Scripts\activate.bat`
3.  **安装依赖 / Install dependencies:**
    ```bash
    pip install keyboard Pillow pystray
    ```

### Linux / macOS
1.  **创建虚拟环境 / Create the environment:**
    ```bash
    python3 -m venv venv
    ```
2.  **激活虚拟环境 / Activate it:**
    ```bash
    source venv/bin/activate
    ```
3.  **安装依赖 / Install dependencies:**
    ```bash
    pip install keyboard Pillow pystray
    ```

---

## 3. 运行指南 / Running the Tool

### 3.1 GUI 模式 (推荐) / GUI Mode (Recommended)
```bash
python GUI.py