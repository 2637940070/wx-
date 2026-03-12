# 🖥️ 窗口文字监控自动回复工具

一个基于 Python 的通用桌面窗口文字监控工具，能够监控任意窗口中的文字内容，当检测到预设的关键字后，自动模拟键盘输入发送预设的回复消息。

---

## ✨ 功能特性

- 📋 **窗口选择**：自动列出系统中所有可见窗口，用户从下拉框选择目标监控窗口
- 🔍 **OCR 文字识别**：定时对目标窗口截图，使用 Tesseract OCR 提取文字内容
- 🎯 **关键字匹配**：检测文字中是否包含预设关键字，支持多组规则，冷却机制防止重复触发
- 💬 **自动回复**：检测到关键字后自动激活目标窗口，通过剪贴板粘贴方式发送中文回复
- ⚙️ **配置管理**：JSON 配置文件持久化存储规则，GUI 中支持增删改规则
- 📝 **日志记录**：实时在界面显示运行日志，同时写入 `logs/monitor.log` 文件

---

## 📁 项目结构

```
├── README.md              # 项目说明文档（本文件）
├── requirements.txt       # Python 依赖
├── config.json            # 默认配置文件（关键字-回复规则）
├── main.py                # 程序入口
├── monitor/
│   ├── __init__.py
│   ├── window_manager.py  # 窗口管理（列举、选择、截图）
│   ├── ocr_engine.py      # OCR 文字识别引擎
│   ├── keyword_matcher.py # 关键字匹配逻辑（含冷却机制）
│   ├── auto_sender.py     # 自动发送消息（模拟键盘）
│   └── config_manager.py  # 配置文件管理
├── gui/
│   ├── __init__.py
│   └── main_window.py     # tkinter 主窗口界面
└── logs/
    └── .gitkeep           # 日志目录（运行后自动生成 monitor.log）
```

---

## 🔧 安装步骤

### 1. 安装 Python

确保已安装 **Python 3.8 或更高版本**。

可从 [https://www.python.org/downloads/](https://www.python.org/downloads/) 下载。

### 2. 安装 Tesseract OCR（Windows）

Tesseract OCR 是本工具进行文字识别的核心依赖，**必须单独安装**。

1. 访问下载页面：[https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
2. 下载最新版本的 Windows 安装程序（例如 `tesseract-ocr-w64-setup-5.x.x.exe`）
3. 运行安装程序，**安装时勾选 "Additional language data" 中的 "Chinese (Simplified)"**（简体中文）
4. 安装完成后，默认路径为：`C:\Program Files\Tesseract-OCR\tesseract.exe`
5. 建议将 `C:\Program Files\Tesseract-OCR` 添加到系统环境变量 `PATH` 中

> ⚠️ 如果不安装 Tesseract，程序将无法进行 OCR 文字识别，但仍可启动（只是无法检测窗口文字）。

### 3. 安装 Python 依赖

在项目根目录下运行：

```bash
pip install -r requirements.txt
```

依赖列表：

| 包名 | 用途 |
|------|------|
| `pyautogui` | 模拟键盘鼠标操作 |
| `pygetwindow` | 跨平台窗口管理 |
| `Pillow` | 图像处理和窗口截图 |
| `pytesseract` | OCR 文字识别（Tesseract 的 Python 封装） |
| `pyperclip` | 剪贴板操作（用于发送中文） |

---

## 🚀 使用说明

### 启动程序

```bash
python main.py
```

### 界面操作

1. **选择目标窗口**：在「目标窗口选择」区域的下拉框中选择要监控的窗口。点击「刷新窗口列表」可更新列表。

2. **管理规则**：
   - 点击「➕ 添加规则」添加新的关键字-回复规则
   - 选中规则后点击「✏️ 编辑规则」修改
   - 选中规则后点击「🔄 切换启用」启用或禁用该规则
   - 选中规则后点击「🗑️ 删除规则」删除

3. **调整参数**：
   - **监控间隔**：每次截图的时间间隔（默认 3 秒）
   - **冷却时间**：同一关键字再次触发的等待时间（默认 30 秒）
   - **发送延迟**：发送消息后的等待时间（默认 0.5 秒）
   - 修改后点击「保存设置」

4. **开始监控**：点击「▶ 开始监控」按钮，状态指示变为绿色表示监控中

5. **停止监控**：点击「⏹ 停止监控」按钮

6. **查看日志**：底部日志区域实时显示运行信息，同时保存在 `logs/monitor.log`

---

## ⚙️ 配置文件说明

配置文件 `config.json` 存储在项目根目录，格式如下：

```json
{
  "rules": [
    {
      "keyword": "你好",
      "reply": "你好！有什么可以帮助你的吗？",
      "enabled": true
    },
    {
      "keyword": "价格",
      "reply": "请稍等，我马上为您查询价格信息。",
      "enabled": true
    },
    {
      "keyword": "在吗",
      "reply": "在的，请问有什么需要？",
      "enabled": true
    }
  ],
  "scan_interval": 3,
  "cooldown": 30,
  "send_delay": 0.5
}
```

| 字段 | 说明 |
|------|------|
| `rules` | 关键字-回复规则列表 |
| `rules[].keyword` | 触发关键字 |
| `rules[].reply` | 自动回复内容 |
| `rules[].enabled` | 是否启用该规则 |
| `scan_interval` | 监控扫描间隔（秒） |
| `cooldown` | 同一关键字冷却时间（秒） |
| `send_delay` | 发送消息后延迟（秒） |

---

## 🛠️ 常见问题

**Q: 提示 "TesseractNotFoundError"**

A: 请按照上方步骤安装 Tesseract OCR，并确保将其路径加入系统 `PATH` 环境变量。

**Q: 中文回复发送后乱码或缺失**

A: 程序使用剪贴板（Ctrl+V）方式发送中文，请确保目标窗口的输入框已获得焦点，且支持粘贴操作。

**Q: 截图区域不正确**

A: 确保目标窗口没有被其他窗口遮挡，程序会自动激活目标窗口后再截图。

**Q: Windows 系统上 `pygetwindow` 无法正常工作**

A: 可尝试以管理员身份运行 `python main.py`。

---

## ⚠️ 免责声明

- 本工具仅供学习和合法的自动化场景使用（例如：自己账号的客服自动应答）
- **严禁**用于未经授权地监控他人通讯或窗口内容，否则可能违反《个人信息保护法》等相关法律法规
- 使用本工具产生的任何后果由使用者自行承担，作者不负任何法律责任
- 请遵守目标应用程序的服务协议和相关法律法规，合法合规使用

---

## 📄 开源协议

MIT License
