# QQ 状态极速刷屏小工具

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
python GUI.py
```

使用步骤  
1. 把 QQ 聊天窗口（或其他目标输入框）置于前台并保持焦点  

---

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
python GUI.py
```

Usage Steps:  
1. Bring the QQ chat window (or other target input field) to the foreground and keep it focused.  

---

## 3. 编译与打包指南（可选） | Build & Pack Guide (Optional)

- 如果目标机器不想装 Python 环境，可把脚本打成**单文件可执行程序**。  
- If the target machine has no Python, you can build a **single-file executable**.
- 需要虚拟环境。
- A virtual environment is required.


```bash
python -m nuitka --standalone --onefile --enable-plugin=tk-inter GUI.py
```


---

## 4. GUI

如果你不是个傻子，GUI 将是非常容易使用的，但不过你可能要懂一些英文。  
If you are not a fool, the GUI will be very easy to use.

---

## 5. Thanks

致所有用户：抱歉，由于作者第一次干，很多事还不是很完善。  
To all users: Sorry, since this is the author's first attempt, many things are not yet perfect.

---

## 6.Tips
- 请注意，当QQ未开启时，无法开启自动点击。
- Please note that auto-click cannot be enabled when QQ is not running.
- 如果你需要在linux上运行此程序，需更改进程校验逻辑，由于作者不太擅长linux，请自行解决或联系作者提交修改方案
- If you need to run this program on Linux, you need to modify the process verification logic. Since the author is not very familiar with Linux, please resolve it yourself or contact the author to submit a modification plan.
- 请在虚拟环境中安装nuitka库和keyboard库，或手动指定一份keyboard库。
- Please install the nuitka and keyboard libraries in a virtual environment, or manually specify a copy of the keyboard library.
- 你现在可以使用CLI/You can now use the CLI
- python GUI.py --cli -i 0.5 -d 30

