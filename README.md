<p align="center">
  <img src="artificial-intelligence.png" width="120" alt="OPEN-AGENT">
</p>

<h1 align="center">OPEN-AGENT</h1>
<p align="center"><strong>可定制桌面 AI 助手 · Customizable Desktop AI Assistant</strong></p>
<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.10+-green.svg" alt="Python"></a>
</p>

---

A desktop AI companion with multi-level memory, 25+ built-in tools, task scheduling, and natural language interaction. Powered by Qwen LLM through OpenAI-compatible API.  
一个带有多级记忆系统、25+ 内置工具、任务调度和自然语言交互的桌面 AI 助手，基于 Qwen 大模型。

---

## ✨ Features · 特性

- **Multi-Level Memory · 多级记忆**  
  Core Memory (personality) + Medium Memory (dynamic) + Deep Memory (ChromaDB vector search)  
  核心记忆（人格设定）+ 中期记忆（动态更新）+ 深度记忆（向量检索）

- **Tool Calling · 工具调用**  
  25+ built-in tools: file ops, system control, web search, paper retrieval, PDF reading, clipboard, app launch, etc.  
  涵盖文件操作、系统控制、网页搜索、论文检索、PDF 阅读、剪贴板、应用启动等

- **Streaming Chat · 流式对话**  
  Real-time streaming with chain-of-thought reasoning support  
  支持思维链推理的实时流式输出

- **Task Scheduler · 定时任务**  
  SQLite + Cron expression driven task engine  
  SQLite + Cron 表达式驱动的任务调度引擎

- **Desktop GUI · 桌面界面**  
  PyQt5 native desktop app with system tray, notifications, drag-and-drop file upload  
  PyQt5 原生桌面应用，支持系统托盘、消息通知、拖拽上传

- **Configurable Personality · 可定制人格**  
  Define AI persona freely via `Memory/core_memory.md`  
  通过核心记忆文件自由定义 AI 角色

- **Security Sandbox · 安全沙箱**  
  File access whitelist/blacklist, extension filter, size limit  
  文件访问白名单/黑名单、后缀过滤、大小限制

---

## 🚀 Quick Start · 快速开始

### Requirements · 环境

- Python 3.10+
- Windows / macOS / Linux
- [Aliyun Bailian API Key](https://dashscope.aliyun.com/) (or any OpenAI-compatible API)

### Install · 安装

```bash
git clone https://github.com/your-username/open-agent.git
cd open-agent
pip install -r requirements.txt
```

### Configure · 配置

Edit `config.json` / 编辑配置文件：

```json
{
  "api": {
    "LLM_API_KEY": "your-api-key-here",
    "LLM_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1"
  }
}
```

Or set environment variable / 或设置环境变量：

```bash
# Windows
set ALI_API_KEY=your-api-key

# Linux / macOS
export ALI_API_KEY=your-api-key
```

Edit `Memory/core_memory.md` to customize AI personality / 编辑核心记忆文件定义 AI 人格。

### Run · 运行

```bash
# Desktop GUI · 桌面模式
python GUI.py

# Terminal · 终端模式
python demo.py
```

---

## 🛠 Built-in Tools · 内置工具

| Category 类别 | Tools 工具 |
|---------------|------------|
| **System 系统** | Get time, system status info 获取时间、系统状态 |
| **Network 网络** | Web search, weather, academic paper search/read 网页搜索、天气、学术论文检索/阅读 |
| **File 文件** | Read files, browse directories, edit files, Word documents 读取文件、浏览目录、编辑文件、Word 文档 |
| **Desktop 桌面** | Screenshot, mouse/keyboard control, clipboard, app launch 截图、键鼠控制、剪贴板管理、应用启动 |
| **Task 任务** | Cron task create/query/cancel, todo management 定时任务创建/查询/取消、待办管理 |
| **Memory 记忆** | Deep memory search via ChromaDB vector retrieval 深度记忆搜索（向量检索） |

> All tools are auto-invoked via OpenAI Function Calling protocol.  
> 所有工具通过 Function Calling 协议自动调用，LLM 自主决定触发时机。

---

## 🏗️ Architecture · 架构

```
┌─────────────────────────────────┐
│       PyQt5 GUI / CLI Demo       │
├─────────────────────────────────┤
│      Assistant Core Engine       │
│  ┌───────────────────────────┐  │
│  │   3-Tier Memory System    │  │
│  │  Core → Medium → Context  │  │
│  │        + ChromaDB         │  │
│  └───────────────────────────┘  │
├─────────────────────────────────┤
│    Reasoning Layer (LLM)        │
│  Qwen / DeepSeek / OpenAI API   │
├─────────────────────────────────┤
│     Tool System (25+ tools)     │
│  FuncCall → name2func dispatch  │
├─────────────────────────────────┤
│     Task Manager (SQLite)       │
│  Cron scheduler + event queue   │
└─────────────────────────────────┘
```

---

## 📁 Structure · 项目结构

```
open-agent/
├── Assistant.py          # Core engine · 核心引擎
├── GUI.py                # Desktop GUI · 桌面界面
├── demo.py               # CLI demo · 命令行演示
├── reasoning.py          # LLM reasoning layer · 推理层
├── memory.py             # ChromaDB memory management · 记忆管理
├── config.py             # Config manager · 配置管理器
├── config.json           # Config file (gitignored) · 配置文件
├── requirements.txt      # Dependencies · 依赖
├── LICENSE               # MIT License
├── utils/
│   ├── tools_init.py     # Tool registry & function mapping
│   ├── utils.py          # Tool implementations
│   ├── LLM_Tools.py      # Function Calling schema definitions
│   ├── task_manager.py   # Cron task scheduler
│   ├── todo.py           # Todo client
│   └── ys_utils.py       # Todo API wrapper
├── Memory/
│   ├── core_memory.md    # Core personality (editable)
│   └── medium_memory.md  # Medium memory (runtime updated)
└── .gitignore
```

---

## 📝 Customize AI Personality · 自定义 AI 人格

Edit `Memory/core_memory.md` / 编辑核心记忆：

```markdown
# 核心记忆

## 角色设定
你是一个专业的编程助手，擅长 Python 和机器学习。

## 性格设定
你严谨但友善，喜欢用代码示例回答问题。

## 互动设定
简洁高效，直接给出可运行的代码。
```

Restart the program to apply changes.  
重启程序即可生效。

---

## 📄 License · 许可证

MIT License — see [LICENSE](LICENSE)

## 🙏 Acknowledgments · 致谢

- [Qwen](https://github.com/QwenLM/Qwen) — LLM · 大语言模型
- [ChromaDB](https://www.trychroma.com/) — Vector database · 向量数据库
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) — GUI framework · 界面框架
