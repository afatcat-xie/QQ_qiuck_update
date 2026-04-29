# QQ 自动发送监控工具

一个功能强大的QQ自动消息发送工具，支持字典管理、全局快捷键、系统托盘等功能。

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10-blue)
![Platform](https://img.shields.io/badge/platform-Windows-brightgreen)

## 📋 功能特性

### 核心功能
- ✨ **自动发送** - 在QQ聊天框中自动输入并发送消息
- 📝 **字典管理** - 支持导入自定义字典文件，随机选择内容发送
- ⏱️ **可配置间隔** - 自定义消息发送频率（支持小数秒）
- 🔤 **随机字符** - 支持生成随机字符作为备选内容
- 🎛️ **发送方式** - 支持 Enter 或 Ctrl+Enter 发送

### 增强功能
- 🌐 **系统托盘** - 最小化到托盘运行，不占用任务栏
- ⌨️ **全局快捷键** - Ctrl+Alt+Q 快速启动/停止监控
- 📊 **实时日志** - 完整的运行日志记录和显示
- 💾 **配置保存** - 自动保存所有设置到 qq_config.ini
- 🔐 **多字典支持** - 加载多个字典文件，灵活启用/禁用

### 界面优化
- 🎨 **现代UI设计** - 基于Tkinter的清爽界面
- 📐 **响应式布局** - 自适应窗口大小
- 🎯 **字典显示** - 可滚动的字典列表，支持删除和状态管理

## 🚀 快速开始

### 系统要求
- Windows 7 及以上
- Python 3.10+（仅开发模式需要）

### 安装

#### 方法一：直接使用EXE（推荐）
1. 从 [Releases](../../releases) 下载最新的 `GUI.exe`
2. 直接运行，无需安装依赖

#### 方法二：从源代码运行

```bash
# 克隆仓库
git clone https://github.com/yourusername/QQ_qiuck_update.git
cd QQ_qiuck_update

# 安装依赖
pip install -r requirements.txt

# 运行
python GUI.py
```
### 基本设置

1. **启动应用** - 运行 GUI.exe 或 python GUI.py
2. **配置参数**
   - 设置发送间隔（秒）
   - 设置随机字符位数
   - 选择发送方式（Enter 或 Ctrl+Enter）
3. **点击"保存并应用配置"** 确认设置

### 字典管理

#### 添加字典
1. 点击「添加字典」按钮
2. 选择 UTF-8 格式的文本文件
3. 每行一个内容，程序自动加载

#### 启用/禁用字典
- 勾选「启用字典模式」激活字典功能
- 在字典列表中勾选/取消勾选单个字典
- 设置自动保存到配置文件

#### 删除字典
- 点击字典右侧的「删除」按钮
- 或点击「清除全部字典」移除所有字典

### 运行监控

1. **启动监控** - 点击「启动监控」按钮或按 Ctrl+Alt+Q
2. **查看状态** - 顶部状态标签显示实时状态
3. **查看日志** - 下方日志窗口记录所有操作
4. **停止监控** - 点击「停止监控」按钮或再次按 Ctrl+Alt+Q

### 系统托盘

- 点击窗口关闭按钮  最小化到托盘
- 托盘图标右键  「显示窗口」或「退出程序」

## 📋 配置文件格式

### qq_config.ini
```bash
[Settings]
interval = 1.0
input_length = 10
send_with_ctrl = False
enable_dictionary_mode = True
dictionary_files = path/to/dict1.txt;path/to/dict2.txt
dictionary_enabled = path/to/dict1.txt=True;path/to/dict2.txt=False
```

### 字典文件格式 (.txt)
`
内容1
内容2
内容3
`
- UTF-8 编码
- 每行一个内容
- 空行自动忽略

## 📦 依赖包

| 包名 | 用途 |
|------|------|
| keyboard | 全局快捷键支持 |
| Pillow | 图像处理 |
| pystray | 系统托盘 |
| pywin32 | Windows API调用 |
| psutil | 进程监控 |
| uiautomation | UI自动化 |
| Nuitka | 编译打包 |
| zstandard | onefile压缩 |
| easygui | 降低维护成本 |

## 🔧 开发

### 构建EXE

# 安装构建工具
```bash
pip install nuitka zstandard
```
# 构建
```bash
nuitka --onefile --windows-console-mode=disable --standalone 
  --enable-plugin=tk-inter --include-package=PIL 
  --include-package=keyboard --include-package=pystray 
  --include-package=psutil --include-package=uiautomation 
  --include-package=easygui
  --windows-icon-from-ico=icon.ico GUI.py
```

### GitHub Actions CI/CD
项目使用 GitHub Actions 自动构建和发布：
- 支持手动触发构建（填入发布说明）
- 自动上传到 Releases
- Python 3.10 编译环境
- zstandard 压缩优化
- icon.ico 自动打包

## ⚠️ 注意事项

1. **QQ窗口** - 程序只在QQ窗口获得焦点时工作
2. **输入框** - 只在文本输入框中发送，保护聊天记录区
3. **防护** - Ctrl+Alt+Q 快速停止，避免误操作
4. **权限** - 需要管理员权限启用键盘监控和托盘功能
5. **隐私** - 所有配置本地保存，不上传任何数据

## 📝 日志

- **日志位置** - ./logs/qq_monitor_YYYYMMDD_HHMMSS.log
- **自动生成** - 每次启动创建新日志文件
- **包含信息** - 发送内容、时间戳、状态变化、错误信息

## 🐛 故障排除

### 程序无法启动
- 检查Windows版本（需7+）
- 确保Python 3.10+ 已安装
- 以管理员身份运行
- 删掉用户目录下的app.lock

### 快捷键无效
- 检查是否以管理员身份运行
- 尝试更改快捷键组合
- 关闭可能冲突的应用

### 字典加载失败
- 确保文件格式为 UTF-8
- 检查文件路径是否包含中文
- 验证文件内容不为空

### 消息无法发送
- 确认QQ窗口处于焦点
- 验证输入框是否为文本编辑框
- 检查发送间隔设置

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ✨ 更新日志

### v2.0.0 (2026-04-19)
- ✨ 字典管理系统完整实现
- 🚀 自动化持续集成流程
- 🎨 界面优化和布局改进
- 🔧 依赖包更新和优化（移除openai）
- 📦 Nuitka 构建流程完善
- 🌐 系统托盘和全局快捷键支持

## 📧 技术支持

遇到问题？提交 Issue 获取帮助

---

**免责声明** - 此工具仅供学习和研究使用，使用者自行承担使用此工具的所有后果，作者不承担任何责任。
